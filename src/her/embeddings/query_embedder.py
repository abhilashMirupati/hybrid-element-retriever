"""Query text embedding using e5-small model."""
from typing import Optional, List
import numpy as np
import logging

from ._resolve import get_query_resolver
from .cache import EmbeddingCache
from ..config import QUERY_EMBEDDING_DIM

logger = logging.getLogger(__name__)


class QueryEmbedder:
    """Embeds query text using e5-small model with caching."""
    
    def __init__(self, cache_enabled: bool = True):
        """Initialize query embedder.
        
        Args:
            cache_enabled: Whether to use embedding cache
        """
        self.resolver = get_query_resolver()
        self.dim = QUERY_EMBEDDING_DIM
        self.cache = EmbeddingCache(namespace="query") if cache_enabled else None
    
    def embed(self, text: str) -> np.ndarray:
        """Generate embedding for query text.
        
        Args:
            text: Query text to embed
            
        Returns:
            Normalized embedding vector of shape (dim,)
        """
        if not text:
            return np.zeros(self.dim, dtype=np.float32)
        
        # Check cache first
        if self.cache:
            cached = self.cache.get(text)
            if cached is not None:
                logger.debug(f"Cache hit for query: {text[:50]}")
                return cached
        
        # Generate embedding
        logger.debug(f"Generating embedding for query: {text[:50]}")
        
        # For e5-small, prepend "query: " prefix as per model documentation
        prefixed_text = f"query: {text}"
        embedding = self.resolver.embed(prefixed_text, normalize=True)
        
        # Cache the result
        if self.cache:
            self.cache.put(text, embedding)
        
        return embedding
    
    def batch_embed(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for multiple query texts.
        
        Args:
            texts: List of query texts
            
        Returns:
            Array of shape (n_texts, dim)
        """
        if not texts:
            return np.array([], dtype=np.float32).reshape(0, self.dim)
        
        embeddings = []
        for text in texts:
            embeddings.append(self.embed(text))
        
        return np.vstack(embeddings)
    
    def similarity(self, query_embedding: np.ndarray, target_embedding: np.ndarray) -> float:
        """Compute cosine similarity between embeddings.
        
        Args:
            query_embedding: Query embedding vector
            target_embedding: Target embedding vector
            
        Returns:
            Cosine similarity score in [0, 1]
        """
        # Ensure both are normalized
        query_norm = query_embedding / (np.linalg.norm(query_embedding) + 1e-8)
        target_norm = target_embedding / (np.linalg.norm(target_embedding) + 1e-8)
        
        # Compute cosine similarity
        similarity = np.dot(query_norm, target_norm)
        
        # Map from [-1, 1] to [0, 1]
        return (similarity + 1.0) / 2.0