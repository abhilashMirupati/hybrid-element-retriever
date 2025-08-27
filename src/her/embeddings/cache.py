"""Two-tier embedding cache: in-memory LRU + sqlite on-disk store."""

from __future__ import annotations
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any
import sqlite3
import io
import logging
import numpy as np

logger = logging.getLogger(__name__)

DEFAULT_DB = Path.home() / ".cache" / "her" / "embeddings.db"


def _ensure_db(path: Path) -> None:
    """Ensure database and table exist."""
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(path))
    try:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS emb (
                k TEXT PRIMARY KEY,
                v BLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )
        con.commit()
    finally:
        con.close()


@dataclass
class EmbeddingCache:
    """LRU memory cache with sqlite persistence."""

    capacity: int = 1024
    db_path: Path = DEFAULT_DB

    def __post_init__(self) -> None:
        self._mem: OrderedDict[str, np.ndarray] = OrderedDict()
        _ensure_db(self.db_path)
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[np.ndarray]:
        """Get embedding from cache, checking memory first then disk."""
        # Check memory
        if key in self._mem:
            # Move to end (most recently used)
            v = self._mem.pop(key)
            self._mem[key] = v
            self._hits += 1
            logger.debug(f"Cache hit (memory) for key: {key[:50]}...")
            return v

        # Check disk
        con = sqlite3.connect(str(self.db_path))
        try:
            cur = con.execute("SELECT v FROM emb WHERE k=?", (key,))
            row = cur.fetchone()
            if not row:
                self._misses += 1
                return None

            # Deserialize numpy array
            buf = io.BytesIO(row[0])
            arr = np.load(buf, allow_pickle=False)

            # Promote to memory
            self._promote(key, arr)
            self._hits += 1
            logger.debug(f"Cache hit (disk) for key: {key[:50]}...")
            return arr
        except Exception as e:
            logger.warning(f"Failed to load from cache: {e}")
            self._misses += 1
            return None
        finally:
            con.close()

    def put(self, key: str, value: np.ndarray) -> None:
        """Store embedding in both memory and disk cache."""
        # Add to memory
        self._promote(key, value)

        # Persist to disk
        con = sqlite3.connect(str(self.db_path))
        try:
            # Serialize numpy array
            buf = io.BytesIO()
            np.save(buf, value, allow_pickle=False)
            blob = sqlite3.Binary(buf.getvalue())

            con.execute("REPLACE INTO emb(k, v) VALUES (?, ?)", (key, blob))
            con.commit()
            logger.debug(f"Cached embedding for key: {key[:50]}...")
        except Exception as e:
            logger.warning(f"Failed to persist to cache: {e}")
        finally:
            con.close()

    def clear(self) -> None:
        """Clear all cached embeddings."""
        self._mem.clear()
        con = sqlite3.connect(str(self.db_path))
        try:
            con.execute("DELETE FROM emb")
            con.commit()
            logger.info("Cleared embedding cache")
        finally:
            con.close()
        self._hits = 0
        self._misses = 0

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0.0

        con = sqlite3.connect(str(self.db_path))
        try:
            cur = con.execute("SELECT COUNT(*) FROM emb")
            disk_count = cur.fetchone()[0]
        finally:
            con.close()

        return {
            "memory_size": len(self._mem),
            "memory_capacity": self.capacity,
            "disk_count": disk_count,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
        }

    def _promote(self, key: str, value: np.ndarray) -> None:
        """Promote entry to memory cache with LRU eviction."""
        if key in self._mem:
            # Remove and re-add to move to end
            self._mem.pop(key)

        self._mem[key] = value

        # Evict oldest if over capacity
        while len(self._mem) > self.capacity:
            evicted = self._mem.popitem(last=False)
            logger.debug(f"Evicted from memory: {evicted[0][:50]}...")
