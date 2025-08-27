"""Query text embedder with ONNX support and deterministic fallback."""
from __future__ import annotations
from typing import Optional, List, Dict, Any
import numpy as np
import logging
from ._resolve import get_query_resolver, FALLBACK_DIM
from .cache import EmbeddingCache

logger = logging.getLogger(__name__)

MODEL_VERSION = "minilm-e5-small-v2"


class QueryEmbedder:
    """Embeds query text using MiniLM/E5-small or deterministic fallback."""
    
    def __init__(self, cache: Optional[EmbeddingCache] = None, dim: int = FALLBACK_DIM) -> None:
        self.cache = cache or EmbeddingCache()
        self.resolver = get_query_resolver()
        self.dim = dim
        self._log_mode()
    
    def _log_mode(self) -> None:
        """Log whether using ONNX or fallback."""
        if self.resolver.session:
            logger.info(f"QueryEmbedder using ONNX model")
        else:
            logger.info(f"QueryEmbedder using deterministic fallback (dim={self.dim})")
    
    def embed(self, text: str) -> np.ndarray:
        """Generate embedding for query text."""
        # Cache key includes model version and text
        cache_key = f"query:{MODEL_VERSION}:{text}"
        
        # Check cache first
        cached = self.cache.get(cache_key)
        if cached is not None:
            logger.debug(f"Cache hit for query: {text[:50]}...")
            return cached
        
        # Generate embedding
        logger.debug(f"Generating embedding for query: {text[:50]}...")
        embedding = self.resolver.embed(text, self.dim)
        
        # Cache the result
        self.cache.put(cache_key, embedding)
        
        return embedding
    
    def embed_batch(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings for multiple queries."""
        return [self.embed(text) for text in texts]
    
    def similarity(self, query_vec: np.ndarray, element_vec: np.ndarray) -> float:
        """Compute cosine similarity between query and element vectors."""
        # Ensure both are normalized
        query_norm = query_vec / (np.linalg.norm(query_vec) + 1e-8)
        element_norm = element_vec / (np.linalg.norm(element_vec) + 1e-8)
        
        # Cosine similarity
        return float(np.dot(query_norm, element_norm))