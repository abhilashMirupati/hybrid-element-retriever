from __future__ import annotations
import logging, os
from typing import Dict, List
import numpy as np, torch
from transformers import MarkupLMModel, PreTrainedTokenizerFast
from .normalization import element_to_text

logger = logging.getLogger(__name__)

def _l2norm(a: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    n = np.linalg.norm(a, axis=-1, keepdims=True); n = np.maximum(n, eps); return a / n

class MarkupLMEmbedder:
    def __init__(self, model_dir: str, device: str = "cpu", batch_size: int = 16, normalize: bool = True):
        self.model_dir = model_dir; self.device = torch.device(device); self.batch_size = int(batch_size); self.normalize = bool(normalize)
        tok_file = os.path.join(self.model_dir, "tokenizer.json")
        if not os.path.isfile(tok_file): raise RuntimeError(f"MarkupLM tokenizer.json not found at {tok_file}")
        self.tokenizer = PreTrainedTokenizerFast(tokenizer_file=tok_file)
        if self.tokenizer.cls_token is None: self.tokenizer.cls_token = "<s>"
        if self.tokenizer.sep_token is None: self.tokenizer.sep_token = "</s>"
        if self.tokenizer.pad_token is None: self.tokenizer.pad_token = "<pad>"
        if self.tokenizer.unk_token is None: self.tokenizer.unk_token = "<unk>"
        if self.tokenizer.mask_token is None: self.tokenizer.mask_token = "<mask>"
        self.tokenizer.model_max_length = 512
        self.model: MarkupLMModel = MarkupLMModel.from_pretrained(self.model_dir, local_files_only=True).to(self.device)
        self.model.eval()
        with torch.no_grad(): self.dim = int(self.model.config.hidden_size)
        logger.info("Loaded MarkupLM dim=%d device=%s normalize=%s from %s", self.dim, self.device, self.normalize, self.model_dir)

    def encode(self, element: Dict) -> np.ndarray: return self.batch_encode([element])[0]

    def batch_encode(self, elements: List[Dict]) -> np.ndarray:
        if not elements: return np.zeros((0, getattr(self, "dim", 768)), dtype=np.float32)
        texts = [element_to_text(e) for e in elements]; vecs = np.zeros((len(texts), self.dim), dtype=np.float32)
        with torch.no_grad():
            for i in range(0, len(texts), self.batch_size):
                chunk = texts[i:i + self.batch_size]
                if all(t == "" for t in chunk): continue
                inputs = self.tokenizer(text=chunk, padding=True, truncation=True, max_length=512, return_tensors="pt").to(self.device)
                outputs = self.model(**inputs); cls = outputs.last_hidden_state[:, 0, :]
                out = cls.detach().cpu().to(torch.float32).numpy()
                if self.normalize: out = _l2norm(out)
                vecs[i:i + len(chunk)] = out
        return vecs
