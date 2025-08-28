from __future__ import annotations
from typing import List, Optional
import numpy as np

from .cache import EmbeddingCache
from ._resolve import get_query_resolver, ONNXModelResolver
from ..utils import sha1_of  # type: ignore


class QueryEmbedder:
    """Query embedder that uses ONNX resolver with two-tier cache.

    Exposes methods used by tests:
      - embed(text) -> np.ndarray
      - embed_batch(texts) -> List[np.ndarray]
      - similarity(vec1, vec2) -> float
      - attributes: cache, resolver, dim
    """

    def __init__(self, cache: Optional[EmbeddingCache] = None, resolver: Optional[ONNXModelResolver] = None) -> None:
        self.cache = cache or EmbeddingCache()
        self.resolver = resolver or get_query_resolver()
        self.dim = int(self.resolver.embedding_dim)

    def _key(self, text: str) -> str:
        return f"q|{sha1_of(text)}|{self.dim}"

    def embed(self, text: str) -> np.ndarray:
        key = self._key(text)
        hit = self.cache.get(key)
        if hit is not None:
            return hit.astype('float32')
        vec = self.resolver.embed(text).astype('float32')
        self.cache.put(key, vec)
        return vec

    def embed_batch(self, texts: List[str]) -> List[np.ndarray]:
        return [self.embed(t) for t in texts]

    @staticmethod
    def similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        v1 = vec1.astype('float32'); v2 = vec2.astype('float32')
        denom = float(np.linalg.norm(v1) * np.linalg.norm(v2))
        return float(np.dot(v1, v2) / denom) if denom != 0 else 0.0
