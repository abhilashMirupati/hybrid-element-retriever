"""Element embedder with automatic fallback when numpy/ONNX not available."""

from __future__ import annotations
from typing import Dict, Any, List, Optional, Union

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None  # type: ignore

from .cache import EmbeddingCache

# Try to import ONNX resolver, fall back if not available
try:
    from ._resolve import get_element_resolver, ONNXModelResolver
    from ..utils import sha1_of
    ONNX_AVAILABLE = True
except (ImportError, Exception):
    ONNX_AVAILABLE = False
    ONNXModelResolver = None  # type: ignore
    
    # Fallback sha1_of implementation
    import hashlib
    def sha1_of(text: str) -> str:
        return hashlib.sha1(text.encode()).hexdigest()


class ElementEmbedder:
    """Element embedder that uses ONNX resolver with fallback to feature-based embeddings.
    
    Automatically falls back to non-numpy implementation when dependencies unavailable.
    """
    
    def __init__(self, cache: Optional[EmbeddingCache] = None, resolver: Optional[ONNXModelResolver] = None, cache_enabled: bool = True) -> None:
        self.cache = (cache or EmbeddingCache()) if cache_enabled else None
        self.dim = 768  # Default dimension for element embeddings
        
        # Try to use ONNX resolver if available
        if ONNX_AVAILABLE and NUMPY_AVAILABLE:
            try:
                self.resolver = resolver or get_element_resolver()
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
            from .fallback_embedder import FallbackElementEmbedder
            self.fallback_embedder = FallbackElementEmbedder(dim=self.dim)
    
    def _key(self, descriptor: Dict[str, Any]) -> str:
        """Generate cache key for descriptor."""
        # Create deterministic key from descriptor
        key_parts = [
            descriptor.get('tag', descriptor.get('tagName', '')),
            descriptor.get('id', ''),
            descriptor.get('text', '')[:100],  # Limit text length
        ]
        key_str = '|'.join(str(p) for p in key_parts)
        return f"e|{sha1_of(key_str)}|{self.dim}"
    
    def embed(self, descriptor: Dict[str, Any]) -> Union[List[float], 'np.ndarray']:
        """Embed element descriptor, returning numpy array if available, else list."""
        key = self._key(descriptor)
        
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
            vec = self.fallback_embedder.embed(descriptor)
        else:
            # Convert descriptor to text for ONNX model
            text = self._descriptor_to_text(descriptor)
            vec = self.resolver.embed(text)
            if NUMPY_AVAILABLE:
                vec = vec.astype('float32')
            else:
                vec = list(vec) if hasattr(vec, '__iter__') else [vec]
        
        # Cache result
        if self.cache is not None:
            self.cache.put(key, vec)
        
        return vec
    
    def embed_batch(self, descriptors: List[Dict[str, Any]]) -> List[Union[List[float], 'np.ndarray']]:
        """Embed multiple descriptors."""
        return [self.embed(desc) for desc in descriptors]
    
    def _descriptor_to_text(self, descriptor: Dict[str, Any]) -> str:
        """Convert descriptor to text representation for embedding."""
        parts = []
        
        # Add tag
        tag = descriptor.get('tag', descriptor.get('tagName', ''))
        if tag:
            parts.append(f"tag:{tag}")
        
        # Add ID
        elem_id = descriptor.get('id')
        if elem_id:
            parts.append(f"id:{elem_id}")
        
        # Add classes
        classes = descriptor.get('classes', [])
        if classes:
            if isinstance(classes, list):
                parts.append(f"class:{' '.join(classes)}")
            else:
                parts.append(f"class:{classes}")
        
        # Add text
        text = descriptor.get('text', '')
        if text:
            parts.append(f"text:{text[:200]}")  # Limit text length
        
        # Add key attributes
        attrs = descriptor.get('attributes', {})
        for key in ['role', 'type', 'name', 'placeholder', 'aria-label']:
            if key in attrs:
                parts.append(f"{key}:{attrs[key]}")
        
        return ' '.join(parts)