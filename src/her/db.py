from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import numpy as np

from .hashing import element_dom_hash

def _l2(a: np.ndarray, eps=1e-12):
    n = np.linalg.norm(a, axis=-1, keepdims=True)
    n = np.maximum(n, eps)
    return a / n

@dataclass
class VectorIndex:
    """
    Simple in-memory vector index keyed by element dom_hash.
    Stores:
      - meta: list of element dicts (+ dom_hash)
      - vecs: float32 matrix (N, D)
    """
    dim: Optional[int] = None
    meta: List[Dict] = field(default_factory=list)
    vecs: Optional[np.ndarray] = None
    key_to_row: Dict[str, int] = field(default_factory=dict)

    def upsert(self, elements: List[Dict], embedder) -> None:
        """Delta-embed only new or changed elements by dom_hash."""
        new_meta = []
        need_embed = []
        rows_map = []

        for el in elements:
            h = element_dom_hash(el)
            el["_dom_hash"] = h
            if h in self.key_to_row:
                # unchanged -> keep existing
                rows_map.append(self.key_to_row[h])
            else:
                new_meta.append(el)
                need_embed.append(el)
                rows_map.append(None)

        # Embed only new
        if need_embed:
            vecs_new = embedder.batch_encode(need_embed).astype(np.float32)
            if self.dim is None:
                self.dim = int(vecs_new.shape[1])
            elif vecs_new.shape[1] != self.dim:
                # pad or truncate to maintain consistency
                D = self.dim
                fixed = np.zeros((vecs_new.shape[0], D), dtype=np.float32)
                k = min(D, vecs_new.shape[1]); fixed[:, :k] = vecs_new[:, :k]
                vecs_new = fixed

            # Append to storage
            if self.vecs is None:
                self.vecs = vecs_new
                base = 0
            else:
                base = int(self.vecs.shape[0])
                self.vecs = np.vstack([self.vecs, vecs_new])

            for j, el in enumerate(new_meta):
                row = base + j
                self.key_to_row[el["_dom_hash"]] = row
                self.meta.append(el)

        # rows_map now maps input elements to existing/new rows; not needed further

    def search(self, qvec: np.ndarray, topk: int = 10):
        """Brute-force cosine on CPU; acceptable for few-thousand elements."""
        if self.vecs is None or self.vecs.size == 0:
            return []
        q = qvec.astype(np.float32, copy=False).reshape(1, -1)
        Q = _l2(q)[0]
        V = _l2(self.vecs)
        scores = V @ Q
        order = np.argsort(-scores)
        topk = max(1, min(topk, len(order)))
        out = []
        for i in order[:topk]:
            out.append({"index": int(i), "score": float(scores[i]), "meta": self.meta[i]})
        return out
