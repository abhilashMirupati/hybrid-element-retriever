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
    TextEmbedder = None  # type: ignore
from her.embeddings.element_embedder import ElementEmbedder
try:
    from her.embeddings.markuplm_embedder import MarkupLMEmbedder
except Exception:
    MarkupLMEmbedder = None  # type: ignore

log = logging.getLogger(__name__)


def _cos(a: np.ndarray, b: np.ndarray) -> float:
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
    High-level pipeline: embed query & elements, compute cosine similarity,
    apply hybrid bonuses, deterministic tie-breakers, dedup, and confidence.
    Offline-friendly with optional heavy deps.
    """

    def __init__(self, models_root: Optional[Path] = None) -> None:
        self._models_root = models_root or Path(_resolve._models_root_from_env())

        # Text embedder (optional)
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

        # Element embedder (MarkupLM if present, else deterministic)
        self.element_embedder = None
        try:
            elem_res = _resolve.resolve_element_embedding()
            if getattr(elem_res, "framework", None) == "transformers" and MarkupLMEmbedder is not None:
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

    def embed_query(self, query: str) -> np.ndarray:
        if not query or self.text_embedder is None:
            return np.zeros((self._text_dim(),), dtype=np.float32)
        vec = self.text_embedder.encode(query)
        return vec.astype(np.float32, copy=False)

    def embed_elements(self, elements: List[Dict[str, Any]]) -> np.ndarray:
        if not elements:
            return np.zeros((0, self._elem_dim()), dtype=np.float32)

        if hasattr(self.element_embedder, "batch_encode"):
            vecs = self.element_embedder.batch_encode(elements)
        else:
            vecs = np.vstack([self.element_embedder.encode(el) for el in elements])

        vecs = vecs.astype(np.float32, copy=False)
        if vecs.ndim != 2:
            dim = self._elem_dim()
            fixed = np.zeros((vecs.shape[0], dim), dtype=np.float32)
            if vecs.ndim == 1:
                # single vector — broadcast to one row
                fixed[0, : min(dim, vecs.shape[0])] = vecs[: min(dim, vecs.shape[0])]
            else:
                k = min(dim, vecs.shape[1])
                if k:
                    fixed[:, :k] = vecs[:, :k]
            vecs = fixed
        return vecs

    def query(self, query: str, elements: List[Dict[str, Any]], top_k: int = 10) -> Dict[str, Any]:
        q = self.embed_query(query)
        E = self.embed_elements(elements)
        if E.size == 0:
            return {"results": [], "strategy": "hybrid", "confidence": 0.0}

        base_scores = np.array([_cos(q, E[i]) for i in range(E.shape[0])], dtype=np.float32)

        def _tag_bias(tag: str) -> float:
            tag = (tag or "").lower()
            if tag == "button": return 0.02
            if tag == "a":      return 0.015
            if tag == "input":  return 0.01
            return 0.0

        def _role_bonus(role: str) -> float:
            role = (role or "").lower()
            if role in ("button", "link", "menuitem", "tab", "checkbox", "radio"):
                return 0.02
            return 0.0

        def _href_bonus(href: str, qtokens: List[str]) -> float:
            if not href:
                return 0.0
            href_l = href.lower()
            for t in qtokens:
                if t and t in href_l:
                    return 0.02
            return 0.0

        qtokens = [t for t in re.split(r"[^a-z0-9]+", (query or "").lower()) if t and len(t) >= 3]

        bonuses = np.zeros_like(base_scores, dtype=np.float32)
        reasons: List[List[str]] = [[] for _ in range(len(elements))]

        for i, el in enumerate(elements):
            tag = (el.get("tag") or (el.get("attrs", {}) or {}).get("tag") or "").lower()
            role = (el.get("role") or (el.get("attrs", {}) or {}).get("role") or "").lower()
            href = el.get("href") or (el.get("attrs", {}) or {}).get("href") or ""

            tb = _tag_bias(tag)
            rb = _role_bonus(role)
            hb = _href_bonus(href, qtokens)

            bonuses[i] = tb + rb + hb
            reasons[i].append(f"cosine={base_scores[i]:.3f}")
            if tb: reasons[i].append(f"+tag[{tag}]=+{tb:.3f}")
            if rb: reasons[i].append(f"+role[{role}]=+{rb:.3f}")
            if hb: reasons[i].append(f"+href-match=+{hb:.3f}")

        scores = np.clip(base_scores + bonuses, 0.0, 1.0)

        def _vis(el: Dict[str, Any]) -> bool:
            v = el.get("visible")
            if isinstance(v, bool):
                return v
            return str(v).lower() == "true"

        def _area(el: Dict[str, Any]) -> float:
            bbox = el.get("bbox") or {}
            try:
                return float((bbox.get("width") or 0.0) * (bbox.get("height") or 0.0))
            except Exception:
                return 0.0

        def _depth_from_xpath(el: Dict[str, Any]) -> int:
            xp = el.get("xpath") or el.get("abs_xpath") or el.get("absolute_xpath") or ""
            if not isinstance(xp, str) or not xp:
                return 9999
            return max(1, xp.count("/"))

        def _interactive_rank(el: Dict[str, Any]) -> int:
            tag = (el.get("tag") or "").lower()
            role = (el.get("role") or "").lower()
            tabindex = str(el.get("tabindex") or "").strip()
            if tag == "button" or role == "button":
                return 0
            if tag in ("a", "input") or role in ("link", "checkbox", "radio", "menuitem", "tab"):
                return 1
            if tabindex and tabindex.isdigit() and int(tabindex) >= 0:
                return 1
            return 2

        order = list(np.argsort(-scores))

        def _key(i: int):
            el = elements[int(i)]
            return (
                -float(scores[int(i)]),
                0 if _vis(el) else 1,
                _depth_from_xpath(el),
                -_area(el),
                _interactive_rank(el),
            )

        order.sort(key=_key)

        seen: List[int] = []
        deduped: List[int] = []
        for i in order:
            keep = True
            for j in list(seen):
                if _cos(E[int(i)], E[int(j)]) > 0.995:
                    if _key(i) < _key(j):
                        seen.remove(j)
                        seen.append(i)
                        if j in deduped:
                            deduped.remove(j)
                            deduped.append(i)
                    keep = False
                    break
            if keep:
                seen.append(i)
                deduped.append(i)

        top_k = max(1, min(top_k, len(deduped)))
        top_idxs = deduped[:top_k]

        def _sigmoid(x: float) -> float:
            return 1.0 / (1.0 + math.exp(-x))

        max_score = float(scores[top_idxs[0]]) if top_idxs else 0.0
        confidence = float(np.clip(_sigmoid((max_score - 0.7) * 6.0), 0.0, 1.0))

        results: List[Dict[str, Any]] = []
        for rank_pos, i in enumerate(top_idxs):
            i = int(i)
            reason = "; ".join(reasons[i]) if reasons[i] else f"cosine={base_scores[i]:.3f}"
            results.append({
                "index": i,
                "score": float(scores[i]),
                "confidence": confidence if rank_pos == 0 else max(0.0, confidence - 0.05 * rank_pos),
                "reason": reason,
                "element": elements[i],
            })

        return {"results": results, "strategy": "hybrid", "confidence": confidence}

    def _text_dim(self) -> int:
        dim = getattr(self.text_embedder, "dim", None)
        return int(dim) if isinstance(dim, (int, float)) and dim else 384

    def _elem_dim(self) -> int:
        dim = getattr(self.element_embedder, "dim", None)
        return int(dim) if isinstance(dim, (int, float)) and dim else 768
