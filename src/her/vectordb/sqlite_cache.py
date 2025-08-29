"""Enhanced SQLite cache with batch operations and hit tracking."""

import sqlite3
import json
import pickle
import time
import logging
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
from threading import Lock
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class CacheStats:
    """Cache statistics."""
    total_gets: int = 0
    total_puts: int = 0
    hits: int = 0
    misses: int = 0
    batch_gets: int = 0
    batch_puts: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


class SQLiteKV:
    """SQLite key-value store with batch operations and statistics."""
    
    def __init__(self, path: str, max_size_mb: int = 100):
        """Initialize SQLite cache.
        
        Args:
            path: Path to SQLite database
            max_size_mb: Maximum cache size in MB
        """
        self.path = Path(path).expanduser().resolve()
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.lock = Lock()
        self.stats = CacheStats()
        
        # Ensure directory exists
        self.path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize database schema."""
        with sqlite3.connect(self.path) as conn:
            # Main cache table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS kv (
                    k TEXT PRIMARY KEY,
                    v BLOB,
                    timestamp REAL DEFAULT 0,
                    hits INTEGER DEFAULT 0,
                    size_bytes INTEGER DEFAULT 0
                )
            """)
            
            # Embedding cache table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS embeddings (
                    element_hash TEXT PRIMARY KEY,
                    vector BLOB,
                    dimension INTEGER,
                    model_name TEXT,
                    timestamp REAL,
                    hits INTEGER DEFAULT 0
                )
            """)
            
            # Promotion table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS promotions (
                    original_selector TEXT,
                    promoted_selector TEXT,
                    success_count INTEGER DEFAULT 0,
                    failure_count INTEGER DEFAULT 0,
                    last_used REAL,
                    PRIMARY KEY (original_selector, promoted_selector)
                )
            """)
            
            conn.commit()
    
    def get(self, k: str) -> Optional[bytes]:
        """Get value from cache (backward compatible)."""
        self.stats.total_gets += 1
        
        with self.lock:
            with sqlite3.connect(self.path) as conn:
                cursor = conn.execute("SELECT v, hits FROM kv WHERE k = ?", (k,))
                row = cursor.fetchone()
                
                if row:
                    value, hits = row
                    conn.execute("UPDATE kv SET hits = ? WHERE k = ?", (hits + 1, k))
                    conn.commit()
                    self.stats.hits += 1
                    return value
                else:
                    self.stats.misses += 1
                    return None
    
    def put(self, k: str, v: bytes) -> None:
        """Store value in cache (backward compatible)."""
        self.stats.total_puts += 1
        
        with self.lock:
            with sqlite3.connect(self.path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO kv (k, v, timestamp, hits, size_bytes)
                    VALUES (?, ?, ?, 0, ?)
                """, (k, v, time.time(), len(v)))
                conn.commit()
    
    def batch_get(self, keys: List[str]) -> Dict[str, bytes]:
        """Get multiple values from cache."""
        self.stats.batch_gets += 1
        results = {}
        
        with self.lock:
            with sqlite3.connect(self.path) as conn:
                placeholders = ','.join('?' * len(keys))
                cursor = conn.execute(
                    f"SELECT k, v, hits FROM kv WHERE k IN ({placeholders})",
                    keys
                )
                
                for key, value, hits in cursor.fetchall():
                    conn.execute("UPDATE kv SET hits = ? WHERE k = ?", (hits + 1, key))
                    results[key] = value
                    self.stats.hits += 1
                
                conn.commit()
        
        for key in keys:
            if key not in results:
                self.stats.misses += 1
        
        return results
    
    def batch_put(self, items: Dict[str, bytes]) -> None:
        """Store multiple values in cache."""
        self.stats.batch_puts += 1
        
        with self.lock:
            with sqlite3.connect(self.path) as conn:
                timestamp = time.time()
                data = [(k, v, timestamp, 0, len(v)) for k, v in items.items()]
                
                conn.executemany("""
                    INSERT OR REPLACE INTO kv (k, v, timestamp, hits, size_bytes)
                    VALUES (?, ?, ?, ?, ?)
                """, data)
                
                conn.commit()
                self.stats.total_puts += len(data)
    
    def get_embedding(self, element_hash: str) -> Optional[List[float]]:
        """Get cached embedding for element."""
        with self.lock:
            with sqlite3.connect(self.path) as conn:
                cursor = conn.execute(
                    "SELECT vector, hits FROM embeddings WHERE element_hash = ?",
                    (element_hash,)
                )
                row = cursor.fetchone()
                
                if row:
                    vector_blob, hits = row
                    conn.execute(
                        "UPDATE embeddings SET hits = ? WHERE element_hash = ?",
                        (hits + 1, element_hash)
                    )
                    conn.commit()
                    
                    try:
                        return pickle.loads(vector_blob)
                    except Exception:
                        return None
                
                return None
    
    def put_embedding(self, element_hash: str, vector: List[float], model_name: str = "default") -> None:
        """Store embedding in cache."""
        with self.lock:
            try:
                vector_blob = pickle.dumps(vector)
                
                with sqlite3.connect(self.path) as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO embeddings 
                        (element_hash, vector, dimension, model_name, timestamp, hits)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (element_hash, vector_blob, len(vector), model_name, time.time(), 0))
                    conn.commit()
            except Exception as e:
                logger.error(f"Failed to cache embedding: {e}")
    
    def batch_get_embeddings(self, element_hashes: List[str]) -> Dict[str, List[float]]:
        """Get multiple embeddings from cache."""
        results = {}
        
        with self.lock:
            with sqlite3.connect(self.path) as conn:
                placeholders = ','.join('?' * len(element_hashes))
                cursor = conn.execute(
                    f"SELECT element_hash, vector, hits FROM embeddings WHERE element_hash IN ({placeholders})",
                    element_hashes
                )
                
                for element_hash, vector_blob, hits in cursor.fetchall():
                    conn.execute(
                        "UPDATE embeddings SET hits = ? WHERE element_hash = ?",
                        (hits + 1, element_hash)
                    )
                    
                    try:
                        results[element_hash] = pickle.loads(vector_blob)
                    except Exception:
                        pass
                
                conn.commit()
        
        return results
    
    def batch_put_embeddings(self, embeddings: Dict[str, List[float]], model_name: str = "default") -> None:
        """Store multiple embeddings in cache."""
        with self.lock:
            with sqlite3.connect(self.path) as conn:
                timestamp = time.time()
                data = []
                
                for element_hash, vector in embeddings.items():
                    try:
                        vector_blob = pickle.dumps(vector)
                        data.append((element_hash, vector_blob, len(vector), model_name, timestamp, 0))
                    except Exception:
                        pass
                
                conn.executemany("""
                    INSERT OR REPLACE INTO embeddings 
                    (element_hash, vector, dimension, model_name, timestamp, hits)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, data)
                
                conn.commit()
    
    def get_promotion(self, original_selector: str) -> Optional[str]:
        """Get promoted selector for original."""
        with self.lock:
            with sqlite3.connect(self.path) as conn:
                cursor = conn.execute("""
                    SELECT promoted_selector 
                    FROM promotions 
                    WHERE original_selector = ? 
                    ORDER BY success_count DESC, last_used DESC
                    LIMIT 1
                """, (original_selector,))
                
                row = cursor.fetchone()
                return row[0] if row else None
    
    def record_promotion(self, original_selector: str, promoted_selector: str, success: bool) -> None:
        """Record promotion result."""
        with self.lock:
            with sqlite3.connect(self.path) as conn:
                cursor = conn.execute("""
                    SELECT success_count, failure_count 
                    FROM promotions 
                    WHERE original_selector = ? AND promoted_selector = ?
                """, (original_selector, promoted_selector))
                
                row = cursor.fetchone()
                
                if row:
                    success_count, failure_count = row
                    if success:
                        success_count += 1
                    else:
                        failure_count += 1
                    
                    conn.execute("""
                        UPDATE promotions 
                        SET success_count = ?, failure_count = ?, last_used = ?
                        WHERE original_selector = ? AND promoted_selector = ?
                    """, (success_count, failure_count, time.time(), original_selector, promoted_selector))
                else:
                    conn.execute("""
                        INSERT INTO promotions 
                        (original_selector, promoted_selector, success_count, failure_count, last_used)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        original_selector, promoted_selector,
                        1 if success else 0, 0 if success else 1, time.time()
                    ))
                
                conn.commit()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = asdict(self.stats)
        
        with self.lock:
            with sqlite3.connect(self.path) as conn:
                cursor = conn.execute("SELECT COUNT(*), SUM(size_bytes) FROM kv")
                count, size = cursor.fetchone()
                stats['cache_entries'] = count or 0
                stats['cache_size_bytes'] = size or 0
                
                cursor = conn.execute("SELECT COUNT(*) FROM embeddings")
                stats['embedding_entries'] = cursor.fetchone()[0] or 0
                
                cursor = conn.execute("SELECT COUNT(*) FROM promotions")
                stats['promotion_entries'] = cursor.fetchone()[0] or 0
        
        return stats