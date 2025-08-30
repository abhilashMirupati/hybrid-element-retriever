"""
HER Text Embedding (MiniLM/E5-small ONNX).

Responsibilities
----------------
- Load the E5-small ONNX model from resolved paths.
- Provide a clean API:
    - batch_encode(list[str]) -> np.ndarray (float32, shape [N, D])
    - encode_one(str) -> np.ndarray (float32, shape [D])
- Deterministic hash fallback for robustness (e.g., if files missing or empty).
- Ensure thread-safety and efficiency for repeated calls.

Notes
-----
- Depends on: _resolve.resolve_text_embedding()
- Model files: model.onnx + tokenizer.json
- External deps: onnxruntime, transformers (tokenizer only)
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import List, Optional
import numpy as np

from . import _resolve


class TextEmbedder:
    """MiniLM / E5-small ONNX embedder (sentence-transformers)."""

    def __init__(self, session: Optional[object] = None):
        mp = _resolve.resolve_text_embedding()
        self.paths = mp

        if not mp.exists():
            # Fallback: deterministic hashing
            self.session = None
            self.tokenizer = None
            return

        # Try to load ONNX/Tokenizer, but allow fallback if unavailable
        try:
            from transformers import AutoTokenizer  # type: ignore
            import onnxruntime as ort  # type: ignore
            self.tokenizer = AutoTokenizer.from_pretrained(str(mp.tokenizer.parent))
            self.session = session or ort.InferenceSession(
                str(mp.onnx), providers=["CPUExecutionProvider"]
            )
            self.input_name = self.session.get_inputs()[0].name
            self.output_name = self.session.get_outputs()[0].name
        except Exception:
            # Fallback mode
            self.session = None
            self.tokenizer = None

    # ------------------------------------------------------------------

    @staticmethod
    def _hash_fallback(text: str, dim: int = 384) -> np.ndarray:
        """
        Deterministic hash-based embedding fallback.
        Produces a pseudo-random but stable float32 vector of length `dim`.
        """
        h = hashlib.sha256(text.encode("utf-8")).digest()
        # Repeat digest to fill dimension
        needed = dim * 4  # bytes
        buf = (h * ((needed // len(h)) + 1))[:needed]
        arr = np.frombuffer(buf, dtype=np.uint32)[:dim]
        return (arr % 1000).astype(np.float32)

    # ------------------------------------------------------------------

    def batch_encode(self, texts: List[str]) -> np.ndarray:
        """
        Encode a list of texts into embeddings.

        Returns:
            np.ndarray of shape [len(texts), D] float32.
        """
        if self.session is None or self.tokenizer is None:
            # Fallback for offline/no-model cases
            return np.stack([self._hash_fallback(t) for t in texts])

        enc = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            return_tensors="np",
        )
        ort_inputs = {self.input_name: enc["input_ids"]}
        outputs = self.session.run([self.output_name], ort_inputs)
        return outputs[0].astype(np.float32)

    def encode_one(self, text: str) -> np.ndarray:
        return self.batch_encode([text])[0]

    # ------------------------------------------------------------------

    def info(self) -> dict:
        """Return metadata about the embedder for diagnostics."""
        return {
            "task": self.paths.task,
            "id": self.paths.id,
            "alias": self.paths.alias,
            "root": str(self.paths.root_dir),
            "onnx": str(self.paths.onnx),
            "tokenizer": str(self.paths.tokenizer),
            "mode": "fallback" if self.session is None else "onnx",
        }
