# PLACE: src/her/embeddings/cache.py
"""Two-tier embedding cache: in-memory LRU + sqlite on-disk store."""
from __future__ import annotations
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import sqlite3, io, os
import numpy as np

DEFAULT_DB = Path(".cache/her/embeddings.db")

def _ensure_db(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(path))
    try:
        con.execute("CREATE TABLE IF NOT EXISTS emb (k TEXT PRIMARY KEY, v BLOB)")
        con.commit()
    finally:
        con.close()

@dataclass
class EmbeddingCache:
    capacity: int = 1024
    db_path: Path = DEFAULT_DB

    def __post_init__(self) -> None:
        self._mem: "OrderedDict[str, np.ndarray]" = OrderedDict()
        _ensure_db(self.db_path)

    def get(self, key: str) -> Optional[np.ndarray]:
        if key in self._mem:
            v = self._mem.pop(key)
            self._mem[key] = v
            return v
        # disk
        con = sqlite3.connect(str(self.db_path))
        try:
            cur = con.execute("SELECT v FROM emb WHERE k=?", (key,))
            row = cur.fetchone()
            if not row:
                return None
            buf = io.BytesIO(row[0])
            arr = np.load(buf, allow_pickle=False)
            # promote to memory
            self._promote(key, arr)
            return arr
        finally:
            con.close()

    def put(self, key: str, value: np.ndarray) -> None:
        self._promote(key, value)
        con = sqlite3.connect(str(self.db_path))
        try:
            buf = io.BytesIO()
            np.save(buf, value, allow_pickle=False)
            con.execute("REPLACE INTO emb(k, v) VALUES (?, ?)", (key, sqlite3.Binary(buf.getvalue())))
            con.commit()
        finally:
            con.close()

    def clear(self) -> None:
        self._mem.clear()
        con = sqlite3.connect(str(self.db_path))
        try:
            con.execute("DELETE FROM emb")
            con.commit()
        finally:
            con.close()

    def _promote(self, key: str, value: np.ndarray) -> None:
        if key in self._mem:
            self._mem.pop(key)
        self._mem[key] = value
        while len(self._mem) > self.capacity:
            self._mem.popitem(last=False)
