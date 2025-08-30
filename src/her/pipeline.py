# src/her/pipeline.py
"""
Hybrid Element Retrieval Pipeline
Wires together intent embeddings (MiniLM), element embeddings (MarkupLM),
and ranking fusion into a single flow.
"""

from typing import Dict, Any, List
import time

from her.embeddings.text_embedder import TextEmbedder
from her.embeddings.element_embedder import ElementEmbedder
from her.rank.fusion import FusionScorer
from her.cache.two_tier import TwoTierCache


class HybridPipeline:
    def __init__(self, cache_dir: str = ".cache", device: str = "cpu"):
        self.text_embedder = TextEmbedder(device=device)
        self.element_embedder = ElementEmbedder(device=device)
        self.scorer = FusionScorer()
        self.cache = TwoTierCache(cache_dir)

    def query(self, intent: str, dom_snapshot: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Main entrypoint.
        Args:
            intent: natural language user request (e.g., "click login button")
            dom_snapshot: list of element dicts from DOM+AX
        Returns:
            dict: {element, xpath, confidence, strategy, metadata}
        """
        start = time.time()

        # --- 1. Intent embedding
        intent_vec = self.text_embedder.batch_encode([intent])[0]

        # --- 2. Element embeddings (with caching)
        embeddings = []
        elements = []
        for el in dom_snapshot:
            el_hash = self._hash_el(el)
            cached = self.cache.get(el_hash)
            if cached is not None:
                emb = cached
            else:
                emb = self.element_embedder.batch_encode([el])[0]
                self.cache.set(el_hash, emb)
            embeddings.append(emb)
            elements.append((el, el_hash))

        # --- 3. Retrieval scoring
        scored = self.scorer.score_elements(intent_vec, embeddings, elements)

        # --- 4. Best candidate (fallback to empty if none)
        if not scored:
            return {
                "element": None,
                "xpath": None,
                "confidence": 0.0,
                "strategy": "none",
                "metadata": {"error": "no candidates"},
            }

        best = scored[0]
        latency = time.time() - start

        return {
            "element": best["element"],
            "xpath": best["xpath"],
            "confidence": best["score"],
            "strategy": "fusion",
            "metadata": {
                "latency_sec": latency,
                "cache_hits": self.cache.stats()["hits"],
                "cache_misses": self.cache.stats()["misses"],
            },
        }

    def _hash_el(self, el: Dict[str, Any]) -> str:
        """Stable hash for DOM element dict."""
        import hashlib, json
        m = hashlib.sha256()
        m.update(json.dumps(el, sort_keys=True).encode("utf-8"))
        return m.hexdigest()
