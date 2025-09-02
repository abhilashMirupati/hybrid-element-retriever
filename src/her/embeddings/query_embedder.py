"""Query embedder with deterministic numpy-based vectors.

Provides a lightweight, dependency-friendly implementation that returns
numpy arrays and supports both single and batch encode operations. The
embedding is stable across runs and inputs by hashing the text.
"""

from __future__ import annotations

import hashlib
from typing import List

import numpy as np


class QueryEmbedder:
    """Deterministic query embedder.

    Args:
        dim: Output embedding dimensionality
    """

    def __init__(self, dim: int = 384) -> None:
        self.dim = int(dim)

    def _hash_to_vector(self, text: str) -> np.ndarray:
        """Map text to a stable float32 vector of length self.dim.

        Uses SHA-256 digest material repeated to required length, then
        converts to uint32 chunks and normalizes to [-1, 1].
        """
        # Use text-specific salt to avoid collisions across different dims
        seed_bytes = hashlib.sha256(text.encode("utf-8")).digest()
        # Need 4 bytes per float (uint32 source)
        needed_bytes = self.dim * 4
        buf = (seed_bytes * ((needed_bytes // len(seed_bytes)) + 1))[:needed_bytes]
        vec = np.frombuffer(buf, dtype=np.uint32, count=self.dim)
        # Normalize into [-1, 1]
        vec = (vec % 1000003).astype(np.float32)
        vec = (vec / 500001.5) - 1.0
        # L2 normalize for cosine stability
        norm = float(np.linalg.norm(vec))
        if norm > 0:
            vec = vec / norm
        return vec.astype(np.float32, copy=False)

    def encode(self, text: str) -> np.ndarray:
        """Encode a single string to shape (dim,) float32 numpy array."""
        return self._hash_to_vector(text)

    def batch_encode(self, texts: List[str]) -> np.ndarray:
        """Encode a list of strings to shape (N, dim) float32 numpy array."""
        if not texts:
            return np.zeros((0, self.dim), dtype=np.float32)
        mats = [self._hash_to_vector(t) for t in texts]
        return np.stack(mats, axis=0)

    # Back-compat aliases expected by some call sites
    def embed(self, text: str) -> np.ndarray:  # type: ignore[override]
        return self.encode(text)

    def embed_batch(self, texts: List[str]) -> np.ndarray:  # type: ignore[override]
        return self.batch_encode(texts)
