"""MarkupLM (Transformers) element embedder.

Loads a local MarkupLM model directory (offline) and produces float32
embeddings for DOM element descriptors using a canonical text built by
``normalization.element_to_text``.

Public API:
  - encode(element: dict) -> np.ndarray[(dim,), float32]
  - batch_encode(elements: list[dict]) -> np.ndarray[(N, dim), float32]

Notes:
- Heavy deps are imported inside __init__ to keep module import light.
- Uses CLS token (last_hidden_state[:, 0, :]).
- Empty elements map to deterministic all-zeros vectors.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List
import logging

import numpy as np

from .normalization import element_to_text


class MarkupLMEmbedder:
    def __init__(self, model_dir: str | Path, device: str = "cpu", batch_size: int = 16) -> None:
        self.model_dir = str(Path(model_dir))
        self.batch_size = int(batch_size)
        self._logger = logging.getLogger(__name__)
        # Localize heavy imports
        from transformers import AutoProcessor, MarkupLMModel  # type: ignore
        import torch  # type: ignore

        self._torch = torch
        self.device = torch.device(device)
        # Load processor and model from local directory (offline)
        self.processor = AutoProcessor.from_pretrained(self.model_dir, local_files_only=True)
        self.model = (
            MarkupLMModel.from_pretrained(self.model_dir, local_files_only=True)
            .to(self.device)
            .eval()
        )
        # MarkupLM-base hidden size
        self.dim: int = int(getattr(self.model.config, "hidden_size", 768))
        self._logger.info(
            "Loaded MarkupLM (Transformers) model: dir=%s dim=%s device=%s",
            self.model_dir,
            self.dim,
            self.device,
        )

    def _encode_one(self, element: Dict[str, Any]) -> np.ndarray:
        txt = element_to_text(element)
        if not txt:
            return np.zeros((self.dim,), dtype=np.float32)
        return self.batch_encode([element])[0]

    def encode(self, element: Dict[str, Any]) -> np.ndarray:
        return self._encode_one(element)

    def batch_encode(self, elements: List[Dict[str, Any]]) -> np.ndarray:
        if not elements:
            return np.zeros((0, self.dim), dtype=np.float32)

        # Build canonical texts and separate empties
        texts: List[str] = [element_to_text(e) for e in elements]
        empty_mask = [t == "" for t in texts]

        # Pre-allocate output
        out = np.zeros((len(elements), self.dim), dtype=np.float32)

        # Indices of non-empty items to process
        non_empty_indices = [i for i, is_empty in enumerate(empty_mask) if not is_empty]
        if not non_empty_indices:
            return out

        # Process in micro-batches to avoid OOM
        from math import ceil

        total = len(non_empty_indices)
        bs = max(1, self.batch_size)
        num_batches = ceil(total / bs)

        # Local references
        torch = self._torch

        for b in range(num_batches):
            start = b * bs
            end = min(total, start + bs)
            batch_idx = non_empty_indices[start:end]
            batch_texts = [texts[i] for i in batch_idx]
            enc = self.processor(
                text=batch_texts,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt",
            )
            enc = {k: v.to(self.device) for k, v in enc.items()}
            with torch.no_grad():
                last_hidden = self.model(**enc).last_hidden_state  # [B, T, H]
                cls = last_hidden[:, 0, :]  # [B, H]
            cls_np = cls.detach().cpu().float().numpy()
            out[batch_idx, :] = cls_np

        return out.astype(np.float32, copy=False)

