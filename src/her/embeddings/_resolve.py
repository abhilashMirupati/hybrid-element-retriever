"""ONNX model resolution and loading with deterministic fallback."""

from __future__ import annotations
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging
import hashlib
import numpy as np
import json

logger = logging.getLogger(__name__)

from ..config import (
    get_models_dir,
    QUERY_MODEL_NAME,
    ELEMENT_MODEL_NAME,
    FALLBACK_EMBEDDING_DIM,
    QUERY_EMBEDDING_DIM,
    ELEMENT_EMBEDDING_DIM,
)


class ONNXModelResolver:
    """Resolves and loads ONNX models with fallback to deterministic embeddings."""

    def __init__(
        self, model_name: str, embedding_dim: int = FALLBACK_EMBEDDING_DIM
    ) -> None:
        """Initialize model resolver.

        Args:
            model_name: Name of the model (e.g., 'e5-small', 'markuplm-base')
            embedding_dim: Embedding dimension for this model
        """
        self.model_name = model_name
        self.embedding_dim = embedding_dim
        self.session: Optional[Any] = None
        self.tokenizer: Optional[Any] = None
        self.model_path: Optional[Path] = None
        self.tokenizer_path: Optional[Path] = None
        self._load_model()

    def _find_model_paths(self) -> tuple[Optional[Path], Optional[Path]]:
        """Find model and tokenizer paths using search order.

        Search order:
        1. HER_MODELS_DIR environment variable
        2. Package-bundled models directory
        3. User home directory ~/.her/models

        Returns:
            Tuple of (model_path, tokenizer_path) or (None, None) if not found
        """
        models_dir = get_models_dir()

        # Look for ONNX model file
        model_file = f"{self.model_name}.onnx"
        tokenizer_dir = f"{self.model_name}-tokenizer"

        model_path = models_dir / model_file
        tokenizer_path = models_dir / tokenizer_dir

        if model_path.exists() and tokenizer_path.exists():
            logger.info(f"Found model at: {model_path}")
            return model_path, tokenizer_path

        logger.info(f"Model not found at {models_dir}, will use fallback")
        return None, None

    def _load_model(self) -> None:
        """Try to load ONNX model, fall back gracefully if unavailable."""
        self.model_path, self.tokenizer_path = self._find_model_paths()

        if not self.model_path or not self.model_path.exists():
            logger.info(
                f"ONNX model '{self.model_name}' not found, using deterministic fallback"
            )
            return

        try:
            import onnxruntime as ort

            # Load ONNX model
            self.session = ort.InferenceSession(str(self.model_path))
            logger.info(f"Loaded ONNX model from {self.model_path}")

            # Try to load tokenizer
            if self.tokenizer_path and self.tokenizer_path.exists():
                try:
                    from transformers import AutoTokenizer

                    self.tokenizer = AutoTokenizer.from_pretrained(
                        str(self.tokenizer_path)
                    )
                    logger.info(f"Loaded tokenizer from {self.tokenizer_path}")
                except Exception as e:
                    logger.warning(
                        f"Failed to load tokenizer: {e}, will use simple tokenization"
                    )
                    self.tokenizer = None

        except Exception as e:
            logger.warning(
                f"Failed to load ONNX model: {e}, using deterministic fallback"
            )
            self.session = None
            self.tokenizer = None

    def embed(self, text: str, normalize: bool = True) -> np.ndarray:
        """Generate embedding for text, using ONNX if available or deterministic fallback.

        Args:
            text: Text to embed
            normalize: Whether to normalize to unit vector

        Returns:
            Embedding vector of shape (embedding_dim,)
        """
        if self.session and self.tokenizer:
            try:
                # Tokenize text
                inputs = self.tokenizer(
                    text,
                    return_tensors="np",
                    padding=True,
                    truncation=True,
                    max_length=512,
                )

                # Prepare inputs for ONNX runtime
                ort_inputs = {
                    k: v
                    for k, v in inputs.items()
                    if k in [inp.name for inp in self.session.get_inputs()]
                }

                # Run inference
                outputs = self.session.run(None, ort_inputs)

                # Extract embedding (handle different output formats)
                if len(outputs[0].shape) == 3:
                    # Transformer output: [batch, sequence, hidden]
                    # Use mean pooling over sequence dimension
                    embedding = outputs[0].mean(axis=1).squeeze()
                elif len(outputs[0].shape) == 2:
                    # Already pooled: [batch, hidden]
                    embedding = outputs[0].squeeze()
                else:
                    embedding = outputs[0].squeeze()

                # Ensure correct dimension
                if embedding.shape[0] != self.embedding_dim:
                    # Truncate or pad if needed
                    if embedding.shape[0] > self.embedding_dim:
                        embedding = embedding[: self.embedding_dim]
                    else:
                        padding = np.zeros(self.embedding_dim - embedding.shape[0])
                        embedding = np.concatenate([embedding, padding])

                # Normalize if requested
                if normalize:
                    norm = np.linalg.norm(embedding)
                    if norm > 0:
                        embedding = embedding / norm

                return embedding.astype(np.float32)

            except Exception as e:
                logger.warning(f"ONNX inference failed: {e}, using fallback")

        # Deterministic fallback based on SHA256 hash
        return self._deterministic_embedding(text, normalize)

    def _deterministic_embedding(self, text: str, normalize: bool = True) -> np.ndarray:
        """Generate deterministic embedding from text using SHA256.

        Args:
            text: Text to embed
            normalize: Whether to normalize to unit vector

        Returns:
            Deterministic embedding vector
        """
        # Use SHA256 for more bits
        hash_obj = hashlib.sha256(text.encode("utf-8"))
        hash_bytes = hash_obj.digest()

        # Use hash to seed random generator for reproducibility
        seed = int.from_bytes(hash_bytes[:4], "big")
        rng = np.random.RandomState(seed)

        # Generate embedding with correct dimension
        embedding = rng.randn(self.embedding_dim).astype(np.float32)

        # Add some structure based on text features
        # This makes the fallback slightly more meaningful
        text_lower = text.lower()

        # Boost certain dimensions based on text features
        if "click" in text_lower or "button" in text_lower:
            embedding[0:10] *= 1.5
        if "input" in text_lower or "text" in text_lower:
            embedding[10:20] *= 1.5
        if "search" in text_lower or "find" in text_lower:
            embedding[20:30] *= 1.5
        if "submit" in text_lower or "form" in text_lower:
            embedding[30:40] *= 1.5

        # Normalize to unit vector if requested
        if normalize:
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm

        return embedding

    def batch_embed(self, texts: List[str], normalize: bool = True) -> np.ndarray:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed
            normalize: Whether to normalize to unit vectors

        Returns:
            Array of shape (n_texts, embedding_dim)
        """
        if not texts:
            return np.array([], dtype=np.float32).reshape(0, self.embedding_dim)

        embeddings = []
        for text in texts:
            embeddings.append(self.embed(text, normalize=normalize))

        return np.vstack(embeddings)


def get_query_resolver() -> ONNXModelResolver:
    """Get resolver for query text embeddings (e5-small)."""
    return ONNXModelResolver(
        model_name=QUERY_MODEL_NAME, embedding_dim=QUERY_EMBEDDING_DIM
    )


def get_element_resolver() -> ONNXModelResolver:
    """Get resolver for element embeddings (markuplm-base)."""
    return ONNXModelResolver(
        model_name=ELEMENT_MODEL_NAME, embedding_dim=ELEMENT_EMBEDDING_DIM
    )


def load_model_info() -> Optional[Dict[str, Any]]:
    """Load MODEL_INFO.json if it exists.

    Returns:
        Model info dictionary or None if not found
    """
    models_dir = get_models_dir()
    model_info_path = models_dir / "MODEL_INFO.json"

    if model_info_path.exists():
        try:
            with open(model_info_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load MODEL_INFO.json: {e}")

    return None
