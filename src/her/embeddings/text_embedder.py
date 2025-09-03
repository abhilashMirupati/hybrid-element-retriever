"""
HER Text Embedding (MiniLM/E5-small ONNX).

Responsibilities
----------------
- Load the E5-small ONNX model from resolved paths (offline).
- Provide a clean API:
    - batch_encode_texts(list[str], batch_size=32) -> np.ndarray (float32, [N, D])
    - batch_encode(list[str]) -> np.ndarray (float32, [N, D]) [alias]
    - encode_one(str) -> np.ndarray (float32, [D])
- Reuse a single onnxruntime.InferenceSession across calls/instances.
- No silent hash-based fallbacks; explicit, actionable errors if missing.

Notes
-----
- Depends on: _resolve.resolve_text_embedding()
- Model files: model.onnx + tokenizer.json
- External deps: onnxruntime, transformers (tokenizer only)
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Dict, Any
import logging
import numpy as np

from . import _resolve


class TextEmbedder:
    """MiniLM / E5-small ONNX embedder (sentence-transformers)."""

    # Shared caches across instances keyed by absolute directory paths
    _SESSION_CACHE: Dict[str, Any] = {}
    _TOKENIZER_CACHE: Dict[str, Any] = {}

    def __init__(self, session: Optional[object] = None, device: str = "cpu"):
        self._logger = logging.getLogger(__name__)
        mp = _resolve.resolve_text_embedding()
        self.paths = mp

        if not mp.exists():  # pragma: no cover - guarded by resolver
            raise RuntimeError(
                "Text embedding model files not found. Expected ONNX model and tokenizer. "
                "Run scripts/install_models.sh to install MiniLM/E5-small (ONNX)."
            )

        # Lazy imports to avoid heavy deps at module import time
        try:
            from transformers import AutoTokenizer  # type: ignore
            import onnxruntime as ort  # type: ignore
        except Exception as e:  # pragma: no cover - environment/setup errors
            raise RuntimeError(
                f"Failed to import dependencies for ONNX text embedding: {e}. "
                "Ensure onnxruntime and transformers are installed."
            )

        # Tokenizer reuse per directory
        tok_dir = str(mp.tokenizer.parent)
        if tok_dir in TextEmbedder._TOKENIZER_CACHE:
            self.tokenizer = TextEmbedder._TOKENIZER_CACHE[tok_dir]
        else:
            tok = AutoTokenizer.from_pretrained(tok_dir, local_files_only=True)
            TextEmbedder._TOKENIZER_CACHE[tok_dir] = tok
            self.tokenizer = tok

        # Session reuse per model path
        onnx_path = str(mp.onnx)
        if session is not None:
            self.session = session
        elif onnx_path in TextEmbedder._SESSION_CACHE:
            self.session = TextEmbedder._SESSION_CACHE[onnx_path]
        else:
            sess = ort.InferenceSession(onnx_path, providers=["CPUExecutionProvider"])  # type: ignore[name-defined]
            TextEmbedder._SESSION_CACHE[onnx_path] = sess
            self.session = sess

        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name

        # Determine output dimension (fallback to 384 if unavailable)
        self.dim: int = 384
        try:
            # Run a minimal forward to infer dimension
            test_vec = self.batch_encode_texts(["ok"], batch_size=1)
            if test_vec.ndim == 2 and test_vec.shape[1] > 0:
                self.dim = int(test_vec.shape[1])
        except Exception:
            # Keep default dim if inference-at-init fails
            self.dim = 384
        self._logger.info(
            "Loaded text embedder (ONNX): onnx=%s tokenizer=%s dim=%s",
            onnx_path,
            tok_dir,
            self.dim,
        )

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

    def batch_encode_texts(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """Return (N, D) float32; tokenizer padding/truncation=max_length=512."""
        if not isinstance(texts, list):  # pragma: no cover - defensive
            raise TypeError("texts must be a list[str]")

        if len(texts) == 0:
            return np.zeros((0, self.dim), dtype=np.float32)

        # Local references
        tokenizer = self.tokenizer
        session = self.session

        # Treat empty/whitespace-only strings as zero-vectors deterministically
        stripped = [str(t).strip() for t in texts]
        is_empty = [s == "" for s in stripped]
        outputs: List[np.ndarray] = []
        n = len(texts)
        bs = max(1, int(batch_size))
        # Build indices for non-empty texts to actually encode
        non_empty_indices = [i for i, e in enumerate(is_empty) if not e]
        # Pre-allocate full output with zeros
        full = np.zeros((n, self.dim), dtype=np.float32)
        if not non_empty_indices:
            return full
        # Encode non-empty chunks only
        for start in range(0, len(non_empty_indices), bs):
            idxs = non_empty_indices[start : start + bs]
            chunk = [stripped[i] for i in idxs]
            enc = tokenizer(
                chunk,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="np",
            )
            ort_inputs = {self.input_name: enc["input_ids"]}
            out = session.run([self.output_name], ort_inputs)[0]
            if out.dtype != np.float32:
                out = out.astype(np.float32, copy=False)
            outputs.append((idxs, out))
        # Scatter-gather into full array
        for idxs, out in outputs:
            full[idxs, :] = out
        return full.astype(np.float32, copy=False)

    def batch_encode(self, texts: List[str]) -> np.ndarray:
        """Compatibility alias for previous API."""
        return self.batch_encode_texts(texts, batch_size=32)

    def encode_one(self, text: str) -> np.ndarray:
        return self.batch_encode_texts([text], batch_size=1)[0]

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
            "mode": "onnx",
        }
