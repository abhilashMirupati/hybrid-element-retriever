from __future__ import annotations
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np

from her.embeddings import _resolve
from her.embeddings.text_embedder import TextEmbedder
from her.embeddings.element_embedder import ElementEmbedder  # deterministic fallback (kept for dev)
try:
    from her.embeddings.markuplm_embedder import MarkupLMEmbedder
except Exception:
    MarkupLMEmbedder = None  # transformers may be optional in some envs


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
    - Text: MiniLM/E5 ONNX (local, offline)
    - Elements: MarkupLM (Transformers, local) when available; dev fallback is deterministic
    """

    def __init__(self, models_root: Optional[Path] = None) -> None:
        # Resolve models root via resolver (env-aware) if not provided.
        self._models_root = models_root or Path(_resolve._models_root_from_env())

        # ---- Text embedder (MiniLM/E5 ONNX) ----
        try:
            txt_res = _resolve.resolve_text_embedding(self._models_root)
            self.text_embedder = TextEmbedder(
                model_root=str(txt_res["model_dir"]),
                normalize=True,
                max_length=512,
                batch_size=32,
            )
            log.info("Text embedder: MiniLM/E5 ONNX @ %s", txt_res["model_dir"])
        except Exception as e:
            log.warning("Text embedder unavailable (%s). Falling back to zero-vector.", e)
            self.text_embedder = None  # will produce zero vectors

        # ---- Element embedder (MarkupLM Transformers preferred) ----
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
            elif elem_res.framework == "onnx":
                # If you later add an ONNX element embedder, wire it here.
                log.warning("Element ONNX path found (%s) but ONNX element embedder is not implemented; "
                            "falling back to deterministic embedder.", elem_res.onnx)
                self.element_embedder = ElementEmbedder()
            else:
                raise _resolve.ResolverError(f"Unsupported framework: {elem_res.framework}")
        except Exception as e:
            log.warning("Element embedder unavailable (%s). Falling back to deterministic embedder.", e)
            self.element_embedder = ElementEmbedder()

        # Hard error only if both are missing (fully stubbed path).
        if self.text_embedder is None and isinstance(self.element_embedder, ElementEmbedder):
            raise RuntimeError(
                "Both text and element embedders are unavailable. "
                "Install models via scripts/install_models.ps1 or ./scripts/install_models.sh."
            )

    # ---- Public API ----

    def embed_query(self, query: str) -> np.ndarray:
        if not query or self.text_embedder is None:
            # zero vector fallback
            return np.zeros((self._text_dim(),), dtype=np.float32)
        return self.text_embedder.batch_encode([query])[0]

    def embed_elements(self, elements: List[Dict[str, Any]]) -> np.ndarray:
        if not elements:
            return np.zeros((0, self._elem_dim()), dtype=np.float32)

        if hasattr(self.element_embedder, "batch_encode"):
            vecs = self.element_embedder.batch_encode(elements)
        else:
            # deterministic fallback has encode() only
            vecs = np.vstack([self.element_embedder.encode(el) for el in elements]).astype(np.float32, copy=False)

        # Ensure float32 and correct shape
        vecs = vecs.astype(np.float32, copy=False)
        if vecs.ndim != 2 or vecs.shape[1] != self._elem_dim():
            # If fallback dimension differs, zero-pad or truncate safely.
            dim = self._elem_dim()
            fixed = np.zeros((vecs.shape[0], dim), dtype=np.float32)
            k = min(dim, vecs.shape[1])
            fixed[:, :k] = vecs[:, :k]
            vecs = fixed
        return vecs

    def query(self, query: str, elements: List[Dict[str, Any]], top_k: int = 10) -> Dict[str, Any]:
        """
        Returns ranked elements by cosine similarity to the query.
        Each item: {index, score, element}
        """
        q = self.embed_query(query)              # (D,)
        E = self.embed_elements(elements)        # (N, H)
        if E.size == 0:
            return {"results": [], "strategy": "cosine", "confidence": 0.0}

        # Cosine vs each element
        scores = np.array([_cos(q, E[i]) for i in range(E.shape[0])], dtype=np.float32)
        order = np.argsort(-scores)
        top_k = max(1, min(top_k, len(order)))
        ranked = [{"index": int(i), "score": float(scores[i]), "element": elements[int(i)]} for i in order[:top_k]]

        conf = float(np.clip(np.max(scores) if len(scores) else 0.0, 0.0, 1.0))
        return {"results": ranked, "strategy": "cosine", "confidence": conf}

    # ---- helpers ----

    def _text_dim(self) -> int:
        # Prefer real dim from text embedder if available
        if self.text_embedder is not None and hasattr(self.text_embedder, "dim"):
            return int(self.text_embedder.dim)
        # fallback conservative dimension when zero-vectoring
        return 384

    def _elem_dim(self) -> int:
        if self.element_embedder is not None and hasattr(self.element_embedder, "dim"):
            return int(self.element_embedder.dim)
        # deterministic fallback often smaller; keep a safe default
        return 768
