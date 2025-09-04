"""Embedding cache that works with or without numpy."""

from typing import Dict, Optional, Union, List
import pickle
import hashlib
from pathlib import Path

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None  # type: ignore


class EmbeddingCache:
    """Two-tier embedding cache with memory and optional disk storage.
    
    Works with both numpy arrays and Python lists.
    """
    
    def __init__(self, cache_dir: Optional[Path] = None, max_memory_items: int = 1000):
        """Initialize cache.
        
        Args:
            cache_dir: Optional directory for disk cache
            max_memory_items: Maximum items in memory cache
        """
        self.memory_cache: Dict[str, Union[List[float], 'np.ndarray']] = {}
        self.max_memory_items = max_memory_items
        self.cache_dir = cache_dir
        
        if cache_dir:
            cache_dir.mkdir(parents=True, exist_ok=True)
    
    def get(self, key: str) -> Optional[Union[List[float], 'np.ndarray']]:
        """Get embedding from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached embedding or None
        """
        # Check memory cache
        if key in self.memory_cache:
            return self.memory_cache[key]
        
        # Check disk cache if available
        if self.cache_dir:
            cache_file = self.cache_dir / f"{self._hash_key(key)}.pkl"
            if cache_file.exists():
                try:
                    with open(cache_file, 'rb') as f:
                        value = pickle.load(f)
                    
                    # Add to memory cache
                    self._add_to_memory(key, value)
                    return value
                except Exception:
                    # Corrupted cache file, remove it
                    cache_file.unlink(missing_ok=True)
        
        return None
    
    def put(self, key: str, value: Union[List[float], 'np.ndarray']) -> None:
        """Store embedding in cache.
        
        Args:
            key: Cache key
            value: Embedding to cache
        """
        # Add to memory cache
        self._add_to_memory(key, value)
        
        # Save to disk if cache_dir available
        if self.cache_dir:
            cache_file = self.cache_dir / f"{self._hash_key(key)}.pkl"
            try:
                with open(cache_file, 'wb') as f:
                    pickle.dump(value, f)
            except Exception:
                # Failed to save, but don't crash
                pass
    
    def _add_to_memory(self, key: str, value: Union[List[float], 'np.ndarray']) -> None:
        """Add item to memory cache with LRU eviction."""
        # Evict oldest if at capacity
        if len(self.memory_cache) >= self.max_memory_items:
            # Simple FIFO eviction (could be improved to LRU)
            first_key = next(iter(self.memory_cache))
            del self.memory_cache[first_key]
        
        self.memory_cache[key] = value
    
    def _hash_key(self, key: str) -> str:
        """Hash key for filesystem storage."""
        return hashlib.md5(key.encode()).hexdigest()
    
    def clear(self) -> None:
        """Clear all cache."""
        self.memory_cache.clear()
        
        if self.cache_dir:
            for cache_file in self.cache_dir.glob("*.pkl"):
                cache_file.unlink(missing_ok=True)
    
    def size(self) -> int:
        """Get number of items in memory cache."""
        return len(self.memory_cache)