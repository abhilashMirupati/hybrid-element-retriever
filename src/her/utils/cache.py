import os
import json
import hashlib
import pickle
import threading
from collections import OrderedDict
from typing import Any, Optional


class TwoTierCache:
    """
    Two-tier cache with memory (LRU) and disk persistence.
    Used for embeddings and DOM snapshots in HER.
    """

    def __init__(self, cache_dir: str, max_memory_items: int = 1000):
        self.cache_dir = os.path.abspath(cache_dir)
        os.makedirs(self.cache_dir, exist_ok=True)

        self.max_memory_items = max_memory_items
        self.memory_cache = OrderedDict()
        self.lock = threading.Lock()

        self.hit_count = 0
        self.miss_count = 0

    def _hash_key(self, key: str) -> str:
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    def _disk_path(self, key: str) -> str:
        return os.path.join(self.cache_dir, f"{self._hash_key(key)}.pkl")

    def get_raw(self, key: str) -> Optional[Any]:
        """
        Direct fetch from memory or disk without triggering higher-level logic.
        Used for cold-start detection and incremental prepopulation.
        """
        with self.lock:
            if key in self.memory_cache:
                return self.memory_cache[key]

        path = self._disk_path(key)
        if os.path.exists(path):
            try:
                with open(path, "rb") as f:
                    return pickle.load(f)
            except Exception:
                return None
        return None

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache, update stats.
        """
        with self.lock:
            if key in self.memory_cache:
                self.memory_cache.move_to_end(key)
                self.hit_count += 1
                return self.memory_cache[key]

        path = self._disk_path(key)
        if os.path.exists(path):
            try:
                with open(path, "rb") as f:
                    value = pickle.load(f)
                with self.lock:
                    self.memory_cache[key] = value
                    self.memory_cache.move_to_end(key)
                    if len(self.memory_cache) > self.max_memory_items:
                        self.memory_cache.popitem(last=False)
                    self.hit_count += 1
                return value
            except Exception:
                pass

        self.miss_count += 1
        return None

    def put(self, key: str, value: Any) -> None:
        """
        Insert into memory and disk atomically.
        """
        with self.lock:
            self.memory_cache[key] = value
            self.memory_cache.move_to_end(key)
            if len(self.memory_cache) > self.max_memory_items:
                self.memory_cache.popitem(last=False)

        path = self._disk_path(key)
        try:
            with open(path, "wb") as f:
                pickle.dump(value, f)
        except Exception:
            pass

    def stats(self) -> dict:
        """
        Return cache statistics.
        """
        with self.lock:
            return {
                "hits": self.hit_count,
                "misses": self.miss_count,
                "memory_items": len(self.memory_cache),
                "disk_items": len(os.listdir(self.cache_dir)),
            }
