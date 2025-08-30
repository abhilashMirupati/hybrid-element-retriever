# archived duplicate of src/her/embeddings/element_embedder.py
"""Element embedder using MarkupLM-base ONNX model."""

import hashlib
import logging
import numpy as np
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
from dataclasses import dataclass

try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False
    
try:
    from transformers import AutoTokenizer
    TRANSFORMERS_AVAILABLE = True  
except ImportError:
    TRANSFORMERS_AVAILABLE = False

from her.embeddings._resolve import ModelResolver
from her.bridge.snapshot import DOMNode

logger = logging.getLogger(__name__)


@dataclass
class ElementEmbedding:
    """Element embedding result."""
    node_id: int
    backend_node_id: int
    embedding: np.ndarray
    text_repr: str
    is_cached: bool = False
    

class ElementEmbedder:
    """Embeds DOM elements using MarkupLM-base ONNX model."""
    
    def __init__(self, use_fallback: bool = False):
        self.use_fallback = use_fallback or not ONNX_AVAILABLE or not TRANSFORMERS_AVAILABLE
        self.model_path: Optional[Path] = None
        self.model_info: Optional[Dict] = None
        self.session: Optional[Any] = None
        self.tokenizer: Optional[Any] = None
        self.dimension = 768  # MarkupLM-base dimension
        self._embedding_cache: Dict[str, np.ndarray] = {}
        
        if not self.use_fallback:
            self._initialize_model()
            
    def _initialize_model(self) -> None:
        """Initialize ONNX model and tokenizer."""
        try:
            resolver = ModelResolver()
            self.model_path, self.model_info = resolver.get_element_embedder_info()
            
            if not self.model_path or not self.model_path.exists():
                logger.warning("Element embedder model not found, using fallback")
                self.use_fallback = True
                return
                
            # Load ONNX model
            providers = ['CPUExecutionProvider']
            self.session = ort.InferenceSession(str(self.model_path), providers=providers)
            logger.info(f"Loaded element embedder from {self.model_path}")
            
            # Load tokenizer
            tokenizer_name = self.model_info.get('tokenizer', 'microsoft/markuplm-base')
            self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
            
            # Update dimension from model info
            self.dimension = self.model_info.get('dimension', 768)
            
        except Exception as e:
            logger.error(f"Failed to initialize element embedder: {e}")
            self.use_fallback = True
            
    def embed_element(self, node: DOMNode) -> ElementEmbedding:
        """Embed a single DOM element.
        
        Args:
            node: DOM node to embed
            
        Returns:
            ElementEmbedding result
        """
        # Create text representation
        text_repr = self._create_text_representation(node)
        
        # Check cache
        cache_key = f"{node.backend_node_id}:{hashlib.md5(text_repr.encode()).hexdigest()}"
        if cache_key in self._embedding_cache:
            return ElementEmbedding(
                node_id=node.node_id,
                backend_node_id=node.backend_node_id,
                embedding=self._embedding_cache[cache_key],
                text_repr=text_repr,
                is_cached=True
            )
            
        # Generate embedding
        if self.use_fallback:
            embedding = self._fallback_embed(node, text_repr)
        else:
            embedding = self._model_embed(node, text_repr)
            
        # Cache result
        self._embedding_cache[cache_key] = embedding
        
        # Limit cache size
        if len(self._embedding_cache) > 10000:
            # Remove oldest entries
            keys_to_remove = list(self._embedding_cache.keys())[:1000]
            for key in keys_to_remove:
                del self._embedding_cache[key]
                
        return ElementEmbedding(
            node_id=node.node_id,
            backend_node_id=node.backend_node_id,
            embedding=embedding,
            text_repr=text_repr,
            is_cached=False
        )
        
    def _create_text_representation(self, node: DOMNode) -> str:
        """Create text representation of element for embedding.
        
        Args:
            node: DOM node
            
        Returns:
            Text representation
        """
        parts = []
        
        # Node name
        parts.append(node.node_name.lower())
        
        # Key attributes
        if node.attributes:
            # ID
            if 'id' in node.attributes:
                parts.append(f"id={node.attributes['id']}")
            # Class
            if 'class' in node.attributes:
                classes = node.attributes['class'].split()[:3]  # Limit classes
                parts.append(f"class={' '.join(classes)}")
            # Type (for inputs)
            if 'type' in node.attributes:
                parts.append(f"type={node.attributes['type']}")
            # Name
            if 'name' in node.attributes:
                parts.append(f"name={node.attributes['name']}")
            # Placeholder
            if 'placeholder' in node.attributes:
                parts.append(f"placeholder={node.attributes['placeholder']}")
                
        # ARIA attributes
        if node.aria_label:
            parts.append(f"aria-label={node.aria_label}")
        if node.role:
            parts.append(f"role={node.role}")
            
        # Text content
        if node.text_content:
            text = node.text_content.strip()[:100]  # Limit length
            if text:
                parts.append(f"text={text}")
                
        # Input value
        if node.input_value:
            parts.append(f"value={node.input_value[:50]}")
            
        return " ".join(parts)
        
    def _model_embed(self, node: DOMNode, text_repr: str) -> np.ndarray:
        """Embed using MarkupLM model.
        
        Args:
            node: DOM node
            text_repr: Text representation
            
        Returns:
            Embedding vector
        """
        try:
            # Tokenize text
            inputs = self.tokenizer(
                text_repr,
                padding=True,
                truncation=True,
                max_length=self.model_info.get('max_tokens', 512),
                return_tensors='np'
            )
            
            # Create dummy XPath features (MarkupLM expects these)
            batch_size = inputs['input_ids'].shape[0]
            seq_length = inputs['input_ids'].shape[1]
            xpath_tags_seq = np.zeros((batch_size, seq_length, 50), dtype=np.int64)
            xpath_subs_seq = np.zeros((batch_size, seq_length, 50), dtype=np.int64)
            
            # Run inference
            outputs = self.session.run(
                None,
                {
                    'input_ids': inputs['input_ids'],
                    'attention_mask': inputs['attention_mask'],
                    'xpath_tags_seq': xpath_tags_seq,
                    'xpath_subs_seq': xpath_subs_seq
                }
            )
            
            # Pool outputs
            embeddings = outputs[0]
            attention_mask = inputs['attention_mask']
            
            # Mean pooling with attention mask
            mask_expanded = np.expand_dims(attention_mask, -1)
            mask_expanded = np.broadcast_to(mask_expanded, embeddings.shape)
            
            sum_embeddings = np.sum(embeddings * mask_expanded, axis=1)
            sum_mask = np.clip(mask_expanded.sum(axis=1), a_min=1e-9, a_max=None)
            mean_pooled = sum_embeddings / sum_mask
            
            # Normalize
            norm = np.linalg.norm(mean_pooled, axis=1, keepdims=True)
            normalized = mean_pooled / np.clip(norm, a_min=1e-9, a_max=None)
            
            return normalized[0]
            
        except Exception as e:
            logger.warning(f"Failed to embed element with model: {e}")
            return self._fallback_embed(node, text_repr)
            
    def _fallback_embed(self, node: DOMNode, text_repr: str) -> np.ndarray:
        """Deterministic fallback embedding.
        
        Args:
            node: DOM node
            text_repr: Text representation
            
        Returns:
            Embedding vector
        """
        # Base hash from text representation
        hash_obj = hashlib.sha256(text_repr.encode())
        hash_bytes = hash_obj.digest()
        
        # Convert to float array
        embedding = np.frombuffer(hash_bytes, dtype=np.uint8).astype(np.float32)
        
        # Pad or truncate to dimension
        if len(embedding) < self.dimension:
            embedding = np.pad(embedding, (0, self.dimension - len(embedding)))
        else:
            embedding = embedding[:self.dimension]
            
        # Add structural features
        features = [
            ('tag', node.node_name.lower(), 0.3),
            ('id', node.attributes.get('id', ''), 0.2),
            ('class', node.attributes.get('class', ''), 0.2),
            ('role', node.role or '', 0.2),
            ('visible', str(node.is_visible), 0.1),
            ('clickable', str(node.is_clickable), 0.1),
        ]
        
        for feature_name, feature_value, weight in features:
            if feature_value:
                feature_hash = hashlib.md5(f"{feature_name}:{feature_value}".encode()).digest()
                for i in range(min(10, len(feature_hash))):
                    idx = (feature_hash[i] * 7 + i) % self.dimension
                    embedding[idx] += weight
                    
        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
            
        return embedding
        
    def batch_embed(self, nodes: List[DOMNode]) -> List[ElementEmbedding]:
        """Embed multiple elements.
        
        Args:
            nodes: List of DOM nodes
            
        Returns:
            List of ElementEmbedding results
        """
        embeddings = []
        for node in nodes:
            embeddings.append(self.embed_element(node))
        return embeddings
        
    def embed_delta(self, old_nodes: List[DOMNode], new_nodes: List[DOMNode]) -> Tuple[List[ElementEmbedding], int]:
        """Embed only changed elements between snapshots.
        
        Args:
            old_nodes: Previous snapshot nodes
            new_nodes: Current snapshot nodes
            
        Returns:
            Tuple of (embeddings for new/changed nodes, number of reused embeddings)
        """
        # Create lookup for old nodes
        old_lookup = {n.backend_node_id: n for n in old_nodes}
        
        embeddings = []
        reused_count = 0
        
        for node in new_nodes:
            # Check if node existed before
            old_node = old_lookup.get(node.backend_node_id)
            
            if old_node:
                # Check if node changed
                old_repr = self._create_text_representation(old_node)
                new_repr = self._create_text_representation(node)
                
                if old_repr == new_repr:
                    # Reuse cached embedding if available
                    cache_key = f"{node.backend_node_id}:{hashlib.md5(new_repr.encode()).hexdigest()}"
                    if cache_key in self._embedding_cache:
                        reused_count += 1
                        continue
                        
            # Embed new/changed node
            embeddings.append(self.embed_element(node))
            
        return embeddings, reused_count
        
    def clear_cache(self) -> None:
        """Clear embedding cache."""
        self._embedding_cache.clear()
        logger.info("Cleared element embedding cache")
        
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        return {
            "cache_size": len(self._embedding_cache),
            "dimension": self.dimension,
            "using_fallback": self.use_fallback
        }