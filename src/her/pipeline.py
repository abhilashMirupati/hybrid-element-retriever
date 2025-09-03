from __future__ import annotations
import logging
import re
import math
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np

from her.embeddings import _resolve
try:
    from her.embeddings.text_embedder import TextEmbedder
except Exception:
    TextEmbedder = None
from her.embeddings.element_embedder import ElementEmbedder  # deterministic fallback
try:
    from her.embeddings.markuplm_embedder import MarkupLMEmbedder
except Exception:
    MarkupLMEmbedder = None  # transformers may be optional

log = logging.getLogger(__name__)


def _cos(a: np.ndarray, b: np.ndarray) -> float:
    """Stable cosine similarity: L2-normalize and dot over shared dimension (no resize/repeat)."""
    a = a.astype(np.float32, copy=False)
    b = b.astype(np.float32, copy=False)
    na = float(np.linalg.norm(a))
    nb = float(np.linalg.norm(b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    a = a / na
    b = b / nb
    d = min(a.shape[0], b.shape[0])
    if d == 0:
        return 0.0
    return float(np.dot(a[:d], b[:d]))


class HybridPipeline:
    """
    High-level pipeline that embeds a query (text) and page elements, then computes similarities.
    """

    def __init__(self, models_root: Optional[Path] = None) -> None:
        self._models_root = models_root or Path(_resolve._models_root_from_env())

        # ---- Text embedder (MiniLM/E5 ONNX) ----
        try:
            if TextEmbedder is not None:
                txt_res = _resolve.resolve_text_embedding(self._models_root)
                self.text_embedder = TextEmbedder(
                    model_root=str(txt_res["model_dir"]),
                    normalize=True,
                    max_length=512,
                    batch_size=32,
                )
                log.info("Text embedder: MiniLM/E5 ONNX @ %s", txt_res["model_dir"])
            else:
                raise RuntimeError("TextEmbedder unavailable")
        except Exception as e:
            log.warning("Text embedder unavailable (%s). Falling back to zero-vector.", e)
            self.text_embedder = None

        # ---- Element embedder ----
        self.element_embedder = None
        try:
            elem_res = _resolve.resolve_element_embedding()
            if elem_res.framework == "transformers" and MarkupLMEmbedder is not None:
                self.element_embedder = MarkupLMEmbedder(
                    model_dir=str(elem_res.model_dir),
                    device="cpu",
                    batch_size=16,
                    normalize=True,
                )
                log.info("Element embedder: MarkupLM (Transformers) @ %s", elem_res.model_dir)
            else:
                self.element_embedder = ElementEmbedder()
        except Exception as e:
            log.warning("Element embedder unavailable (%s). Falling back to deterministic embedder.", e)
            self.element_embedder = ElementEmbedder()

    # ---- Public API ----

    def embed_query(self, query: str) -> np.ndarray:
        if not query or self.text_embedder is None:
            return np.zeros((self._text_dim(),), dtype=np.float32)
        return self.text_embedder.encode(query)

    def embed_elements(self, elements: List[Dict[str, Any]]) -> np.ndarray:
        if not elements:
            return np.zeros((0, self._elem_dim()), dtype=np.float32)
        if hasattr(self.element_embedder, "batch_encode"):
            vecs = self.element_embedder.batch_encode(elements)
        else:
            vecs = np.vstack([self.element_embedder.encode(el) for el in elements]).astype(np.float32, copy=False)
        vecs = vecs.astype(np.float32, copy=False)
        if vecs.ndim != 2:
            dim = self._elem_dim()
            fixed = np.zeros((vecs.shape[0], dim), dtype=np.float32)
            k = min(dim, vecs.shape[1])
            fixed[:, :k] = vecs[:, :k]
            vecs = fixed
        return vecs

    def query(self, query: str, elements: List[Dict[str, Any]], top_k: int = 10) -> Dict[str, Any]:
        """
        Returns ranked elements by cosine similarity plus hybrid bonuses and tie-breaks.
        Each result includes: {index, score, confidence, reason, element}
        """
        q = self.embed_query(query)
        E = self.embed_elements(elements)
        if E.size == 0:
            return {"results": [], "strategy": "hybrid", "confidence": 0.0}

        # Base cosine scores
        base_scores = np.array([_cos(q, E[i]) for i in range(E.shape[0])], dtype=np.float32)

        # Bonuses
        def _tag_bias(tag): return 0.02 if tag == "button" else 0.015 if tag == "a" else 0.01 if tag == "input" else 0.0
        def _role_bonus(role): return 0.02 if role in ("button", "link", "menuitem", "tab", "checkbox", "radio") else 0.0
        def _href_bonus(href, qtokens): return 0.02 if href and any(t in href.lower() for t in qtokens) else 0.0

        qtokens = [t for t in re.split(r"[^a-z0-9]+", query.lower()) if len(t) >= 3]
        bonuses, reasons = np.zeros_like(base_scores), [[] for _ in elements]

        for i, el in enumerate(elements):
            tag, role, href = (el.get("tag") or "").lower(), (el.get("role") or "").lower(), el.get("href", "")
            tb, rb, hb = _tag_bias(tag), _role_bonus(role), _href_bonus(href, qtokens)
            bonuses[i] = tb + rb + hb
            reasons[i].append(f"cosine={base_scores[i]:.3f}")
            if tb: reasons[i].append(f"+tag[{tag}]=+{tb:.3f}")
            if rb: reasons[i].append(f"+role[{role}]=+{rb:.3f}")
            if hb: reasons[i].append(f"+href-match=+{hb:.3f}")

        scores = np.clip(base_scores + bonuses, 0.0, 1.0)

        # Tie-breakers
        def _vis(el): return bool(el.get("visible"))
        def _area(el): 
            b = el.get("bbox") or {}; return (b.get("width") or 0) * (b.get("height") or 0)
        def _depth(el): xp = el.get("xpath") or ""; return xp.count("/") if xp else 9999
        def _interactive(el): return 0 if el.get("tag") == "button" or el.get("role") == "button" else 1

        order = list(np.argsort(-scores))
        order.sort(key=lambda i: (-scores[i], 0 if _vis(elements[i]) else 1, _depth(elements[i]), -_area(elements[i]), _interactive(elements[i])))

        # Dedup near-identical
        seen, deduped = [], []
        for i in order:
            if not any(_cos(E[i], E[j]) > 0.995 for j in seen):
                seen.append(i); deduped.append(i)

        top_idxs = deduped[:max(1, min(top_k, len(deduped)))]
        conf = 1.0 / (1.0 + math.exp(-(float(scores[top_idxs[0]]) - 0.7) * 6)) if top_idxs else 0.0

        results = []
        for rank, i in enumerate(top_idxs):
            results.append({
                "index": i,
                "score": float(scores[i]),
                "confidence": conf if rank == 0 else max(0.0, conf - 0.05 * rank),
                "reason": "; ".join(reasons[i]),
                "element": elements[i],
            })
        return {"results": results, "strategy": "hybrid", "confidence": conf}

    def _text_dim(self) -> int: return getattr(self.text_embedder, "dim", 384) or 384
    def _elem_dim(self) -> int: return getattr(self.element_embedder, "dim", 768) or 768
