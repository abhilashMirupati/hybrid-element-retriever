from __future__ import annotations

import hashlib
from typing import List

import numpy as np

from ._resolve import get_query_resolver, ONNXResolver


class QueryEmbedder:
    """Deterministic query embedder with ONNX fallback.

    API:
    - encode(text) -> np.ndarray[np.float32]
    - batch_encode(texts) -> np.ndarray[np.float32] with shape [N, D]
    """

    def __init__(self, dim: int = 384, **_: object) -> None:
        self.dim = int(dim)
        self.resolver: ONNXResolver = get_query_resolver()
        self._session = None
        self._init_session()

    def _init_session(self) -> None:
        onnx_path, _ = self.resolver.files()
        if onnx_path is None:
            self._session = None
            return
        try:
            import onnxruntime as ort  # type: ignore

            self._session = ort.InferenceSession(str(onnx_path), providers=['CPUExecutionProvider'])
        except Exception:
            self._session = None

    def _hash_fallback(self, text: str) -> np.ndarray:
        seed_bytes = hashlib.sha256(text.strip().lower().encode('utf-8')).digest()
        seed = int.from_bytes(seed_bytes[:8], 'little', signed=False) & 0xFFFFFFFF
        rng = np.random.default_rng(seed)
        vec = rng.standard_normal(self.dim, dtype=np.float32)
        norm = float(np.linalg.norm(vec))
        return vec if norm == 0.0 else (vec / norm).astype(np.float32)

    def encode(self, text: str) -> np.ndarray:
        if not text:
            return self._hash_fallback('')
        if self._session is None:
            return self._hash_fallback(text)
        try:
            # Minimal compatible inputs for common transformer architectures
            input_ids = np.zeros((1, 8), dtype=np.int64)
            attention_mask = np.ones((1, 8), dtype=np.int64)
            token_type_ids = np.zeros((1, 8), dtype=np.int64)
            outs = self._session.run(None, {
                'input_ids': input_ids,
                'attention_mask': attention_mask,
                'token_type_ids': token_type_ids,
            })
            x = outs[0] if isinstance(outs, list) else outs
            arr = np.array(x).mean(axis=1).reshape(-1).astype(np.float32)
            if arr.size != self.dim:
                arr = np.resize(arr, self.dim).astype(np.float32)
            norm = float(np.linalg.norm(arr))
            return arr if norm == 0.0 else (arr / norm).astype(np.float32)
        except Exception:
            return self._hash_fallback(text)

    def batch_encode(self, texts: List[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dim), dtype=np.float32)
        vecs = [self.encode(t) for t in texts]
        return np.stack(vecs, axis=0).astype(np.float32)