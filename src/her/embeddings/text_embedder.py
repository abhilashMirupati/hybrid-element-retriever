from __future__ import annotations
import logging
from pathlib import Path
from threading import Lock
from typing import List, Optional

import numpy as np
import onnxruntime as ort
from transformers import AutoTokenizer

logger = logging.getLogger(__name__)


def _l2norm(a: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    n = np.linalg.norm(a, axis=-1, keepdims=True)
    n = np.maximum(n, eps)
    return a / n


class TextEmbedder:
    """
    Text embedder for queries/passages using local ONNX MiniLM/E5 model.

    Expects directory: src/her/models/e5-small-onnx/ with:
      - model.onnx (preferred) or other variants
      - tokenizer files loadable by AutoTokenizer (tokenizer.json/vocab.txt etc.)

    Accuracy & robustness:
      - Single shared ORT session (perf + stability)
      - Batch encoding (float32)
      - Optional L2 normalization (good for cosine sim)
      - Robust model file selection among common variants
    """

    _shared_session: Optional[ort.InferenceSession] = None
    _session_lock = Lock()

    def __init__(
        self,
        model_root: str = "src/her/models/e5-small-onnx",
        normalize: bool = True,
        max_length: int = 512,
        batch_size: int = 32,
    ):
        self.model_dir = Path(model_root)
        self.normalize = bool(normalize)
        self.max_length = int(max_length)
        self.batch_size = int(batch_size)

        # Pick the best-available ONNX file.
        candidates = [
            "model.onnx",
            "model_fp16.onnx",
            "model_q4.onnx",
            "model_bnb4.onnx",
            "model_int8.onnx",
            "model_uint8.onnx",
            "model_quantized.onnx",
            "model_int8_quantized.onnx",
            "model_quantized_fixed.onnx",
        ]
        chosen = None
        for c in candidates:
            p = self.model_dir / c
            if p.is_file():
                chosen = p
                break
        if chosen is None:
            raise FileNotFoundError(
                f"Could not find ONNX model in {self.model_dir}. "
                f"Expected one of: {', '.join(candidates)}"
            )
        self.model_path = chosen

        # Local tokenizer (no network).
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_dir, use_fast=True)

        # Create (or reuse) ONNX session and infer dimension.
        self._session = self._get_session()
        self.dim = self._infer_dim()

        logger.info(
            "Loaded MiniLM/E5 ONNX dim=%d normalize=%s model=%s",
            self.dim, self.normalize, self.model_path
        )

    def _get_session(self) -> ort.InferenceSession:
        if TextEmbedder._shared_session is None:
            with TextEmbedder._session_lock:
                if TextEmbedder._shared_session is None:
                    so = ort.SessionOptions()
                    TextEmbedder._shared_session = ort.InferenceSession(
                        str(self.model_path),
                        sess_options=so,
                        providers=["CPUExecutionProvider"],
                    )
        return TextEmbedder._shared_session

    def _infer_dim(self) -> int:
        toks = self.tokenizer(
            ["dummy"], padding=True, truncation=True, max_length=8, return_tensors="np"
        )
        inputs = {k: v.astype(np.int64) for k, v in toks.items()}
        out = self._session.run(None, inputs)[0]
        if out.ndim == 3:
            out = out[:, 0, :]
        return int(out.shape[-1])

    def encode_one(self, text: str) -> np.ndarray:
        return self.batch_encode_texts([text])[0]

    def batch_encode_texts(self, texts: List[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dim), dtype=np.float32)

        out = np.zeros((len(texts), self.dim), dtype=np.float32)
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            toks = self.tokenizer(
                batch, padding=True, truncation=True, max_length=self.max_length, return_tensors="np"
            )
            # ORT requires int64
            inputs = {k: v.astype(np.int64) for k, v in toks.items()}
            ort_out = self._session.run(None, inputs)[0]  # (B, D) or (B, T, D)
            if ort_out.ndim == 3:
                ort_out = ort_out[:, 0, :]
            vecs = ort_out.astype(np.float32, copy=False)
            if self.normalize:
                vecs = _l2norm(vecs)
            out[i:i + len(batch)] = vecs
        return out

    # ----- Compatibility shim for older pipeline code -----
    def batch_encode(self, texts: List[str]) -> np.ndarray:
        """Back-compat: some callers expect .batch_encode()."""
        return self.batch_encode_texts(texts)
