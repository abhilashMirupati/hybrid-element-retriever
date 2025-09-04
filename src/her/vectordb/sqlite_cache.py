# src/her/vectordb/sqlite_cache.py
from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

_SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA temp_store=MEMORY;
PRAGMA mmap_size=134217728; -- 128MB
PRAGMA page_size=4096;

CREATE TABLE IF NOT EXISTS kv (
    k TEXT PRIMARY KEY,
    v TEXT NOT NULL,
    ts INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS embeddings (
    hash TEXT PRIMARY KEY,
    vector TEXT NOT NULL,        -- JSON-encoded list[float]
    dim INTEGER NOT NULL,
    model_name TEXT NOT NULL,
    hits INTEGER NOT NULL DEFAULT 0,
    ts INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS promotions (
    page_sig TEXT NOT NULL,
    frame_hash TEXT NOT NULL,
    label_key TEXT NOT NULL,
    selector TEXT NOT NULL,
    success_count INTEGER NOT NULL DEFAULT 0,
    failure_count INTEGER NOT NULL DEFAULT 0,
    updated_at INTEGER NOT NULL,
    PRIMARY KEY (page_sig, frame_hash, label_key, selector)
);
"""

_CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_embeddings_model ON embeddings(model_name);",
    "CREATE INDEX IF NOT EXISTS idx_embeddings_ts ON embeddings(ts);",
    "CREATE INDEX IF NOT EXISTS idx_promotions_label ON promotions(page_sig, frame_hash, label_key);",
]


class SQLiteKV:
    """
    Production-ready SQLite-backed KV + Embedding store (thread-safe).

    - Embeddings are stored as JSON-encoded float lists.
    - Provides batch get/put for embeddings (used by pipeline delta flow).
    - Includes a general kv table (for misc metadata).
    - Promotions table is created here (used in Step 6).

    The DB is small and local; WAL mode makes concurrent reads cheap.
    """

    def __init__(self, db_path: str, max_size_mb: int = 400) -> None:
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._max_size_bytes = max(32, max_size_mb) * 1024 * 1024
        self._init()

    # ----------------------- internal helpers -----------------------

    def _connect(self) -> sqlite3.Connection:
        # isolation_level=None enables autocommit; we manage transactions explicitly
        con = sqlite3.connect(self.db_path, timeout=30.0, isolation_level=None)
        con.execute("PRAGMA foreign_keys=ON;")
        return con

    def _init(self) -> None:
        with self._lock, self._connect() as con:
            con.executescript(_SCHEMA)
            for stmt in _CREATE_INDEXES:
                con.execute(stmt)

    def _now(self) -> int:
        return int(time.time())

    def _db_size_ok(self) -> bool:
        try:
            return os.path.getsize(self.db_path) <= self._max_size_bytes
        except FileNotFoundError:
            return True

    def vacuum_if_needed(self) -> None:
        # Lightweight guard; only VACUUM if DB file exceeds soft limit
        if not self._db_size_ok():
            with self._lock, self._connect() as con:
                con.execute("VACUUM;")

    # -------------------------- KV API ------------------------------

    def put(self, key: str, value: Any) -> None:
        payload = json.dumps(value, ensure_ascii=False)
        ts = self._now()
        with self._lock, self._connect() as con:
            con.execute(
                "INSERT INTO kv(k, v, ts) VALUES(?, ?, ?) "
                "ON CONFLICT(k) DO UPDATE SET v=excluded.v, ts=excluded.ts",
                (key, payload, ts),
            )

    def get(self, key: str) -> Optional[Any]:
        with self._lock, self._connect() as con:
            cur = con.execute("SELECT v FROM kv WHERE k=?", (key,))
            row = cur.fetchone()
        if not row:
            return None
        try:
            return json.loads(row[0])
        except Exception:
            return None

    # ----------------------- Embeddings API -------------------------

    def put_embedding(self, h: str, vector: List[float], model_name: str, dim: Optional[int] = None) -> None:
        if dim is None:
            dim = len(vector)
        payload = json.dumps(vector, ensure_ascii=False)
        ts = self._now()
        with self._lock, self._connect() as con:
            con.execute(
                "INSERT INTO embeddings(hash, vector, dim, model_name, hits, ts) "
                "VALUES(?, ?, ?, ?, 0, ?) "
                "ON CONFLICT(hash) DO UPDATE SET vector=excluded.vector, dim=excluded.dim, "
                "model_name=excluded.model_name, ts=excluded.ts",
                (h, payload, dim, model_name, ts),
            )

    def batch_put_embeddings(self, mapping: Dict[str, List[float]], model_name: str, dim: Optional[int] = None) -> None:
        ts = self._now()
        rows: List[Tuple[str, str, int, str, int]] = []
        for h, vec in mapping.items():
            d = dim if dim is not None else len(vec)
            rows.append((h, json.dumps(vec, ensure_ascii=False), d, model_name, ts))
        if not rows:
            return
        with self._lock, self._connect() as con:
            con.executemany(
                "INSERT INTO embeddings(hash, vector, dim, model_name, hits, ts) "
                "VALUES(?, ?, ?, ?, 0, ?) "
                "ON CONFLICT(hash) DO UPDATE SET vector=excluded.vector, dim=excluded.dim, "
                "model_name=excluded.model_name, ts=excluded.ts",
                rows,
            )

    def get_embedding(self, h: str) -> Optional[List[float]]:
        with self._lock, self._connect() as con:
            cur = con.execute("SELECT vector, dim FROM embeddings WHERE hash=?", (h,))
            row = cur.fetchone()
            if not row:
                return None
            # Increment hits non-critically
            try:
                con.execute("UPDATE embeddings SET hits = hits + 1 WHERE hash=?", (h,))
            except Exception:
                pass
        try:
            vec = json.loads(row[0])
            if not isinstance(vec, list):
                return None
            return vec
        except Exception:
            return None

    def batch_get_embeddings(self, hashes: Iterable[str]) -> Dict[str, List[float]]:
        # Return only found rows; missing keys are omitted.
        out: Dict[str, List[float]] = {}
        hashes = list(dict.fromkeys(hashes))  # de-dup, preserve order
        if not hashes:
            return out

        qmarks = ",".join(["?"] * len(hashes))
        with self._lock, self._connect() as con:
            cur = con.execute(
                f"SELECT hash, vector FROM embeddings WHERE hash IN ({qmarks})",
                tuple(hashes),
            )
            rows = cur.fetchall()
            # Increment hits in bulk (non-fatal)
            try:
                con.executemany("UPDATE embeddings SET hits = hits + 1 WHERE hash=?", [(r[0],) for r in rows])
            except Exception:
                pass

        for h, vec_json in rows:
            try:
                vec = json.loads(vec_json)
                if isinstance(vec, list):
                    out[h] = vec
            except Exception:
                continue
        return out

    # ---------------------- Promotions (Step 6) ---------------------

    def record_promotion(
        self,
        page_sig: str,
        frame_hash: str,
        label_key: str,
        selector: str,
        success: bool,
    ) -> None:
        """Record success/failure for a selector promotion."""
        ts = self._now()
        with self._lock, self._connect() as con:
            # Upsert row and bump counters
            cur = con.execute(
                "SELECT success_count, failure_count FROM promotions "
                "WHERE page_sig=? AND frame_hash=? AND label_key=? AND selector=?",
                (page_sig, frame_hash, label_key, selector),
            )
            row = cur.fetchone()
            if row:
                sc, fc = row
                if success:
                    sc += 1
                else:
                    fc += 1
                con.execute(
                    "UPDATE promotions SET success_count=?, failure_count=?, updated_at=? "
                    "WHERE page_sig=? AND frame_hash=? AND label_key=? AND selector=?",
                    (sc, fc, ts, page_sig, frame_hash, label_key, selector),
                )
            else:
                sc = 1 if success else 0
                fc = 0 if success else 1
                con.execute(
                    "INSERT INTO promotions(page_sig, frame_hash, label_key, selector, success_count, failure_count, updated_at) "
                    "VALUES(?, ?, ?, ?, ?, ?, ?)",
                    (page_sig, frame_hash, label_key, selector, sc, fc, ts),
                )

    def get_promotion(self, page_sig: str, frame_hash: str, label_key: str) -> Optional[str]:
        """Return the most successful selector for this label, if any."""
        with self._lock, self._connect() as con:
            cur = con.execute(
                "SELECT selector, success_count, failure_count, updated_at FROM promotions "
                "WHERE page_sig=? AND frame_hash=? AND label_key=? "
                "ORDER BY success_count DESC, failure_count ASC, updated_at DESC LIMIT 1",
                (page_sig, frame_hash, label_key),
            )
            row = cur.fetchone()
            if not row:
                return None
            selector = row[0]
            return selector
