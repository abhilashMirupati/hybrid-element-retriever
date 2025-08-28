from __future__ import annotations
from typing import Dict, Any, List, Optional
import numpy as np

from .cache import EmbeddingCache
from ._resolve import get_element_resolver, ONNXModelResolver
from ..utils import sha1_of  # type: ignore


class ElementEmbedder:
    """Element embedder that converts descriptors to text then embeds.

    API used by tests:
      - embed(element_dict) -> np.ndarray
      - embed_batch(list_of_elements) -> List[np.ndarray]
      - _element_to_text(element_dict) -> str
    """

    def __init__(self, cache: Optional[EmbeddingCache] = None, resolver: Optional[ONNXModelResolver] = None) -> None:
        self.cache = cache or EmbeddingCache()
        self.resolver = resolver or get_element_resolver()
        self.dim = int(self.resolver.embedding_dim)

    def _key(self, text: str) -> str:
        return f"e|{sha1_of(text)}|{self.dim}"

    def _element_to_text(self, element: Dict[str, Any]) -> str:
        parts: List[str] = []
        tag = element.get('tag') or element.get('tagName') or '*'
        parts.append(f"tag:{tag}")
        for k in ('id','name','type','role','text','placeholder','href'):
            v = element.get(k)
            if v:
                parts.append(f"{k}:{v}")
        # Attributes map
        attrs = element.get('attributes', {}) or {}
        for k in ('aria-label','data-testid','data-test','data-qa','class'):
            v = attrs.get(k)
            if v:
                parts.append(f"{k}:{v}")
        # ARIA
        aria = element.get('aria', {}) or {}
        for k, v in aria.items():
            if v:
                parts.append(f"aria-{k}:{v}")
        # classes list
        classes = element.get('classes') or []
        if classes:
            parts.append("classes:"+"|".join(classes))
        return " ".join(parts)

    def embed(self, element: Dict[str, Any]) -> np.ndarray:
        text = self._element_to_text(element)
        key = self._key(text)
        hit = self.cache.get(key)
        if hit is not None:
            return hit.astype('float32')
        vec = self.resolver.embed(text).astype('float32')
        self.cache.put(key, vec)
        return vec

    def embed_batch(self, elements: List[Dict[str, Any]]) -> List[np.ndarray]:
        return [self.embed(e) for e in elements]
