# src/her/rank/fusion.py
"""
Fusion ranking logic for Hybrid Element Retriever.
Combines semantic similarity (intent ↔ element embeddings)
with optional heuristics and stable tie-breaking.
"""

from typing import Dict, Any, List
import numpy as np
from collections import namedtuple

ElementScore = namedtuple("ElementScore", ["element", "xpath", "score", "meta"])


class FusionScorer:
    def __init__(self, alpha: float = 0.8, beta: float = 0.15, gamma: float = 0.05):
        """
        Weights:
            alpha: semantic similarity weight
            beta: heuristic weight (e.g., text overlap)
            gamma: structural weight (e.g., depth/role)
        """
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma

    def score_elements(
        self,
        intent_vec: np.ndarray,
        embeddings: List[np.ndarray],
        elements: List[tuple],
    ) -> List[Dict[str, Any]]:
        """
        Score DOM elements against the intent.

        Args:
            intent_vec: np.ndarray, embedding of the intent
            embeddings: list[np.ndarray], element embeddings
            elements: list[(element_dict, hash)], same order as embeddings

        Returns:
            list[dict]: sorted candidate list with strict schema
        """
        scored = []
        for emb, (el, el_hash) in zip(embeddings, elements):
            # --- Semantic similarity
            sim = self._cosine(intent_vec, emb)

            # --- Heuristic overlap (cheap text match)
            heur = self._heuristic(intent_vec, el)

            # --- Structural bonus (shallow depth preferred)
            depth = el.get("depth", 5)
            struct = 1.0 / (1 + depth)

            # --- Weighted fusion
            score = self.alpha * sim + self.beta * heur + self.gamma * struct

            scored.append(
                {
                    "element": el,
                    "xpath": el.get("xpath"),
                    "score": float(score),
                    "meta": {
                        "similarity": float(sim),
                        "heuristic": float(heur),
                        "struct": float(struct),
                        "hash": el_hash,
                    },
                }
            )

        # --- Stable sort: score desc, then xpath asc for determinism
        scored.sort(key=lambda x: (-x["score"], x["xpath"] or ""))
        return scored

    def _cosine(self, a: np.ndarray, b: np.ndarray) -> float:
        if a is None or b is None:
            return 0.0
        denom = (np.linalg.norm(a) * np.linalg.norm(b))
        if denom == 0:
            return 0.0
        return float(np.dot(a, b) / denom)

    def _heuristic(self, intent_vec: np.ndarray, el: Dict[str, Any]) -> float:
        """Cheap overlap: does intent text appear in element text?"""
        intent_text = getattr(intent_vec, "text", "")  # fallback if passed raw
        el_text = (el.get("text") or "").lower()
        if not intent_text or not el_text:
            return 0.0
        return 1.0 if intent_text.lower() in el_text else 0.0
