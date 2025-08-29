"""Real embedder implementation using sentence transformers."""

import hashlib
import json
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class RealEmbedder:
    """Real embedder using sentence transformers or fallback to deterministic vectors."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize embedder.
        
        Args:
            model_name: Name of the sentence transformer model
        """
        self.model_name = model_name
        self.model = None
        self.dimension = 384  # MiniLM dimension
        
        # Try to load sentence transformers
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name)
            logger.info(f"Loaded {model_name} model")
        except ImportError:
            logger.warning("sentence-transformers not available, using deterministic fallback")
        except Exception as e:
            logger.warning(f"Could not load model: {e}, using deterministic fallback")
    
    def embed_text(self, text: str) -> List[float]:
        """Embed text using model or deterministic fallback.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        if self.model is not None:
            try:
                # Use real model
                embedding = self.model.encode(text, convert_to_numpy=True)
                return embedding.tolist()
            except Exception as e:
                logger.debug(f"Model encoding failed: {e}")
        
        # Deterministic fallback based on text content
        return self._deterministic_embedding(text)
    
    def embed_element(self, element: Dict[str, Any]) -> List[float]:
        """Embed HTML element.
        
        Args:
            element: Element descriptor
            
        Returns:
            Embedding vector
        """
        # Create text representation of element
        text_parts = []
        
        # Add tag
        if element.get('tag'):
            text_parts.append(f"tag:{element['tag']}")
        
        # Add text content
        if element.get('text'):
            text_parts.append(f"text:{element['text']}")
        
        # Add important attributes
        for attr in ['id', 'name', 'placeholder', 'ariaLabel', 'dataTestId']:
            if element.get(attr):
                text_parts.append(f"{attr}:{element[attr]}")
        
        # Add type for inputs
        if element.get('type'):
            text_parts.append(f"type:{element['type']}")
        
        text = " ".join(text_parts)
        return self.embed_text(text)
    
    def _deterministic_embedding(self, text: str) -> List[float]:
        """Generate deterministic embedding from text.
        
        This creates a reproducible embedding based on text content.
        
        Args:
            text: Input text
            
        Returns:
            Deterministic embedding vector
        """
        # Hash the text for reproducibility
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        
        # Create base vector from hash
        vector = []
        for i in range(self.dimension):
            # Use different parts of hash for each dimension
            chunk = text_hash[i % len(text_hash):(i % len(text_hash)) + 2]
            # Convert to float in range [-1, 1]
            value = (int(chunk, 16) / 255.0) * 2 - 1
            vector.append(value)
        
        # Add some signal based on text content
        text_lower = text.lower()
        
        # Boost certain dimensions based on content
        if 'button' in text_lower:
            vector[0] += 0.5
        if 'input' in text_lower:
            vector[1] += 0.5
        if 'email' in text_lower:
            vector[2] += 0.5
        if 'password' in text_lower:
            vector[3] += 0.5
        if 'submit' in text_lower:
            vector[4] += 0.5
        if 'click' in text_lower:
            vector[5] += 0.5
        if 'type' in text_lower:
            vector[6] += 0.5
        if 'enter' in text_lower:
            vector[7] += 0.5
        
        # Add length signal
        vector[10] = len(text) / 100.0
        
        # Add word count signal
        vector[11] = len(text.split()) / 20.0
        
        # Normalize to unit length
        magnitude = sum(v * v for v in vector) ** 0.5
        if magnitude > 0:
            vector = [v / magnitude for v in vector]
        
        return vector


class MiniLMEmbedder(RealEmbedder):
    """MiniLM embedder for queries."""
    
    def __init__(self):
        """Initialize MiniLM embedder."""
        super().__init__("all-MiniLM-L6-v2")
        self.dimension = 384


class MarkupLMEmbedder(RealEmbedder):
    """MarkupLM embedder for HTML elements."""
    
    def __init__(self):
        """Initialize MarkupLM embedder."""
        # MarkupLM would need special handling, for now use MiniLM
        super().__init__("all-MiniLM-L6-v2")
        self.dimension = 384
    
    def embed_element(self, element: Dict[str, Any]) -> List[float]:
        """Embed HTML element with structure awareness.
        
        Args:
            element: Element descriptor
            
        Returns:
            Embedding vector
        """
        # Add structural information
        text_parts = []
        
        # Tag is important for MarkupLM
        if element.get('tag'):
            text_parts.append(f"<{element['tag']}>")
        
        # Add attributes in HTML-like format
        for attr in ['id', 'class', 'name', 'type']:
            if element.get(attr):
                text_parts.append(f'{attr}="{element[attr]}"')
        
        # Add text content
        if element.get('text'):
            text_parts.append(element['text'])
        
        # Close tag
        if element.get('tag'):
            text_parts.append(f"</{element['tag']}>")
        
        text = " ".join(text_parts)
        return self.embed_text(text)