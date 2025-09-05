from __future__ import annotations

import logging
from typing import Dict, List

import numpy as np
import torch
from transformers import AutoProcessor, MarkupLMModel

from .normalization import element_to_text

logger = logging.getLogger(__name__)

def _l2norm(a: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    n = np.linalg.norm(a, axis=-1, keepdims=True)
    n = np.maximum(n, eps)
    return a / n

class MarkupLMEmbedder:
    """
    Element embedder using MarkupLM (Transformers) from a local directory:
    src/her/models/markuplm-base/ (config.json + pytorch_model.bin + tokenizer files).
    """

    def __init__(self, model_dir: str, device: str = "cpu", batch_size: int = 16, normalize: bool = True):
        self.model_dir = model_dir
        self.device = torch.device(device)
        self.batch_size = int(batch_size)
        self.normalize = bool(normalize)

        # Load locally; no network calls.
        self.processor = AutoProcessor.from_pretrained(self.model_dir)
        self.model: MarkupLMModel = MarkupLMModel.from_pretrained(model_dir).to(self.device)
        self.model.eval()
        with torch.no_grad():
            self.dim = int(self.model.config.hidden_size)

        logger.info(
            "Loaded MarkupLM (transformers) dim=%d device=%s normalize=%s from %s",
            self.dim, self.device, self.normalize, model_dir
        )

    def encode(self, element: Dict) -> np.ndarray:
        arr = self.batch_encode([element])
        return arr[0]

    def batch_encode(self, elements: List[Dict]) -> np.ndarray:
        if not elements:
            return np.zeros((0, getattr(self, "dim", 768)), dtype=np.float32)

        texts = [element_to_text(e) for e in elements]
        vecs = np.zeros((len(texts), self.dim), dtype=np.float32)
        empty = [i for i, t in enumerate(texts) if t == ""]
        with torch.no_grad():
            for i in range(0, len(texts), self.batch_size):
                chunk = texts[i:i + self.batch_size]
                if all(t == "" for t in chunk):
                    continue
                inputs = self.processor(
                    text=chunk,
                    padding=True, truncation=True, max_length=512,
                    return_tensors="pt"
                ).to(self.device)

                outputs = self.model(**inputs)  # last_hidden_state: (B, T, H)
                cls = outputs.last_hidden_state[:, 0, :]  # (B, H)
                out = cls.detach().cpu().to(torch.float32).numpy()
                if self.normalize:
                    out = _l2norm(out)
                vecs[i:i + len(chunk)] = out

        # Leave truly empty elements as exact zero vectors (good for downstream logic).
        return vecs
