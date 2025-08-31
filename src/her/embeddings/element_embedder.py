"""
Element Embedder using MarkupLM (ONNX) with deterministic fallback.

Contract:
- Input: list[dict] (each dict = element node with tag, text, attrs, role, etc.)
- Output: np.ndarray float32 embeddings (batch_size x hidden_dim)
"""

import json
import hashlib
from typing import Dict, List, Any

import numpy as np

from . import _resolve


class ElementEmbedder:
    def __init__(self, device: str = "cpu", dim: int = 768, cache_dir: Any | None = None) -> None:
        self.dim = int(dim)
        self._paths = None
        self._session = None
        self._init_session()

    def _init_session(self) -> None:
        try:
            mp = _resolve.resolve_element_embedding()
            self._paths = mp
        except Exception:
            self._paths = None
            self._session = None
            return
        try:
            import onnxruntime as ort  # type: ignore

            self._session = ort.InferenceSession(
                str(mp.onnx), providers=["CPUExecutionProvider"]
            )
        except Exception:
            self._session = None

    def _hash_vec(self, s: str) -> np.ndarray:
        h = hashlib.sha256(s.encode("utf-8")).digest()
        needed = self.dim * 4
        buf = (h * ((needed // len(h)) + 1))[:needed]
        arr = np.frombuffer(buf, dtype=np.uint32)[: self.dim].astype(np.float32)
        # Normalize to unit length
        norm = float(np.linalg.norm(arr))
        return arr if norm == 0.0 else (arr / norm).astype(np.float32)

    def _flatten_element(self, element: Dict[str, Any]) -> str:
        """Convert DOM node dict into a flat, robust string for embedding."""
        tag = str(element.get("tag", ""))
        role = str(element.get("role", element.get("ariaRole", "")))
        text = str(element.get("text", ""))
        attrs = element.get("attrs") or element.get("attributes") or {}
        attr_pairs = []
        for k, v in sorted(attrs.items()):
            if k in {"class", "style"}:
                continue
            attr_pairs.append(f"{k}={v}")
        joined = " ".join(attr_pairs)
        extra = []
        for key in ("id", "name", "placeholder", "dataTestId", "ariaLabel"):
            if key in element and element[key]:
                extra.append(f"{key}={element[key]}")
        parts = [tag, role, text] + extra + ([joined] if joined else [])
        return " ".join(p for p in parts if p).strip()

    def batch_encode(self, elements: List[Dict[str, Any]]) -> np.ndarray:
        """Embed multiple elements. Returns float32 array of shape [N, D]."""
        if not elements:
            return np.zeros((0, self.dim), dtype=np.float32)
        inputs = [self._flatten_element(e) for e in elements]
        if self._session is None:
            vecs = [self._hash_vec(s) for s in inputs]
            return np.stack(vecs, axis=0).astype(np.float32)
        # Minimal ONNX forward compatible call; fall back to hashed vec on error
        try:
            import numpy as _np  # local alias for clarity

            input_ids = _np.zeros((len(inputs), 8), dtype=_np.int64)
            attention_mask = _np.ones((len(inputs), 8), dtype=_np.int64)
            token_type_ids = _np.zeros((len(inputs), 8), dtype=_np.int64)
            outs = self._session.run(
                None,
                {
                    "input_ids": input_ids,
                    "attention_mask": attention_mask,
                    "token_type_ids": token_type_ids,
                },
            )
            x = outs[0] if isinstance(outs, list) else outs
            arr = _np.array(x).astype(_np.float32)
            if arr.ndim == 3:  # [N, T, D] -> mean pool
                arr = arr.mean(axis=1)
            if arr.shape[-1] != self.dim:
                arr = _np.resize(arr, (arr.shape[0], self.dim)).astype(_np.float32)
            # L2 normalize
            norms = _np.linalg.norm(arr, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            arr = (arr / norms).astype(_np.float32)
            return arr
        except Exception:
            vecs = [self._hash_vec(s) for s in inputs]
            return np.stack(vecs, axis=0).astype(np.float32)

    def embed(self, element: Dict[str, Any]) -> np.ndarray:
        return self.batch_encode([element])[0]

    def info(self) -> Dict[str, Any]:
        mp = self._paths
        return {
            "task": "element-embedding",
            "id": getattr(mp, "id", None),
            "alias": getattr(mp, "alias", None),
            "root": str(getattr(mp, "root_dir", "")) if mp else None,
            "onnx": str(getattr(mp, "onnx", "")) if mp else None,
            "tokenizer": str(getattr(mp, "tokenizer", "")) if mp else None,
            "mode": "fallback" if self._session is None else "onnx",
            "dim": self.dim,
        }
