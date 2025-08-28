"""Lightweight FAISS wrapper for storing and querying embeddings.

This module provides an in‑memory fallback store that exposes the minimal
operations used by the rest of the system.  When FAISS is available it
could be used for fast vector similarity search.  This implementation
appends vectors to a list and performs a linear scan on query.
"""

from typing import List, Tuple, Optional

import numpy as np


class InMemoryVectorStore:
    def __init__(self, dim: Optional[int] = None) -> None:
        self.vectors: List[np.ndarray] = []
        self.payloads: List[dict] = []
        self.dim: Optional[int] = dim

    def add(self, vector: np.ndarray, payload: dict) -> None:
        self.vectors.append(vector)
        self.payloads.append(payload)

    def search(self, query_vec: np.ndarray, top_k: int) -> List[Tuple[dict, float]]:
        """Return top_k payloads sorted by cosine similarity descending."""
        sims = []
        for vec, payload in zip(self.vectors, self.payloads):
            denom = np.linalg.norm(vec) * np.linalg.norm(query_vec)
            sim = float(np.dot(vec, query_vec) / denom) if denom != 0 else 0.0
            sims.append((payload, sim))
        sims.sort(key=lambda x: x[1], reverse=True)
        return sims[:top_k]

    def size(self) -> int:
        return len(self.vectors)
