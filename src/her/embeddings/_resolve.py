"""ONNX model resolution and loading with deterministic fallback."""
from __future__ import annotations
from pathlib import Path
from typing import Optional, Union, Dict, Any
import logging
import os
import hashlib
import numpy as np

logger = logging.getLogger(__name__)

# Model paths relative to package
MODEL_DIR = Path(__file__).parent.parent / "models"
QUERY_MODEL_PATH = MODEL_DIR / "minilm-e5-small.onnx"
ELEMENT_MODEL_PATH = MODEL_DIR / "markuplm-base.onnx"

# Fallback dimensions when models unavailable
FALLBACK_DIM = 384  # Standard dimension for sentence transformers


class ONNXModelResolver:
    """Resolves and loads ONNX models with fallback to deterministic embeddings."""
    
    def __init__(self, model_path: Optional[Union[str, Path]] = None) -> None:
        self.model_path = Path(model_path) if model_path else None
        self.session: Optional[Any] = None
        self.tokenizer: Optional[Any] = None
        self._load_model()
    
    def _load_model(self) -> None:
        """Try to load ONNX model, fall back gracefully if unavailable."""
        if not self.model_path or not self.model_path.exists():
            logger.info(f"ONNX model not found at {self.model_path}, using deterministic fallback")
            return
        
        try:
            import onnxruntime as ort
            self.session = ort.InferenceSession(str(self.model_path))
            logger.info(f"Loaded ONNX model from {self.model_path}")
        except Exception as e:
            logger.warning(f"Failed to load ONNX model: {e}, using deterministic fallback")
            self.session = None
    
    def embed(self, text: str, dim: int = FALLBACK_DIM) -> np.ndarray:
        """Generate embedding for text, using ONNX if available or deterministic fallback."""
        if self.session:
            try:
                # Simplified tokenization for demo (real impl would use transformers)
                # This is a placeholder - real implementation would tokenize properly
                tokens = self._simple_tokenize(text)
                inputs = {self.session.get_inputs()[0].name: tokens}
                outputs = self.session.run(None, inputs)
                embedding = outputs[0].squeeze()
                
                # Normalize
                norm = np.linalg.norm(embedding)
                if norm > 0:
                    embedding = embedding / norm
                
                return embedding.astype(np.float32)
            except Exception as e:
                logger.warning(f"ONNX inference failed: {e}, using fallback")
        
        # Deterministic fallback based on SHA256 hash
        return self._deterministic_embedding(text, dim)
    
    def _simple_tokenize(self, text: str) -> np.ndarray:
        """Simple tokenization placeholder for ONNX input."""
        # This would normally use the actual tokenizer
        # For now, create dummy input matching expected shape
        max_length = 512
        vocab_size = 30522  # BERT vocab size
        
        # Hash text to get consistent token IDs
        hash_obj = hashlib.sha256(text.encode())
        hash_bytes = hash_obj.digest()
        
        # Convert to token IDs
        tokens = []
        for i in range(min(len(hash_bytes), max_length)):
            tokens.append(int.from_bytes(hash_bytes[i:i+1], 'big') % vocab_size)
        
        # Pad to max_length
        while len(tokens) < max_length:
            tokens.append(0)
        
        return np.array([tokens[:max_length]], dtype=np.int64)
    
    def _deterministic_embedding(self, text: str, dim: int) -> np.ndarray:
        """Generate deterministic embedding from text using SHA256."""
        # Use SHA256 for more bits
        hash_obj = hashlib.sha256(text.encode())
        hash_bytes = hash_obj.digest()
        
        # Use hash to seed random generator for reproducibility
        seed = int.from_bytes(hash_bytes[:4], 'big')
        rng = np.random.RandomState(seed)
        
        # Generate embedding
        embedding = rng.randn(dim).astype(np.float32)
        
        # Normalize to unit vector
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        
        return embedding


def get_query_resolver() -> ONNXModelResolver:
    """Get resolver for query text embeddings."""
    return ONNXModelResolver(QUERY_MODEL_PATH)


def get_element_resolver() -> ONNXModelResolver:
    """Get resolver for element embeddings."""
    return ONNXModelResolver(ELEMENT_MODEL_PATH)