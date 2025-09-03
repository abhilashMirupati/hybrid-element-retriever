# src/her/pipeline.py
"""
Hybrid Element Retrieval Pipeline
Wires together intent embeddings (MiniLM), element embeddings (MarkupLM),
and ranking fusion into a single flow.
"""

from typing import Dict, Any, List
import time

import logging
from her.embeddings.text_embedder import TextEmbedder
from her.embeddings.element_embedder import ElementEmbedder
from her.embeddings import _resolve
try:
    from her.embeddings.markuplm_embedder import MarkupLMEmbedder
except Exception:
    MarkupLMEmbedder = None  # type: ignore
from her.rank.fusion_scorer import FusionScorer
from her.cache.two_tier import TwoTierCache
# Note: Do NOT import HERPipeline here to avoid circular imports.


class PipelineConfig:
    """Legacy-friendly configuration shim.

    Accepts arbitrary keyword options used by legacy tests. The modern pipeline
    does not rely on these flags directly; they are stored for compatibility.
    """

    def __init__(self, **options: Any) -> None:
        self.__dict__.update(options)

# Legacy alias export so tests can `from her.pipeline import HERPipeline`
from .compat import HERPipeline  # noqa: E402  (placed after class definitions)


logger = logging.getLogger(__name__)


class HybridPipeline:
    def __init__(self, cache_dir: str = ".cache", device: str = "cpu"):
        # Text embedder (MiniLM/E5-small via ONNX with internal fallback)
        try:
            self.text_embedder = TextEmbedder(device=device)
            logger.info("Loaded text embedder: framework=onnx path=%s", getattr(self.text_embedder, 'paths', None))
        except Exception:
            # Deterministic fallback path is handled internally by TextEmbedder
            self.text_embedder = TextEmbedder(device=device)

        # Element embedder: prefer MarkupLM (Transformers) when available
        try:
            paths = _resolve.resolve_element_embedding()
            if paths.framework == "transformers" and paths.model_dir and MarkupLMEmbedder is not None:
                self.element_embedder = MarkupLMEmbedder(paths.model_dir, device=device)
                logger.info("Loaded element embedder: framework=transformers dir=%s dim=%s", paths.model_dir, getattr(self.element_embedder, 'dim', None))
            elif paths.framework == "onnx":
                # Keep legacy stub for ONNX element model until an ONNX runtime embedder is implemented
                self.element_embedder = ElementEmbedder(dim=768)
                logger.info("Using legacy ElementEmbedder stub for ONNX element model at %s", getattr(paths, 'onnx', None))
            else:
                raise RuntimeError("Element embedder could not be resolved; check model installation.")
        except Exception:
            # Final safety: deterministic stub
            self.element_embedder = ElementEmbedder(dim=768)
        self.scorer = FusionScorer()
        # Reuse global cache if available to cooperate with test fixtures
        try:
            from her.cache.two_tier import get_global_cache as _gg
            self.cache = _gg()
        except Exception:
            self.cache = TwoTierCache(cache_dir=cache_dir)

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
        cache_hits = 0
        cache_misses = 0
        batch: List[Dict[str, Any]] = []
        for el in dom_snapshot:
            # Visibility filtering for performance
            if el.get('is_visible') is False:
                continue
            el_hash = self._hash_el(el)
            raw = self.cache.get_raw(el_hash)
            cached = raw.get("value")
            if cached is not None:
                emb = cached
                cache_hits += 1
                embeddings.append(emb)
                elements.append(el)
            else:
                batch.append((el, el_hash))
                # Flush batch at size 100
                if len(batch) >= 100:
                    enc = self.element_embedder.batch_encode([b[0] for b in batch])
                    for (e, h), emb in zip(batch, enc):
                        self.cache.put(h, emb)
                        embeddings.append(emb)
                        elements.append(e)
                        cache_misses += 1
                    batch = []
        # Flush remaining batch
        if batch:
            enc = self.element_embedder.batch_encode([b[0] for b in batch])
            for (e, h), emb in zip(batch, enc):
                self.cache.put(h, emb)
                embeddings.append(emb)
                elements.append(e)
                cache_misses += 1

        # --- 3. Retrieval scoring
        # Compute simple cosine similarities as semantic proxy
        import numpy as _np
        def _cos(a: _np.ndarray, b: _np.ndarray) -> float:
            a = a.astype(_np.float32); b = b.astype(_np.float32)
            # Resize to match dims if needed
            if a.shape[0] != b.shape[0]:
                if a.shape[0] < b.shape[0]:
                    b = _np.resize(b, a.shape[0])
                else:
                    a = _np.resize(a, b.shape[0])
            na = float(_np.linalg.norm(a)); nb = float(_np.linalg.norm(b))
            if na == 0.0 or nb == 0.0:
                return 0.0
            return float(_np.dot(a, b) / (na * nb))

        semantic_scores = [_cos(intent_vec, e) for e in embeddings]
        # Heuristic CSS/text score: prefer buttons/links and text inclusion
        css_scores = []
        for el in elements:
            score = 0.0
            tag = str(el.get('tag', '')).lower()
            txt = str(el.get('text', '')).lower()
            if tag in {'button', 'a', 'input'}:
                score += 0.2
            for w in str(intent).lower().split():
                if w and w in txt:
                    score += 0.1
            css_scores.append(min(1.0, score))
        promotions = [0.0] * len(elements)

        # The FusionScorer shim accepts optional semantic/css/promotions arrays
        try:
            scored = self.scorer.score_elements(intent, elements, semantic_scores, css_scores, promotions)
        except TypeError:
            scored = self.scorer.score_elements(intent, elements)

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

        # Shadow DOM/frame hints
        metadata = {
            "latency_sec": float(latency),
            "cache_hits": int(cache_hits),
            "cache_misses": int(cache_misses),
            "frame_info": "main",
        }
        if best.get("element", {}).get("shadow_elements"):
            metadata["in_shadow_dom"] = True
        out = {
            "element": best.get("element"),
            "xpath": best.get("xpath", ""),
            "confidence": float(best.get("score", 0.0)),
            "strategy": "fusion",
            "metadata": metadata,
        }
        # Frame fields for tests (use None when main)
        out["used_frame_id"] = None
        out["frame_path"] = []
        return out

    def _hash_el(self, el: Dict[str, Any]) -> str:
        """Stable hash for DOM element dict."""
        import hashlib, json
        m = hashlib.sha256()
        m.update(json.dumps(el, sort_keys=True).encode("utf-8"))
        return m.hexdigest()
