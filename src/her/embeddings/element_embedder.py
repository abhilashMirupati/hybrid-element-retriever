"""Element embedding using markuplm-base model."""

from typing import Dict, Any, Optional, List
import numpy as np
import logging

from ._resolve import get_element_resolver
from .cache import EmbeddingCache
from ..config import ELEMENT_EMBEDDING_DIM

logger = logging.getLogger(__name__)


class ElementEmbedder:
    """Embeds UI elements using markuplm-base model with caching."""

    def __init__(self, cache_enabled: bool = True):
        """Initialize element embedder.

        Args:
            cache_enabled: Whether to use embedding cache
        """
        self.resolver = get_element_resolver()
        self.dim = ELEMENT_EMBEDDING_DIM
        self.cache = EmbeddingCache() if cache_enabled else None

    def _element_to_text(self, element: Dict[str, Any]) -> str:
        """Convert element descriptor to text representation.

        Args:
            element: Element descriptor dictionary

        Returns:
            Text representation for embedding
        """
        parts = []

        # Tag name is primary
        tag = element.get("tagName", "").lower()
        if tag:
            parts.append(f"<{tag}>")

        # Role from accessibility tree
        role = element.get("role", "")
        if role and role != tag:
            parts.append(f"role={role}")

        # Text content (visible text)
        text = element.get("text", "").strip()
        if text:
            # Truncate very long text
            if len(text) > 100:
                text = text[:97] + "..."
            parts.append(f'"{text}"')

        # Name from accessibility tree
        name = element.get("name", "").strip()
        if name and name != text:
            if len(name) > 50:
                name = name[:47] + "..."
            parts.append(f"name={name}")

        # Important attributes
        attrs = element.get("attributes", {})

        # ID
        elem_id = attrs.get("id", "")
        if elem_id:
            parts.append(f"#{elem_id}")

        # Classes
        classes = attrs.get("class", "")
        if classes:
            # Take first few classes
            class_list = classes.split()[:3]
            for cls in class_list:
                parts.append(f".{cls}")

        # Type for inputs
        elem_type = attrs.get("type", "")
        if elem_type and tag in ["input", "button"]:
            parts.append(f"type={elem_type}")

        # Placeholder
        placeholder = attrs.get("placeholder", "")
        if placeholder:
            if len(placeholder) > 30:
                placeholder = placeholder[:27] + "..."
            parts.append(f"placeholder={placeholder}")

        # ARIA label
        aria_label = attrs.get("aria-label", "")
        if aria_label and aria_label not in [text, name]:
            if len(aria_label) > 30:
                aria_label = aria_label[:27] + "..."
            parts.append(f"aria-label={aria_label}")

        # Value for form elements
        value = attrs.get("value", "")
        if value and tag in ["input", "select", "textarea"]:
            if len(value) > 30:
                value = value[:27] + "..."
            parts.append(f"value={value}")

        # href for links
        href = attrs.get("href", "")
        if href and tag == "a":
            if len(href) > 50:
                href = href[:47] + "..."
            parts.append(f"href={href}")

        # State information
        if element.get("disabled"):
            parts.append("disabled")
        if element.get("checked"):
            parts.append("checked")
        if element.get("selected"):
            parts.append("selected")
        if element.get("focused"):
            parts.append("focused")

        # Visibility
        if not element.get("visible", True):
            parts.append("hidden")

        # Join all parts
        return " ".join(parts)

    def embed(self, element: Dict[str, Any]) -> np.ndarray:
        """Generate embedding for UI element.

        Args:
            element: Element descriptor dictionary

        Returns:
            Normalized embedding vector of shape (dim,)
        """
        # Convert element to text representation
        text = self._element_to_text(element)

        if not text:
            return np.zeros(self.dim, dtype=np.float32)

        # Create cache key from element
        cache_key = self._get_cache_key(element)

        # Check cache first
        if self.cache and cache_key:
            cached = self.cache.get(cache_key)
            if cached is not None:
                logger.debug(f"Cache hit for element: {text[:50]}")
                return cached

        # Generate embedding
        logger.debug(f"Generating embedding for element: {text[:50]}")

        # For markuplm-base, we can provide HTML-like structure
        # The model is trained on markup, so preserve structure
        embedding = self.resolver.embed(text, normalize=True)

        # Cache the result
        if self.cache and cache_key:
            self.cache.put(cache_key, embedding)

        return embedding

    def batch_embed(self, elements: List[Dict[str, Any]]) -> np.ndarray:
        """Generate embeddings for multiple elements.

        Args:
            elements: List of element descriptors

        Returns:
            Array of shape (n_elements, dim)
        """
        if not elements:
            return np.array([], dtype=np.float32).reshape(0, self.dim)

        embeddings = []
        for element in elements:
            embeddings.append(self.embed(element))

        return np.vstack(embeddings)

    def _get_cache_key(self, element: Dict[str, Any]) -> Optional[str]:
        """Generate cache key for element.

        Args:
            element: Element descriptor

        Returns:
            Cache key string or None if element is not cacheable
        """
        # Use a subset of stable attributes for cache key
        key_parts = []

        # Tag name
        tag = element.get("tagName", "")
        if tag:
            key_parts.append(f"tag:{tag}")

        # Text content
        text = element.get("text", "")[:100]  # Truncate for key
        if text:
            key_parts.append(f"text:{text}")

        # Important attributes
        attrs = element.get("attributes", {})

        # ID is very stable
        elem_id = attrs.get("id", "")
        if elem_id:
            key_parts.append(f"id:{elem_id}")

        # Role
        role = element.get("role", "")
        if role:
            key_parts.append(f"role:{role}")

        # Name from accessibility
        name = element.get("name", "")[:50]
        if name:
            key_parts.append(f"name:{name}")

        if not key_parts:
            return None

        return "|".join(key_parts)
    
    def embed_batch(self, elements: List[Dict[str, Any]]) -> List[np.ndarray]:
        """Generate embeddings for multiple elements.
        
        Args:
            elements: List of element descriptors
        
        Returns:
            List of embedding vectors
        """
        return [self.embed(elem) for elem in elements]
