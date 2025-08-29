from __future__ import annotations
from collections import OrderedDict
from threading import Lock
from typing import Generic, Optional, TypeVar

K = TypeVar('K')
V = TypeVar('V')


class LRUCache(Generic[K, V]):
    """Thread-safe LRU cache with hit/miss counters.

    - Capacity-bounded with eviction of least-recently-used entries
    - get promotes entry to most recently used
    - put inserts/replaces entry and evicts when over capacity
    - counters: hits, misses, gets, puts
    """

    def __init__(self, capacity: int = 256) -> None:
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self.capacity = int(capacity)
        self._data: OrderedDict[K, V] = OrderedDict()
        self._lock: Lock = Lock()
        self.hits: int = 0
        self.misses: int = 0
        self.gets: int = 0
        self.puts: int = 0

    def get(self, key: K) -> Optional[V]:
        """Get a value and mark as recently used."""
        with self._lock:
            self.gets += 1
            if key in self._data:
                value = self._data.pop(key)
                self._data[key] = value
                self.hits += 1
                return value
            self.misses += 1
            return None

    def put(self, key: K, value: V) -> None:
        """Insert or update a value; evict LRU if capacity exceeded."""
        with self._lock:
            self.puts += 1
            if key in self._data:
                self._data.pop(key)
            self._data[key] = value
            while len(self._data) > self.capacity:
                self._data.popitem(last=False)

    def clear(self) -> None:
        with self._lock:
            self._data.clear()
            self.hits = 0
            self.misses = 0
            self.gets = 0
            self.puts = 0

    def __len__(self) -> int:  # pragma: no cover - trivial
        with self._lock:
            return len(self._data)

