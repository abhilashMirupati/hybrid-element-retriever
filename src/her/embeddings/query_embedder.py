"""Query embedder with automatic fallback when numpy/ONNX not available."""

from __future__ import annotations
from typing import List, Optional, Union

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None  # type: ignore

from .cache import EmbeddingCache

# Try to import ONNX resolver, fall back if not available
try:
    from ._resolve import get_query_resolver, ONNXModelResolver
    from ..utils import sha1_of
    ONNX_AVAILABLE = True
except (ImportError, Exception):
    ONNX_AVAILABLE = False
    ONNXModelResolver = None  # type: ignore
    
    # Fallback sha1_of implementation
    import hashlib
    def sha1_of(text: str) -> str:
        return hashlib.sha1(text.encode()).hexdigest()


class QueryEmbedder:
    """Query embedder that uses ONNX resolver with fallback to deterministic embeddings.
    
    Automatically falls back to non-numpy implementation when dependencies unavailable.
    """
    
    def __init__(self, cache: Optional[EmbeddingCache] = None, resolver: Optional[ONNXModelResolver] = None, cache_enabled: bool = True) -> None:
        self.cache = (cache or EmbeddingCache()) if cache_enabled else None
        self.dim = 384  # Default dimension
        
        # Try to use ONNX resolver if available
        if ONNX_AVAILABLE and NUMPY_AVAILABLE:
            try:
                self.resolver = resolver or get_query_resolver()
                self.dim = int(self.resolver.embedding_dim)
                self.use_fallback = False
            except Exception:
                self.resolver = None
                self.use_fallback = True
        else:
            self.resolver = None
            self.use_fallback = True
        
        # Initialize fallback embedder if needed
        if self.use_fallback:
            from .fallback_embedder import FallbackQueryEmbedder
            self.fallback_embedder = FallbackQueryEmbedder(dim=self.dim)
    
    def _key(self, text: str) -> str:
        return f"q|{sha1_of(text)}|{self.dim}"
    
    def embed(self, text: str) -> Union[List[float], 'np.ndarray']:
        """Embed text, returning numpy array if available, else list."""
        key = self._key(text)
        
        # Check cache
        if self.cache is not None:
            hit = self.cache.get(key)
            if hit is not None:
                if NUMPY_AVAILABLE:
                    return hit.astype('float32')
                else:
                    return hit if isinstance(hit, list) else list(hit)
        
        # Generate embedding
        if self.use_fallback:
            vec = self.fallback_embedder.embed(text)
        else:
            vec = self.resolver.embed(text)
            if NUMPY_AVAILABLE:
                vec = vec.astype('float32')
            else:
                vec = list(vec) if hasattr(vec, '__iter__') else [vec]
        
        # Cache result
        if self.cache is not None:
            self.cache.put(key, vec)
        
        return vec
    
    def embed_batch(self, texts: List[str]) -> List[Union[List[float], 'np.ndarray']]:
        """Embed multiple texts."""
        return [self.embed(t) for t in texts]
    
    def batch_embed(self, texts: List[str]) -> Union[List[List[float]], 'np.ndarray']:
        """Embed batch, returning 2D array if numpy available."""
        if not texts:
            if NUMPY_AVAILABLE:
                return np.zeros((0, self.dim), dtype='float32')
            else:
                return []
        
        vecs = [self.embed(t) for t in texts]
        
        if NUMPY_AVAILABLE and not self.use_fallback:
            return np.stack(vecs, axis=0)
        else:
            return vecs
    
    @staticmethod
    def similarity(vec1: Union[List[float], 'np.ndarray'], vec2: Union[List[float], 'np.ndarray']) -> float:
        """Compute cosine similarity between vectors."""
        if NUMPY_AVAILABLE and isinstance(vec1, np.ndarray) and isinstance(vec2, np.ndarray):
            v1 = vec1.astype('float32')
            v2 = vec2.astype('float32')
            denom = float(np.linalg.norm(v1) * np.linalg.norm(v2))
            return float(np.dot(v1, v2) / denom) if denom != 0 else 0.0
        else:
            # Fallback to pure Python
            from .fallback_embedder import FallbackQueryEmbedder
            # Convert to lists if needed
            v1 = list(vec1) if hasattr(vec1, '__iter__') else [vec1]
            v2 = list(vec2) if hasattr(vec2, '__iter__') else [vec2]
            return FallbackQueryEmbedder.similarity(v1, v2)