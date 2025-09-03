"""MarkupLM (Transformers) element embedder.

Loads a local MarkupLM model directory (offline) and produces float32
embeddings for DOM element descriptors. Minimal input is the element "text".

Public API mirrors other embedders:
  - encode(element: dict) -> np.ndarray[(dim,), float32]
  - batch_encode(elements: list[dict]) -> np.ndarray[(N, dim), float32]

Guard rails:
- Does not import onnxruntime or optimum.
- Requires an installed local Transformers model directory.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import torch
from transformers import AutoProcessor, MarkupLMModel  # type: ignore


class MarkupLMEmbedder:
    def __init__(self, model_dir: str | Path, device: str = "cpu") -> None:
        self.model_dir = str(Path(model_dir))
        self.device = torch.device(device)
        # Load processor and model from local directory
        self.processor = AutoProcessor.from_pretrained(self.model_dir)
        self.model = MarkupLMModel.from_pretrained(self.model_dir).to(self.device).eval()
        # MarkupLM-base hidden size
        self.dim: int = int(getattr(self.model.config, "hidden_size", 768))

    def _encode_one(self, element: Dict[str, Any]) -> np.ndarray:
        text = (element.get("text") or "").strip()
        if not text:
            return np.zeros((self.dim,), dtype=np.float32)
        inputs = self.processor(text=[text], return_tensors="pt", truncation=True, padding=True)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        with torch.no_grad():
            out = self.model(**inputs).last_hidden_state[:, 0, :]  # CLS token
        return out.squeeze(0).detach().cpu().float().numpy()

    def encode(self, element: Dict[str, Any]) -> np.ndarray:
        return self._encode_one(element)

    def batch_encode(self, elements: List[Dict[str, Any]]) -> np.ndarray:
        if not elements:
            return np.zeros((0, self.dim), dtype=np.float32)
        mats = [self._encode_one(e) for e in elements]
        return np.stack(mats, axis=0)

