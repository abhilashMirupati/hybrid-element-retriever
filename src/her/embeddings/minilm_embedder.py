from __future__ import annotations
from typing import List, Dict, Any
import numpy as np

from her.embeddings import _resolve
try:
    from her.embeddings.text_embedder import TextEmbedder
except Exception:
    TextEmbedder = None  # type: ignore


class MiniLMEmbedder:
    """
    Compatibility shim for legacy imports.
    Provides .embed_query(str) and .embed_element(dict) returning 384-d vectors.
    Uses local ONNX TextEmbedder if available; otherwise returns zero-vectors.
    """
    def __init__(self) -> None:
        self.dim = 384
        self._text = None
        try:
            if TextEmbedder is None:
                raise RuntimeError("TextEmbedder unavailable")
            res = _resolve.resolve_text_embedding(_resolve._models_root_from_env())
            self._text = TextEmbedder(
                model_root=str(res["model_dir"]),
                normalize=True,
                max_length=512,
                batch_size=32,
            )
        except Exception:
            self._text = None

    def _zeros(self) -> np.ndarray:
        return np.zeros((self.dim,), dtype=np.float32)

    def embed_query(self, q: str) -> np.ndarray:
        if not q or self._text is None:
            return self._zeros()
        v = self._text.encode(q)
        return v.astype(np.float32, copy=False)

    def embed_element(self, el: Dict[str, Any]) -> np.ndarray:
        # Project element to text for a fast semantic vector
        if self._text is None:
            return self._zeros()
        parts: List[str] = []
        attrs = (el.get("attrs") or {})
        if el.get("text"): parts.append(str(el.get("text")))
        for k in ("aria-label","title","alt","placeholder","name","value","role","type"):
            v = attrs.get(k)
            if v: parts.append(f"{k}:{v}")
        txt = " ".join(parts).strip()
        if not txt:
            return self._zeros()
        v = self._text.encode(txt)
        return v.astype(np.float32, copy=False)

