"""Query embedder using E5-small ONNX model."""

import hashlib
import logging
import numpy as np
from typing import Optional, List, Dict, Any
from pathlib import Path

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

logger = logging.getLogger(__name__)


class QueryEmbedder:
    """Embeds user queries using E5-small ONNX model or deterministic fallback."""
    
    def __init__(self, use_fallback: bool = False):
        self.use_fallback = use_fallback or not ONNX_AVAILABLE or not TRANSFORMERS_AVAILABLE
        self.model_path: Optional[Path] = None
        self.model_info: Optional[Dict] = None
        self.session: Optional[Any] = None
        self.tokenizer: Optional[Any] = None
        self.dimension = 384  # E5-small dimension
        
        if not self.use_fallback:
            self._initialize_model()
            
    def _initialize_model(self) -> None:
        """Initialize ONNX model and tokenizer."""
        try:
            resolver = ModelResolver()
            self.model_path, self.model_info = resolver.get_query_embedder_info()
            
            if not self.model_path or not self.model_path.exists():
                logger.warning("Query embedder model not found, using fallback")
                self.use_fallback = True
                return
                
            # Load ONNX model
            providers = ['CPUExecutionProvider']
            self.session = ort.InferenceSession(str(self.model_path), providers=providers)
            logger.info(f"Loaded query embedder from {self.model_path}")
            
            # Load tokenizer
            tokenizer_name = self.model_info.get('tokenizer', 'sentence-transformers/all-MiniLM-L6-v2')
            self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
            
            # Update dimension from model info
            self.dimension = self.model_info.get('dimension', 384)
            
        except Exception as e:
            logger.error(f"Failed to initialize query embedder: {e}")
            self.use_fallback = True
            
    def embed(self, query: str) -> np.ndarray:
        """Embed a single query.
        
        Args:
            query: User query text
            
        Returns:
            Embedding vector of shape (dimension,)
        """
        if self.use_fallback:
            return self._fallback_embed(query)
            
        try:
            # Tokenize
            inputs = self.tokenizer(
                query,
                padding=True,
                truncation=True,
                max_length=self.model_info.get('max_tokens', 512),
                return_tensors='np'
            )
            
            # Run inference
            outputs = self.session.run(
                None,
                {
                    'input_ids': inputs['input_ids'],
                    'attention_mask': inputs['attention_mask']
                }
            )
            
            # Pool outputs (mean pooling)
            embeddings = outputs[0]
            attention_mask = inputs['attention_mask']
            
            # Expand attention mask for broadcasting
            mask_expanded = np.expand_dims(attention_mask, -1)
            mask_expanded = np.broadcast_to(mask_expanded, embeddings.shape)
            
            # Apply mask and mean pool
            sum_embeddings = np.sum(embeddings * mask_expanded, axis=1)
            sum_mask = np.clip(mask_expanded.sum(axis=1), a_min=1e-9, a_max=None)
            mean_pooled = sum_embeddings / sum_mask
            
            # Normalize
            norm = np.linalg.norm(mean_pooled, axis=1, keepdims=True)
            normalized = mean_pooled / np.clip(norm, a_min=1e-9, a_max=None)
            
            return normalized[0]
            
        except Exception as e:
            logger.warning(f"Failed to embed query with model: {e}")
            return self._fallback_embed(query)
            
    def _fallback_embed(self, query: str) -> np.ndarray:
        """Deterministic hash-based fallback embedding.
        
        Args:
            query: User query text
            
        Returns:
            Deterministic embedding vector
        """
        # Create deterministic hash
        hash_obj = hashlib.sha256(query.encode())
        hash_bytes = hash_obj.digest()
        
        # Convert to float array
        embedding = np.frombuffer(hash_bytes, dtype=np.uint8).astype(np.float32)
        
        # Pad or truncate to dimension
        if len(embedding) < self.dimension:
            embedding = np.pad(embedding, (0, self.dimension - len(embedding)))
        else:
            embedding = embedding[:self.dimension]
            
        # Add some structure based on query tokens
        tokens = query.lower().split()
        for i, token in enumerate(tokens[:10]):
            token_hash = hashlib.md5(token.encode()).digest()[0]
            idx = (i * 37 + token_hash) % self.dimension
            embedding[idx] += 0.5
            
        # Normalize to unit vector
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
            
        return embedding
        
    def batch_embed(self, queries: List[str]) -> np.ndarray:
        """Embed multiple queries.
        
        Args:
            queries: List of query texts
            
        Returns:
            Array of shape (n_queries, dimension)
        """
        embeddings = []
        for query in queries:
            embeddings.append(self.embed(query))
        return np.array(embeddings)
        
    def get_dimension(self) -> int:
        """Get embedding dimension.
        
        Returns:
            Embedding vector dimension
        """
        return self.dimension