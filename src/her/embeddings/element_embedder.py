# PLACE: src/her/embeddings/element_embedder.py
"""Markup-aware embedder (optional ONNX) or deterministic fallback for element descriptors."""
from __future__ import annotations
from typing import Dict, Any, Optional
import numpy as np
from ..utils import sha1_of
from .cache import EmbeddingCache

DIM = 16
MODEL_VERSION = "markuplm-base-onnx-or-hash"

class ElementEmbedder:
    def __init__(self, cache: Optional[EmbeddingCache] = None) -> None:
        self.cache = cache or EmbeddingCache()

    def embed(self, element: Dict[str, Any]) -> np.ndarray:
        sig = (element.get("tag"), element.get("text"), element.get("role"), element.get("name"))
        key = f"e:{MODEL_VERSION}:{sig}"
        hit = self.cache.get(key)
        if hit is not None:
            return hit
        h = sha1_of(sig)
        rng = np.random.default_rng(int(h[:8], 16))
        vec = rng.normal(size=(DIM,)).astype(np.float32)
        vec = vec / (np.linalg.norm(vec) + 1e-8)
        self.cache.put(key, vec)
        return vec
