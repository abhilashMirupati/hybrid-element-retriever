from __future__ import annotations

import json
import os
import sqlite3
import struct
import time
from collections import OrderedDict
from pathlib import Path
from threading import Lock
from typing import Any, Dict, Iterable, List, MutableMapping, Optional, Tuple

import numpy as np


class _LRU(MutableMapping[str, np.ndarray]):
    def __init__(self, capacity: int) -> None:
        self.capacity = int(max(1, capacity))
        self._data: OrderedDict[str, np.ndarray] = OrderedDict()
        self._lock = Lock()

    def __getitem__(self, key: str) -> np.ndarray:
        with self._lock:
            value = self._data.pop(key)
            self._data[key] = value
            return value

    def __setitem__(self, key: str, value: np.ndarray) -> None:
        with self._lock:
            if key in self._data:
                self._data.pop(key)
            self._data[key] = value
            while len(self._data) > self.capacity:
                self._data.popitem(last=False)

    def __delitem__(self, key: str) -> None:
        with self._lock:
            del self._data[key]

    def __iter__(self) -> Iterable[str]:  # pragma: no cover - trivial
        with self._lock:
            return iter(list(self._data.keys()))

    def __len__(self) -> int:  # pragma: no cover - trivial
        with self._lock:
            return len(self._data)

    def get_direct(self, key: str) -> Optional[np.ndarray]:
        with self._lock:
            if key in self._data:
                return self._data[key]
            return None


def _ensure_db(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS embeddings (
                key TEXT PRIMARY KEY,
                vec BLOB,
                dim INT,
                meta TEXT,
                ts INT
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_ts ON embeddings(ts)")
        conn.commit()


def _to_blob(vec: np.ndarray) -> bytes:
    arr = np.asarray(vec, dtype=np.float32)
    return arr.astype('<f4', copy=False).tobytes(order='C')


def _from_blob(blob: bytes, dim: int) -> np.ndarray:
    arr = np.frombuffer(blob, dtype='<f4')
    if dim and arr.size != dim:
        # Defensive: resize deterministically if metadata is wrong
        arr = np.resize(arr, dim)
    return arr.astype(np.float32, copy=False)


class TwoTierCache:
    """Two-tier embedding cache: in-memory LRU plus on-disk SQLite.

    SQLite schema: (key TEXT PRIMARY KEY, vec BLOB, dim INT, meta JSON, ts INT)
    """

    def __init__(self, cache_dir: os.PathLike[str] | str, max_memory_items: int = 4096) -> None:
        self.cache_root = Path(cache_dir).expanduser().resolve()
        self.cache_root.mkdir(parents=True, exist_ok=True)
        self.db_path = (self.cache_root / 'embeddings' / 'embeds.db').resolve()
        _ensure_db(self.db_path)
        self.mem = _LRU(max_memory_items)
        self._lock = Lock()
        self._hits = 0
        self._misses = 0

    # Public API
    def get(self, key: str) -> Optional[np.ndarray]:
        v = self.mem.get_direct(key)
        if v is not None:
            self._hits += 1
            # Promote in LRU by setting again
            self.mem[key] = v
            return v
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute("SELECT vec, dim FROM embeddings WHERE key=?", (key,))
            row = cur.fetchone()
            if row is None:
                self._misses += 1
                return None
            blob, dim = row
            arr = _from_blob(blob, int(dim))
            self.mem[key] = arr
            self._hits += 1
            return arr

    def get_raw(self, key: str) -> Optional[np.ndarray]:
        """Bypass any overrides: read memory then disk directly."""
        v = self.mem.get_direct(key)
        if v is not None:
            return v
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute("SELECT vec, dim FROM embeddings WHERE key=?", (key,))
            row = cur.fetchone()
            if row is None:
                return None
            blob, dim = row
            return _from_blob(blob, int(dim))

    def put(self, key: str, vec: np.ndarray, meta: Optional[Dict[str, Any]] = None) -> None:
        arr = np.asarray(vec, dtype=np.float32)
        meta_json = json.dumps(meta or {}, ensure_ascii=False)
        blob = _to_blob(arr)
        ts = int(time.time())
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO embeddings(key, vec, dim, meta, ts) VALUES (?, ?, ?, ?, ?)",
                (key, blob, int(arr.size), meta_json, ts),
            )
            conn.commit()
        self.mem[key] = arr

    def batch_get(self, keys: List[str]) -> Dict[str, np.ndarray]:
        out: Dict[str, np.ndarray] = {}
        remaining: List[str] = []
        for k in keys:
            v = self.mem.get_direct(k)
            if v is not None:
                out[k] = v
            else:
                remaining.append(k)
        if not remaining:
            self._hits += len(out)
            return out
        with sqlite3.connect(self.db_path) as conn:
            if remaining:
                placeholders = ','.join('?' * len(remaining))
                cur = conn.execute(
                    f"SELECT key, vec, dim FROM embeddings WHERE key IN ({placeholders})",
                    remaining,
                )
                for k, blob, dim in cur.fetchall():
                    arr = _from_blob(blob, int(dim))
                    self.mem[k] = arr
                    out[k] = arr
        self._hits += len(out)
        self._misses += max(0, len(keys) - len(out))
        return out

    def batch_put(self, items: List[Tuple[str, np.ndarray, Optional[Dict[str, Any]]]]) -> None:
        if not items:
            return
        ts = int(time.time())
        with sqlite3.connect(self.db_path) as conn:
            rows: List[Tuple[str, bytes, int, str, int]] = []
            for key, vec, meta in items:
                arr = np.asarray(vec, dtype=np.float32)
                rows.append((key, _to_blob(arr), int(arr.size), json.dumps(meta or {}), ts))
                self.mem[key] = arr
            conn.executemany(
                "INSERT OR REPLACE INTO embeddings(key, vec, dim, meta, ts) VALUES (?, ?, ?, ?, ?)",
                rows,
            )
            conn.commit()

    def stats(self) -> Dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            c = conn.execute("SELECT COUNT(*) FROM embeddings").fetchone()
            disk_items = int(c[0]) if c else 0
        return {
            'hits': int(self._hits),
            'misses': int(self._misses),
            'mem_items': int(len(self.mem)),
            'disk_items': disk_items,
            'db_path': str(self.db_path),
        }


__all__ = ["TwoTierCache"]

