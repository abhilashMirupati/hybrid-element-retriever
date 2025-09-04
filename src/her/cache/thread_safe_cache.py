"""Thread-safe two-tier cache implementation."""

import json
import threading
import time
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, Optional


class ThreadSafeTwoTierCache:
    """Thread-safe two-tier cache with LRU memory cache and persistent disk cache."""
    
    def __init__(self, max_memory_items: int = 1000, cache_dir: str = "/tmp/her_cache"):
        """Initialize thread-safe cache.
        
        Args:
            max_memory_items: Maximum items in memory cache
            cache_dir: Directory for persistent cache
        """
        self.max_memory_items = max_memory_items
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Memory cache (LRU)
        self.memory_cache: OrderedDict = OrderedDict()
        
        # Thread safety
        self.lock = threading.RLock()  # Reentrant lock
        self.stats = {
            "hits": 0,
            "misses": 0,
            "writes": 0
        }
        self.stats_lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache (thread-safe).
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        if key is None:
            return None
            
        with self.lock:
            # Check memory cache first
            if key in self.memory_cache:
                # Move to end (LRU)
                self.memory_cache.move_to_end(key)
                self._record_hit()
                return self.memory_cache[key]
            
            # Check disk cache
            cache_file = self.cache_dir / f"{hash(key)}.json"
            if cache_file.exists():
                try:
                    with open(cache_file, 'r') as f:
                        value = json.load(f)
                    
                    # Add to memory cache
                    self._add_to_memory(key, value)
                    self._record_hit()
                    return value
                except Exception:
                    pass
            
            self._record_miss()
            return None
    
    def put(self, key: str, value: Any) -> None:
        """Put value in cache (thread-safe).
        
        Args:
            key: Cache key
            value: Value to cache
        """
        if key is None:
            return
            
        with self.lock:
            # Add to memory cache
            self._add_to_memory(key, value)
            
            # Write to disk cache
            cache_file = self.cache_dir / f"{hash(key)}.json"
            try:
                with open(cache_file, 'w') as f:
                    json.dump(value, f)
                self._record_write()
            except Exception:
                pass
    
    def set(self, key: str, value: Any) -> None:
        """Alias for put (for compatibility)."""
        self.put(key, value)
    
    def clear(self) -> None:
        """Clear all caches (thread-safe)."""
        with self.lock:
            self.memory_cache.clear()
            
            # Clear disk cache
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    cache_file.unlink()
                except Exception:
                    pass
    
    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics (thread-safe)."""
        with self.stats_lock:
            return self.stats.copy()
    
    def _add_to_memory(self, key: str, value: Any) -> None:
        """Add to memory cache with LRU eviction.
        
        Note: Must be called with lock held.
        """
        if key in self.memory_cache:
            # Move to end
            self.memory_cache.move_to_end(key)
        else:
            # Add new
            self.memory_cache[key] = value
            
            # Evict if needed
            if len(self.memory_cache) > self.max_memory_items:
                # Remove oldest
                self.memory_cache.popitem(last=False)
        
        self.memory_cache[key] = value
    
    def _record_hit(self) -> None:
        """Record cache hit."""
        with self.stats_lock:
            self.stats["hits"] += 1
    
    def _record_miss(self) -> None:
        """Record cache miss."""
        with self.stats_lock:
            self.stats["misses"] += 1
    
    def _record_write(self) -> None:
        """Record cache write."""
        with self.stats_lock:
            self.stats["writes"] += 1