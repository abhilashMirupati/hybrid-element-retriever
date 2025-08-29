"""Two-tier cache system with LRU in-memory and SQLite persistence."""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from collections import OrderedDict
from pathlib import Path
import sqlite3
import json
import time
import hashlib
import logging
from threading import Lock
import pickle

from ..config import get_cache_dir, MEMORY_CACHE_SIZE, DISK_CACHE_SIZE_MB

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Single cache entry with metadata."""

    key: str
    value: Any
    timestamp: float = field(default_factory=time.time)
    hits: int = 0
    size_bytes: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "key": self.key,
            "value": self.value,
            "timestamp": self.timestamp,
            "hits": self.hits,
            "size_bytes": self.size_bytes,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CacheEntry":
        """Create from dictionary."""
        return cls(**data)


class LRUCache:
    """Thread-safe LRU cache implementation."""

    def __init__(self, max_size: int = MEMORY_CACHE_SIZE):
        """Initialize LRU cache.

        Args:
            max_size: Maximum number of entries
        """
        self.max_size = max_size
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.lock = Lock()
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        with self.lock:
            if key in self.cache:
                # Move to end (most recently used)
                entry = self.cache.pop(key)
                entry.hits += 1
                self.cache[key] = entry
                self.hits += 1
                return entry.value
            else:
                self.misses += 1
                return None

    def put(
        self, key: str, value: Any, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Put value in cache.

        Args:
            key: Cache key
            value: Value to cache
            metadata: Optional metadata
        """
        with self.lock:
            # Remove if exists
            if key in self.cache:
                self.cache.pop(key)

            # Add to end
            entry = CacheEntry(
                key=key,
                value=value,
                metadata=metadata or {},
                size_bytes=len(pickle.dumps(value)),
            )
            self.cache[key] = entry

            # Evict oldest if over capacity
            while len(self.cache) > self.max_size:
                self.cache.popitem(last=False)

    def clear(self) -> None:
        """Clear all entries."""
        with self.lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self.lock:
            total_size = sum(e.size_bytes for e in self.cache.values())
            return {
                "entries": len(self.cache),
                "max_size": self.max_size,
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": (
                    self.hits / (self.hits + self.misses)
                    if (self.hits + self.misses) > 0
                    else 0
                ),
                "total_size_bytes": total_size,
            }


