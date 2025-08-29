"""Fallback embedders that work without numpy/ONNX dependencies."""

import hashlib
import math
from typing import List, Dict, Any, Optional


class FallbackQueryEmbedder:
    """Fallback query embedder using deterministic hashing when numpy not available."""
    
    def __init__(self, dim: int = 384):
        self.dim = dim
        self.cache = {}
    
    def embed(self, text: str) -> List[float]:
        """Generate deterministic embedding from text using hashing."""
        if text in self.cache:
            return self.cache[text]
        
        # Create deterministic pseudo-embedding from text
        embedding = []
        
        # Use multiple hash functions for different dimensions
        for i in range(self.dim):
            # Create unique hash for each dimension
            hash_input = f"{text}:dim{i}"
            hash_bytes = hashlib.sha256(hash_input.encode()).digest()
            
            # Convert bytes to float in range [-1, 1]
            value = 0.0
            for j in range(min(4, len(hash_bytes))):
                value += hash_bytes[j] / 256.0
            
            # Normalize to [-1, 1]
            value = (value - 0.5) * 2.0
            
            # Add some structure based on text features
            if i < self.dim // 3:
                # First third: character-based features
                char_sum = sum(ord(c) for c in text[:10]) if text else 0
                value *= math.sin(char_sum / 100.0 + i)
            elif i < 2 * self.dim // 3:
                # Second third: word-based features
                word_count = len(text.split())
                value *= math.cos(word_count + i)
            else:
                # Last third: semantic hints
                if any(action in text.lower() for action in ['click', 'button', 'submit']):
                    value *= 1.5
                if any(form in text.lower() for form in ['input', 'field', 'text', 'email']):
                    value *= 0.7
            
            embedding.append(value)
        
        # Normalize
        norm = math.sqrt(sum(v * v for v in embedding))
        if norm > 0:
            embedding = [v / norm for v in embedding]
        
        self.cache[text] = embedding
        return embedding
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts."""
        return [self.embed(text) for text in texts]
    
    @staticmethod
    def similarity(vec1: List[float], vec2: List[float]) -> float:
        """Compute cosine similarity between vectors."""
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        
        if norm1 * norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)


class FallbackElementEmbedder:
    """Fallback element embedder using feature extraction when numpy not available."""
    
    def __init__(self, dim: int = 768):
        self.dim = dim
        self.cache = {}
    
    def embed(self, descriptor: Dict[str, Any]) -> List[float]:
        """Generate embedding from element descriptor."""
        # Create cache key
        cache_key = self._descriptor_key(descriptor)
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        embedding = []
        
        # Extract features
        tag = descriptor.get('tag', descriptor.get('tagName', 'unknown'))
        text = descriptor.get('text', '')
        elem_id = descriptor.get('id', '')
        classes = descriptor.get('classes', [])
        attributes = descriptor.get('attributes', {})
        
        # Generate embedding dimensions
        for i in range(self.dim):
            value = 0.0
            
            # Tag-based features (first quarter)
            if i < self.dim // 4:
                tag_hash = hashlib.md5(f"{tag}:{i}".encode()).hexdigest()
                value = (int(tag_hash[:8], 16) / 0xFFFFFFFF - 0.5) * 2
                
                # Boost important tags
                if tag in ['button', 'input', 'a', 'form']:
                    value *= 1.5
                elif tag in ['div', 'span']:
                    value *= 0.7
            
            # Text-based features (second quarter)
            elif i < self.dim // 2:
                if text:
                    text_hash = hashlib.md5(f"{text}:{i}".encode()).hexdigest()
                    value = (int(text_hash[:8], 16) / 0xFFFFFFFF - 0.5) * 2
                    
                    # Boost action words
                    if any(word in text.lower() for word in ['submit', 'click', 'save', 'continue']):
                        value *= 1.3
            
            # ID/class features (third quarter)
            elif i < 3 * self.dim // 4:
                if elem_id:
                    id_hash = hashlib.md5(f"{elem_id}:{i}".encode()).hexdigest()
                    value = (int(id_hash[:8], 16) / 0xFFFFFFFF - 0.5) * 2
                    value *= 1.2  # IDs are usually important
                elif classes:
                    class_str = ' '.join(classes) if isinstance(classes, list) else str(classes)
                    class_hash = hashlib.md5(f"{class_str}:{i}".encode()).hexdigest()
                    value = (int(class_hash[:8], 16) / 0xFFFFFFFF - 0.5) * 2
            
            # Attribute features (last quarter)
            else:
                if attributes:
                    attr_str = str(sorted(attributes.items()))
                    attr_hash = hashlib.md5(f"{attr_str}:{i}".encode()).hexdigest()
                    value = (int(attr_hash[:8], 16) / 0xFFFFFFFF - 0.5) * 2
                    
                    # Boost accessibility attributes
                    if any(k.startswith('aria-') for k in attributes.keys()):
                        value *= 1.2
                    if 'role' in attributes:
                        value *= 1.1
            
            embedding.append(value)
        
        # Normalize
        norm = math.sqrt(sum(v * v for v in embedding))
        if norm > 0:
            embedding = [v / norm for v in embedding]
        
        self.cache[cache_key] = embedding
        return embedding
    
    def embed_batch(self, descriptors: List[Dict[str, Any]]) -> List[List[float]]:
        """Embed multiple descriptors."""
        return [self.embed(desc) for desc in descriptors]
    
    def _descriptor_key(self, descriptor: Dict[str, Any]) -> str:
        """Create cache key for descriptor."""
        key_parts = [
            descriptor.get('tag', ''),
            descriptor.get('id', ''),
            descriptor.get('text', '')[:50],  # Limit text length
            str(descriptor.get('attributes', {}))
        ]
        return '|'.join(key_parts)


class FallbackEmbedder:
    """Compatibility facade exposing simple text embed for tests."""

    def __init__(self, dim: int = 384):
        self._qe = FallbackQueryEmbedder(dim=dim)

    def embed(self, text: str) -> List[float]:
        return self._qe.embed(text)