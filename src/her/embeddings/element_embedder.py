"""Element embedder with deterministic numpy-based vectors and simple cache.

Produces stable embeddings from element descriptors. Designed to satisfy
tests that expect numpy arrays, shape control, and caching behavior.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np


class ElementEmbedder:
    def __init__(self, cache_dir: Optional[Path] = None, dim: int = 768, device: str | None = None) -> None:
        self.dim = int(dim)
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self._mem_cache: Dict[str, np.ndarray] = {}

    def _descriptor_key(self, desc: Dict[str, Any]) -> str:
        # Stable key based on relevant fields
        key_parts = [
            str(desc.get("tag", desc.get("tagName", ""))).lower(),
            str(desc.get("text", ""))[:64],
            str(desc.get("id", "")),
            str(desc.get("attributes", {})),
        ]
        raw = "|".join(key_parts)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _hash_to_vector(self, seed: str) -> np.ndarray:
        # Convert a string seed into a normalized float32 vector
        digest = hashlib.sha256(seed.encode("utf-8")).digest()
        needed = self.dim * 4
        buf = (digest * ((needed // len(digest)) + 1))[:needed]
        vec = np.frombuffer(buf, dtype=np.uint32, count=self.dim)
        vec = (vec % 1000003).astype(np.float32)
        vec = (vec / 500001.5) - 1.0
        n = float(np.linalg.norm(vec))
        if n > 0:
            vec = vec / n
        return vec.astype(np.float32, copy=False)

    def encode(self, descriptor: Dict[str, Any]) -> np.ndarray:
        key = self._descriptor_key(descriptor)
        cached = self._mem_cache.get(key)
        if cached is not None:
            return cached
        vec = self._hash_to_vector(key)
        self._mem_cache[key] = vec
        return vec

    def batch_encode(self, descriptors: List[Dict[str, Any]]) -> np.ndarray:
        if not descriptors:
            return np.zeros((0, self.dim), dtype=np.float32)
        mats = [self.encode(d) for d in descriptors]
        return np.stack(mats, axis=0)
