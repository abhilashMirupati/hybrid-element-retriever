"""Element embedder with markup-aware ONNX support and deterministic fallback."""
from __future__ import annotations
from typing import Dict, Any, Optional, List
import numpy as np
import json
import logging
from ._resolve import get_element_resolver, FALLBACK_DIM
from .cache import EmbeddingCache

logger = logging.getLogger(__name__)

MODEL_VERSION = "markuplm-base-v1"


class ElementEmbedder:
    """Embeds DOM elements using MarkupLM or deterministic fallback."""
    
    def __init__(self, cache: Optional[EmbeddingCache] = None, dim: int = FALLBACK_DIM) -> None:
        self.cache = cache or EmbeddingCache()
        self.resolver = get_element_resolver()
        self.dim = dim
        self._log_mode()
    
    def _log_mode(self) -> None:
        """Log whether using ONNX or fallback."""
        if self.resolver.session:
            logger.info(f"ElementEmbedder using ONNX model")
        else:
            logger.info(f"ElementEmbedder using deterministic fallback (dim={self.dim})")
    
    def embed(self, element: Dict[str, Any]) -> np.ndarray:
        """Generate embedding for a DOM element descriptor."""
        # Create signature for caching
        sig = self._element_signature(element)
        cache_key = f"element:{MODEL_VERSION}:{sig}"
        
        # Check cache
        cached = self.cache.get(cache_key)
        if cached is not None:
            logger.debug(f"Cache hit for element: {element.get('tag', 'unknown')}")
            return cached
        
        # Generate text representation of element
        element_text = self._element_to_text(element)
        
        # Generate embedding
        logger.debug(f"Generating embedding for element: {element.get('tag', 'unknown')}")
        embedding = self.resolver.embed(element_text, self.dim)
        
        # Cache result
        self.cache.put(cache_key, embedding)
        
        return embedding
    
    def embed_batch(self, elements: List[Dict[str, Any]]) -> List[np.ndarray]:
        """Generate embeddings for multiple elements."""
        return [self.embed(element) for element in elements]
    
    def _element_signature(self, element: Dict[str, Any]) -> str:
        """Create a unique signature for an element for caching."""
        # Include key attributes that define the element
        sig_parts = [
            element.get("tag", ""),
            element.get("text", ""),
            element.get("role", ""),
            element.get("name", ""),
            element.get("id", ""),
            str(element.get("classes", [])),
            element.get("placeholder", ""),
            element.get("type", ""),
            str(element.get("aria", {})),
        ]
        return json.dumps(sig_parts, sort_keys=True)
    
    def _element_to_text(self, element: Dict[str, Any]) -> str:
        """Convert element descriptor to text for embedding."""
        parts = []
        
        # Tag name
        if element.get("tag"):
            parts.append(f"tag:{element['tag']}")
        
        # Text content
        if element.get("text"):
            text = str(element["text"]).strip()[:100]  # Limit length
            if text:
                parts.append(f"text:{text}")
        
        # Role (accessibility)
        if element.get("role"):
            parts.append(f"role:{element['role']}")
        
        # Name (accessibility)
        if element.get("name"):
            parts.append(f"name:{element['name']}")
        
        # ID attribute
        if element.get("id"):
            parts.append(f"id:{element['id']}")
        
        # Classes
        if element.get("classes"):
            classes = element["classes"]
            if isinstance(classes, list):
                parts.append(f"classes:{' '.join(classes)}")
        
        # Placeholder
        if element.get("placeholder"):
            parts.append(f"placeholder:{element['placeholder']}")
        
        # Input type
        if element.get("type"):
            parts.append(f"type:{element['type']}")
        
        # ARIA attributes
        if element.get("aria"):
            aria = element["aria"]
            if isinstance(aria, dict):
                for key, value in aria.items():
                    parts.append(f"aria-{key}:{value}")
        
        # Labels
        if element.get("labels"):
            labels = element["labels"]
            if isinstance(labels, list):
                parts.append(f"labels:{' '.join(labels)}")
        
        # Combine all parts
        return " ".join(parts) if parts else "empty-element"