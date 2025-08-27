# PLACE: src/her/embeddings/query_embedder.py
"""MiniLM/E5-small ONNX (optional) or deterministic hash fallback for query text."""
from __future__ import annotations
from typing import Optional
import numpy as np
from ..utils import sha1_of
from .cache import EmbeddingCache

DIM = 16  # small for demo; can be 384+ with a real model
MODEL_VERSION = "minilm-e5-small-onnx-or-hash"

class QueryEmbedder:
    def __init__(self, cache: Optional[EmbeddingCache] = None) -> None:
        self.cache = cache or EmbeddingCache()

    def embed(self, text: str) -> np.ndarray:
        key = f"q:{MODEL_VERSION}:{text}"
        hit = self.cache.get(key)
        if hit is not None:
            return hit
        # fallback deterministic vector
        h = sha1_of(text)
        rng = np.random.default_rng(int(h[:8], 16))
        vec = rng.normal(size=(DIM,)).astype(np.float32)
        # L2 normalise
        n = np.linalg.norm(vec) + 1e-8
        vec = vec / n
        self.cache.put(key, vec)
        return vec
