from __future__ import annotations
from collections import OrderedDict
from typing import Generic, TypeVar
K=TypeVar('K'); V=TypeVar('V')
class LRUCache(Generic[K,V]):
    def __init__(self, capacity:int=256)->None:
        self.capacity=capacity; self._data:OrderedDict[K,V]=OrderedDict()
    def get(self, k:K):
        if k in self._data:
            v=self._data.pop(k); self._data[k]=v; return v
        return None
    def put(self, k:K, v:V)->None:
        if k in self._data: self._data.pop(k)
        self._data[k]=v
        if len(self._data)>self.capacity: self._data.popitem(last=False)
