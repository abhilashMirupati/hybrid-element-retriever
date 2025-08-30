"""SQLite-based vector cache with LRU eviction."""

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import numpy as np
import aiosqlite
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class CachedVector:
    """Cached vector entry."""
    key: str
    vector: np.ndarray
    metadata: Dict[str, Any]
    timestamp: float
    access_count: int
    

class VectorCache:
    """SQLite-based vector cache with LRU eviction.
    
    Stores embeddings in .cache/embeddings/ directory.
    """
    
    def __init__(self, cache_dir: Optional[Path] = None, max_size: int = 100000):
        self.cache_dir = cache_dir or Path(".cache/embeddings")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.cache_dir / "vectors.db"
        self.max_size = max_size
        self._db: Optional[aiosqlite.Connection] = None
        self._memory_cache: Dict[str, CachedVector] = {}  # LRU memory cache
        self._memory_cache_size = 1000  # Max items in memory
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "total_gets": 0,
            "total_puts": 0
        }
        
    async def initialize(self) -> None:
        """Initialize database connection and tables."""
        self._db = await aiosqlite.connect(self.db_path)
        self._db.row_factory = aiosqlite.Row
        
        # Create tables
        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS vectors (
                key TEXT PRIMARY KEY,
                vector BLOB NOT NULL,
                metadata TEXT,
                dimension INTEGER NOT NULL,
                timestamp REAL NOT NULL,
                access_count INTEGER DEFAULT 1,
                last_access REAL NOT NULL
            )
        """)
        
        await self._db.execute("""
            CREATE INDEX IF NOT EXISTS idx_last_access 
            ON vectors(last_access)
        """)
        
        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS cache_stats (
                id INTEGER PRIMARY KEY,
                total_items INTEGER DEFAULT 0,
                total_hits INTEGER DEFAULT 0,
                total_misses INTEGER DEFAULT 0,
                total_evictions INTEGER DEFAULT 0,
                last_cleanup REAL
            )
        """)
        
        await self._db.commit()
        
        # Load stats
        await self._load_stats()
        
        logger.info(f"Vector cache initialized at {self.db_path}")
        
    async def _load_stats(self) -> None:
        """Load statistics from database."""
        cursor = await self._db.execute("SELECT * FROM cache_stats WHERE id = 1")
        row = await cursor.fetchone()
        if row:
            self._stats["hits"] = row["total_hits"]
            self._stats["misses"] = row["total_misses"]
            self._stats["evictions"] = row["total_evictions"]
        else:
            await self._db.execute(
                "INSERT INTO cache_stats (id, last_cleanup) VALUES (1, ?)",
                (time.time(),)
            )
            await self._db.commit()
            
    async def get(self, key: str) -> Optional[CachedVector]:
        """Get vector from cache.
        
        Args:
            key: Cache key
            
        Returns:
            CachedVector if found, None otherwise
        """
        self._stats["total_gets"] += 1
        
        # Check memory cache first
        if key in self._memory_cache:
            self._stats["hits"] += 1
            entry = self._memory_cache[key]
            entry.access_count += 1
            return entry
            
        # Check database
        cursor = await self._db.execute(
            "SELECT * FROM vectors WHERE key = ?",
            (key,)
        )
        row = await cursor.fetchone()
        
        if row:
            self._stats["hits"] += 1
            
            # Deserialize vector
            vector = np.frombuffer(row["vector"], dtype=np.float32)
            metadata = json.loads(row["metadata"]) if row["metadata"] else {}
            
            # Update access stats
            await self._db.execute(
                "UPDATE vectors SET access_count = access_count + 1, last_access = ? WHERE key = ?",
                (time.time(), key)
            )
            await self._db.commit()
            
            # Create entry
            entry = CachedVector(
                key=key,
                vector=vector,
                metadata=metadata,
                timestamp=row["timestamp"],
                access_count=row["access_count"] + 1
            )
            
            # Add to memory cache
            self._add_to_memory_cache(key, entry)
            
            return entry
        else:
            self._stats["misses"] += 1
            return None
            
    async def put(self, key: str, vector: np.ndarray, metadata: Optional[Dict] = None) -> None:
        """Put vector in cache.
        
        Args:
            key: Cache key
            vector: Vector to cache
            metadata: Optional metadata
        """
        self._stats["total_puts"] += 1
        
        # Serialize vector
        vector_bytes = vector.astype(np.float32).tobytes()
        metadata_json = json.dumps(metadata) if metadata else None
        timestamp = time.time()
        
        # Insert or replace in database
        await self._db.execute(
            """
            INSERT OR REPLACE INTO vectors 
            (key, vector, metadata, dimension, timestamp, access_count, last_access)
            VALUES (?, ?, ?, ?, ?, 
                    COALESCE((SELECT access_count FROM vectors WHERE key = ?), 0) + 1,
                    ?)
            """,
            (key, vector_bytes, metadata_json, len(vector), timestamp, key, timestamp)
        )
        await self._db.commit()
        
        # Add to memory cache
        entry = CachedVector(
            key=key,
            vector=vector,
            metadata=metadata or {},
            timestamp=timestamp,
            access_count=1
        )
        self._add_to_memory_cache(key, entry)
        
        # Check if cleanup needed
        await self._maybe_cleanup()
        
    async def batch_get(self, keys: List[str]) -> Dict[str, Optional[CachedVector]]:
        """Get multiple vectors from cache.
        
        Args:
            keys: List of cache keys
            
        Returns:
            Dictionary mapping keys to CachedVector or None
        """
        results = {}
        db_keys = []
        
        # Check memory cache first
        for key in keys:
            if key in self._memory_cache:
                results[key] = self._memory_cache[key]
                self._stats["hits"] += 1
            else:
                db_keys.append(key)
                
        # Batch fetch from database
        if db_keys:
            placeholders = ",".join("?" * len(db_keys))
            cursor = await self._db.execute(
                f"SELECT * FROM vectors WHERE key IN ({placeholders})",
                db_keys
            )
            rows = await cursor.fetchall()
            
            found_keys = set()
            for row in rows:
                key = row["key"]
                found_keys.add(key)
                
                # Deserialize
                vector = np.frombuffer(row["vector"], dtype=np.float32)
                metadata = json.loads(row["metadata"]) if row["metadata"] else {}
                
                entry = CachedVector(
                    key=key,
                    vector=vector,
                    metadata=metadata,
                    timestamp=row["timestamp"],
                    access_count=row["access_count"]
                )
                
                results[key] = entry
                self._add_to_memory_cache(key, entry)
                self._stats["hits"] += 1
                
            # Mark misses
            for key in db_keys:
                if key not in found_keys:
                    results[key] = None
                    self._stats["misses"] += 1
                    
            # Update access times
            if found_keys:
                placeholders = ",".join("?" * len(found_keys))
                await self._db.execute(
                    f"UPDATE vectors SET access_count = access_count + 1, last_access = ? WHERE key IN ({placeholders})",
                    [time.time()] + list(found_keys)
                )
                await self._db.commit()
                
        self._stats["total_gets"] += len(keys)
        return results
        
    async def batch_put(self, entries: Dict[str, Tuple[np.ndarray, Optional[Dict]]]) -> None:
        """Put multiple vectors in cache.
        
        Args:
            entries: Dictionary mapping keys to (vector, metadata) tuples
        """
        timestamp = time.time()
        
        # Prepare batch insert
        values = []
        for key, (vector, metadata) in entries.items():
            vector_bytes = vector.astype(np.float32).tobytes()
            metadata_json = json.dumps(metadata) if metadata else None
            values.append((key, vector_bytes, metadata_json, len(vector), timestamp, key, timestamp))
            
            # Add to memory cache
            entry = CachedVector(
                key=key,
                vector=vector,
                metadata=metadata or {},
                timestamp=timestamp,
                access_count=1
            )
            self._add_to_memory_cache(key, entry)
            
        # Batch insert
        await self._db.executemany(
            """
            INSERT OR REPLACE INTO vectors
            (key, vector, metadata, dimension, timestamp, access_count, last_access)
            VALUES (?, ?, ?, ?, ?,
                    COALESCE((SELECT access_count FROM vectors WHERE key = ?), 0) + 1,
                    ?)
            """,
            values
        )
        await self._db.commit()
        
        self._stats["total_puts"] += len(entries)
        
        # Check if cleanup needed
        await self._maybe_cleanup()
        
    def _add_to_memory_cache(self, key: str, entry: CachedVector) -> None:
        """Add entry to memory cache with LRU eviction.
        
        Args:
            key: Cache key
            entry: Cache entry
        """
        # Remove oldest if at capacity
        if len(self._memory_cache) >= self._memory_cache_size:
            # Find least recently used
            lru_key = min(self._memory_cache.keys(), 
                         key=lambda k: self._memory_cache[k].access_count)
            del self._memory_cache[lru_key]
            
        self._memory_cache[key] = entry
        
    async def _maybe_cleanup(self) -> None:
        """Cleanup old entries if cache is too large."""
        # Check size periodically
        if self._stats["total_puts"] % 100 != 0:
            return
            
        cursor = await self._db.execute("SELECT COUNT(*) as count FROM vectors")
        row = await cursor.fetchone()
        count = row["count"]
        
        if count > self.max_size:
            # Delete oldest entries
            to_delete = count - int(self.max_size * 0.9)  # Keep 90% after cleanup
            
            await self._db.execute(
                """
                DELETE FROM vectors WHERE key IN (
                    SELECT key FROM vectors 
                    ORDER BY last_access ASC 
                    LIMIT ?
                )
                """,
                (to_delete,)
            )
            await self._db.commit()
            
            self._stats["evictions"] += to_delete
            logger.info(f"Evicted {to_delete} entries from vector cache")
            
            # Update stats
            await self._save_stats()
            
    async def _save_stats(self) -> None:
        """Save statistics to database."""
        await self._db.execute(
            """
            UPDATE cache_stats SET
                total_hits = ?,
                total_misses = ?,
                total_evictions = ?,
                last_cleanup = ?
            WHERE id = 1
            """,
            (self._stats["hits"], self._stats["misses"], 
             self._stats["evictions"], time.time())
        )
        await self._db.commit()
        
    async def clear(self) -> None:
        """Clear all cached vectors."""
        await self._db.execute("DELETE FROM vectors")
        await self._db.commit()
        self._memory_cache.clear()
        logger.info("Cleared vector cache")
        
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary of statistics
        """
        cursor = await self._db.execute("SELECT COUNT(*) as count FROM vectors")
        row = await cursor.fetchone()
        
        hit_rate = 0
        if self._stats["total_gets"] > 0:
            hit_rate = self._stats["hits"] / self._stats["total_gets"]
            
        return {
            "total_items": row["count"],
            "memory_items": len(self._memory_cache),
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "hit_rate": hit_rate,
            "evictions": self._stats["evictions"],
            "total_gets": self._stats["total_gets"],
            "total_puts": self._stats["total_puts"]
        }
        
    async def close(self) -> None:
        """Close database connection."""
        if self._db:
            await self._save_stats()
            await self._db.close()
            self._db = None