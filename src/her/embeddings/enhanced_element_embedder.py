"""Enhanced element embedder with partial embedding support and caching."""

from typing import Dict, Any, List, Optional, Set, Tuple
import hashlib
import logging

from .element_embedder import ElementEmbedder
from ..vectordb.sqlite_cache import SQLiteKV

logger = logging.getLogger(__name__)


class EnhancedElementEmbedder(ElementEmbedder):
    """Element embedder with delta tracking and batch operations."""
    
    def __init__(self, cache_path: Optional[str] = None, cache_enabled: bool = True):
        """Initialize enhanced embedder.
        
        Args:
            cache_path: Path to SQLite cache
            cache_enabled: Whether to use caching
        """
        super().__init__(cache_enabled=cache_enabled)
        
        # Initialize SQLite cache for persistent storage
        self.sqlite_cache = SQLiteKV(cache_path) if cache_path else None
        self.embedded_hashes: Dict[str, Set[str]] = {}
    
    def embed_partial(
        self,
        session_id: str,
        elements: List[Dict[str, Any]],
        force_all: bool = False
    ) -> Tuple[Dict[str, List[float]], List[str]]:
        """Embed only new/changed elements.
        
        Args:
            session_id: Session identifier
            elements: All current elements
            force_all: Force embedding of all elements
            
        Returns:
            Tuple of (all_embeddings, new_element_hashes)
        """
        all_embeddings = {}
        new_hashes = []
        
        # Calculate hashes for all elements
        element_hashes = {}
        for elem in elements:
            elem_hash = self._element_hash(elem)
            element_hashes[elem_hash] = elem
        
        # Get previously embedded hashes for this session
        prev_hashes = self.embedded_hashes.get(session_id, set())
        
        if force_all:
            # Embed all elements
            to_embed = element_hashes
            new_hashes = list(element_hashes.keys())
        else:
            # Find new elements
            to_embed = {}
            for elem_hash, elem in element_hashes.items():
                if elem_hash not in prev_hashes:
                    to_embed[elem_hash] = elem
                    new_hashes.append(elem_hash)
        
        # Try to get cached embeddings first
        if self.sqlite_cache and not force_all:
            cached = self.sqlite_cache.batch_get_embeddings(list(element_hashes.keys()))
            for elem_hash, embedding in cached.items():
                all_embeddings[elem_hash] = embedding
                # Remove from to_embed if found in cache
                to_embed.pop(elem_hash, None)
        
        # Embed new elements
        if to_embed:
            logger.info(f"Embedding {len(to_embed)} new elements for session {session_id}")
            
            new_embeddings = {}
            for elem_hash, elem in to_embed.items():
                try:
                    embedding = self.embed(elem)
                    # Convert to list if needed
                    if hasattr(embedding, 'tolist'):
                        embedding = embedding.tolist()
                    elif not isinstance(embedding, list):
                        embedding = list(embedding)
                    
                    new_embeddings[elem_hash] = embedding
                    all_embeddings[elem_hash] = embedding
                except Exception as e:
                    logger.warning(f"Failed to embed element: {e}")
            
            # Cache new embeddings
            if self.sqlite_cache and new_embeddings:
                self.sqlite_cache.batch_put_embeddings(new_embeddings)
        
        # Update tracked hashes
        self.embedded_hashes[session_id] = set(element_hashes.keys())
        
        logger.info(f"Session {session_id}: {len(all_embeddings)} total, {len(new_hashes)} new")
        
        return all_embeddings, new_hashes
    
    def _element_hash(self, element: Dict[str, Any]) -> str:
        """Calculate stable hash for element."""
        # Create signature from stable attributes
        sig_parts = [
            element.get('tag', ''),
            element.get('id', ''),
            element.get('dataTestId', ''),
            element.get('ariaLabel', ''),
            str(element.get('text', '')[:100]),  # Limit text length
            element.get('frame_path', 'main')
        ]
        
        signature = '|'.join(str(p) for p in sig_parts)
        return hashlib.md5(signature.encode()).hexdigest()
    
    def get_embedding_stats(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get embedding statistics.
        
        Args:
            session_id: Optional session to get stats for
            
        Returns:
            Dictionary of statistics
        """
        stats = {
            'total_sessions': len(self.embedded_hashes),
            'total_embedded': sum(len(h) for h in self.embedded_hashes.values())
        }
        
        if session_id and session_id in self.embedded_hashes:
            stats['session_embedded'] = len(self.embedded_hashes[session_id])
        
        if self.sqlite_cache:
            cache_stats = self.sqlite_cache.get_stats()
            stats['cache_embeddings'] = cache_stats.get('embedding_entries', 0)
            stats['cache_hit_rate'] = cache_stats.get('hit_rate', 0.0)
        
        return stats
    
    def clear_session(self, session_id: str) -> None:
        """Clear embeddings for a session.
        
        Args:
            session_id: Session to clear
        """
        self.embedded_hashes.pop(session_id, None)