class SQLiteCache:
    """SQLite-based persistent cache."""

    def __init__(
        self, db_path: Optional[Path] = None, max_size_mb: int = DISK_CACHE_SIZE_MB
    ):
        """Initialize SQLite cache.

        Args:
            db_path: Path to database file
            max_size_mb: Maximum cache size in MB
        """
        self.db_path = db_path or (get_cache_dir() / "embeddings.db")
        self.max_size_mb = max_size_mb
        self.lock = Lock()
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value BLOB NOT NULL,
                    timestamp REAL NOT NULL,
                    hits INTEGER DEFAULT 0,
                    size_bytes INTEGER NOT NULL,
                    metadata TEXT
                )
            """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON cache(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_hits ON cache(hits)")
            conn.commit()

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        with self.lock:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.execute(
                    "SELECT value, hits FROM cache WHERE key = ?", (key,)
                )
                row = cursor.fetchone()

                if row:
                    value_blob, hits = row
                    # Update hits
                    conn.execute(
                        "UPDATE cache SET hits = ? WHERE key = ?", (hits + 1, key)
                    )
                    conn.commit()

                    try:
                        return pickle.loads(value_blob)
                    except Exception as e:
                        logger.error(f"Failed to deserialize cache value: {e}")
                        return None

                return None

    def put(
        self, key: str, value: Any, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Put value in cache.

        Args:
            key: Cache key
            value: Value to cache
            metadata: Optional metadata
        """
        with self.lock:
            try:
                value_blob = pickle.dumps(value)
                size_bytes = len(value_blob)

                with sqlite3.connect(str(self.db_path)) as conn:
                    # Check current cache size
                    cursor = conn.execute("SELECT SUM(size_bytes) FROM cache")
                    current_size = cursor.fetchone()[0] or 0

                    # Evict old entries if needed
                    max_bytes = self.max_size_mb * 1024 * 1024
                    if current_size + size_bytes > max_bytes:
                        self._evict_lru(conn, size_bytes)

                    # Insert or replace
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO cache (key, value, timestamp, hits, size_bytes, metadata)
                        VALUES (?, ?, ?, 0, ?, ?)
                    """,
                        (
                            key,
                            value_blob,
                            time.time(),
                            size_bytes,
                            json.dumps(metadata or {}),
                        ),
                    )
                    conn.commit()

            except Exception as e:
                logger.error(f"Failed to cache value: {e}")

    def _evict_lru(self, conn: sqlite3.Connection, needed_bytes: int) -> None:
        """Evict least recently used entries.

        Args:
            conn: Database connection
            needed_bytes: Bytes needed
        """
        # Get entries sorted by hits and timestamp
        cursor = conn.execute(
            """
            SELECT key, size_bytes
            FROM cache
            ORDER BY hits ASC, timestamp ASC
        """
        )

        evicted_bytes = 0
        keys_to_evict = []

        for key, size_bytes in cursor:
            keys_to_evict.append(key)
            evicted_bytes += size_bytes
            if evicted_bytes >= needed_bytes:
                break

        # Evict entries
        if keys_to_evict:
            placeholders = ",".join("?" * len(keys_to_evict))
            conn.execute(
                f"DELETE FROM cache WHERE key IN ({placeholders})", keys_to_evict
            )

    def clear(self) -> None:
        """Clear all entries."""
        with self.lock:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute("DELETE FROM cache")
                conn.commit()

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self.lock:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.execute(
                    """
                    SELECT
                        COUNT(*) as entries,
                        SUM(size_bytes) as total_size,
                        SUM(hits) as total_hits,
                        AVG(hits) as avg_hits
                    FROM cache
                """
                )
                row = cursor.fetchone()

                return {
                    "entries": row[0] or 0,
                    "total_size_bytes": row[1] or 0,
                    "total_size_mb": (row[1] or 0) / (1024 * 1024),
                    "max_size_mb": self.max_size_mb,
                    "total_hits": row[2] or 0,
                    "avg_hits": row[3] or 0,
                }


class TwoTierCache:
    """Two-tier cache with LRU memory and SQLite disk caching."""

    def __init__(
        self,
        memory_size: int = MEMORY_CACHE_SIZE,
        disk_size_mb: int = DISK_CACHE_SIZE_MB,
        db_path: Optional[Path] = None,
        *,
        cache_dir: Optional[Path] = None,
        max_memory_items: Optional[int] = None,
    ):
        """Initialize two-tier cache.

        Args:
            memory_size: Maximum memory cache entries
            disk_size_mb: Maximum disk cache size in MB
            db_path: Optional database path
            cache_dir: Optional directory to place the SQLite db (embeddings.db)
            max_memory_items: Override for memory LRU capacity
        """
        # Resolve effective paths and capacities
        effective_db_path = (
            (Path(cache_dir) / "embeddings.db") if cache_dir is not None else (db_path or (get_cache_dir() / "embeddings.db"))
        )
        effective_memory = max_memory_items if max_memory_items is not None else memory_size

        self.memory_cache = LRUCache(max_size=effective_memory)
        self.disk_cache = SQLiteCache(db_path=effective_db_path, max_size_mb=disk_size_mb)
        # Register as global so other components reuse this instance (test compatibility)
        try:
            global _global_cache
            _global_cache = self
        except Exception:
            pass

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache (memory first, then disk).

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        # Try memory cache first
        value = self.memory_cache.get(key)
        if value is not None:
            return value

        # Try disk cache
        value = self.disk_cache.get(key)
        if value is not None:
            # Promote to memory cache
            self.memory_cache.put(key, value)
            return value

        return None

    def set(self, key: str, value: Any, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Store value in cache (alias for put)."""
        self.put(key, value, metadata)
    
    def put(
        self, key: str, value: Any, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Put value in both cache tiers.

        Args:
            key: Cache key
            value: Value to cache
            metadata: Optional metadata
        """
        # Put in memory cache
        self.memory_cache.put(key, value, metadata)

        # Put in disk cache
        self.disk_cache.put(key, value, metadata)

    def get_batch(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values from cache.

        Args:
            keys: List of cache keys

        Returns:
            Dictionary of key-value pairs
        """
        results = {}

        for key in keys:
            value = self.get(key)
            if value is not None:
                results[key] = value

        return results

    def put_batch(
        self, items: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Put multiple values in cache.

        Args:
            items: Dictionary of key-value pairs
            metadata: Optional metadata for all items
        """
        for key, value in items.items():
            self.put(key, value, metadata)

    def clear(self) -> None:
        """Clear both cache tiers."""
        self.memory_cache.clear()
        self.disk_cache.clear()

    def stats(self) -> Dict[str, Any]:
        """Get combined cache statistics."""
        return {"memory": self.memory_cache.stats(), "disk": self.disk_cache.stats()}

    def size(self) -> int:
        """Total number of entries across memory and disk (approx)."""
        try:
            return int(self.memory_cache.stats().get("entries", 0))
        except Exception:
            return 0

    def compute_key(self, *args, **kwargs) -> str:
        """Compute cache key from arguments.

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Cache key
        """
        # Create stable hash from arguments
        key_data = {"args": args, "kwargs": kwargs}
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()


# Global cache instance
_global_cache: Optional[TwoTierCache] = None


def get_global_cache() -> TwoTierCache:
    """Get or create global cache instance."""
    global _global_cache
    if _global_cache is None:
        _global_cache = TwoTierCache()
    return _global_cache


def cache_embeddings(func):
    """Decorator to cache embedding function results.

    Usage:
        @cache_embeddings
        def compute_embeddings(text):
            # Expensive computation
            return embeddings
    """

    def wrapper(*args, **kwargs):
        cache = get_global_cache()
        key = cache.compute_key(func.__name__, *args, **kwargs)

        # Try cache
        result = cache.get(key)
        if result is not None:
            logger.debug(f"Cache hit for {func.__name__}")
            return result

        # Compute and cache
        logger.debug(f"Cache miss for {func.__name__}")
        result = func(*args, **kwargs)
        cache.put(key, result)

        return result

    return wrapper
