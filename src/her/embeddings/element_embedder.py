# src/her/embedders/element_embedder.py
"""
Element Embedder using MarkupLM (ONNX).
Encodes DOM + Accessibility element snapshots into dense vectors for retrieval.

Contract:
- Input: list[dict] (each dict = element node with tag, text, attrs, role, etc.)
- Output: np.ndarray float32 embeddings (batch_size x hidden_dim)
"""

import os
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any

import numpy as np
import onnxruntime as ort

HER_MODELS_DIR = Path(__file__).resolve().parents[2] / "models"


class ElementEmbedder:
    def __init__(self, model_name: str = "markuplm-base-onnx", device: str = "cpu"):
        self.model_dir = self._resolve_model_dir(model_name)
        self.session = ort.InferenceSession(str(self.model_dir / "model.onnx"),
                                            providers=["CPUExecutionProvider"])
        self.tokenizer_path = self.model_dir / "tokenizer.json"
        if not self.tokenizer_path.exists():
            raise FileNotFoundError(f"Tokenizer not found: {self.tokenizer_path}")
        # minimal tokenizer loader stub; real impl should use HuggingFace tokenizers
        import json
        with open(self.tokenizer_path, "r", encoding="utf-8") as f:
            self.tokenizer_config = json.load(f)

    def _resolve_model_dir(self, model_name: str) -> Path:
        # Precedence: HER_MODELS_DIR → packaged → ~/.her/models
        candidates = [
            HER_MODELS_DIR / model_name,
            Path.home() / ".her" / "models" / model_name,
        ]
        for c in candidates:
            if (c / "model.onnx").exists():
                return c
        raise FileNotFoundError(f"Model {model_name} not found in {candidates}")

    def _hash_element(self, element: Dict[str, Any]) -> str:
        """Stable hash for caching (dict must be deterministic)."""
        m = hashlib.sha256()
        m.update(json.dumps(element, sort_keys=True).encode("utf-8"))
        return m.hexdigest()

    def batch_encode(self, elements: List[Dict[str, Any]]) -> np.ndarray:
        """Embed multiple elements. Returns np.ndarray float32."""
        if not elements:
            return np.zeros((0, 768), dtype=np.float32)

        # Dummy tokenizer: flatten element dict into string
        # Real impl should align with MarkupLM tokenization
        inputs = [self._flatten_element(e) for e in elements]

        # Stubbed encoding for demonstration (replace with tokenizer.encode_batch)
        encoded_inputs = np.random.rand(len(inputs), 768).astype(np.float32)

        # Call ONNX model (stub: feed dummy ids)
        # Example (pseudocode, depends on tokenizer format):
        # ort_inputs = {"input_ids": ids, "attention_mask": mask}
        # ort_outs = self.session.run(None, ort_inputs)
        # embeddings = ort_outs[0].astype(np.float32)

        return encoded_inputs

    def _flatten_element(self, element: Dict[str, Any]) -> str:
        """Convert DOM node dict into a flat string for embedding."""
        tag = element.get("tag", "")
        role = element.get("role", "")
        text = element.get("text", "")
        attrs = " ".join(f"{k}={v}" for k, v in element.get("attrs", {}).items())
        return f"{tag} {role} {text} {attrs}".strip()
