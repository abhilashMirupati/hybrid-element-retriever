"""Fusion-based ranking combining semantic and heuristic scores."""

import logging
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from scipy.spatial.distance import cosine

from her.bridge.snapshot import DOMNode
from her.embeddings.element_embedder import ElementEmbedding

logger = logging.getLogger(__name__)


@dataclass
class RankingResult:
    """Result of ranking a single element."""
    node: DOMNode
    semantic_score: float
    heuristic_score: float
    promotion_score: float
    final_score: float
    rank: int
    explanation: str
    

class FusionRanker:
    """Combines semantic embeddings with robust heuristics for ranking.
    
    Uses weighted fusion:
    - α (alpha): Weight for semantic similarity (default 1.0)
    - β (beta): Weight for robust CSS heuristics (default 0.5)
    - γ (gamma): Weight for promotion/self-heal (default 0.2)
    
    Ensures semantic scores materially affect ranking (non-rule-based).
    """
    
    def __init__(
        self,
        alpha: float = 1.0,
        beta: float = 0.5,
        gamma: float = 0.2
    ):
        self.alpha = alpha  # Semantic weight
        self.beta = beta   # Heuristic weight
        self.gamma = gamma  # Promotion weight
        
        # Ensure semantic has highest weight (non-rule-based requirement)
        if self.alpha < max(self.beta, self.gamma):
            logger.warning("Semantic weight (alpha) should be highest for non-rule-based ranking")
            
    def rank(
        self,
        query_embedding: np.ndarray,
        element_embeddings: List[ElementEmbedding],
        nodes: List[DOMNode],
        query_text: str,
        promotion_scores: Optional[Dict[int, float]] = None
    ) -> List[RankingResult]:
        """Rank elements using fusion scoring.
        
        Args:
            query_embedding: Query vector
            element_embeddings: Element vectors
            nodes: DOM nodes corresponding to embeddings
            query_text: Original query text
            promotion_scores: Optional promotion scores from self-heal
            
        Returns:
            Sorted list of RankingResult (best first)
        """
        if not element_embeddings:
            return []
            
        # Ensure alignment
        assert len(element_embeddings) == len(nodes), "Embeddings and nodes must align"
        
        results = []
        
        for i, (elem_emb, node) in enumerate(zip(element_embeddings, nodes)):
            # 1. Semantic similarity score
            semantic_score = self._compute_semantic_score(
                query_embedding,
                elem_emb.embedding
            )
            
            # 2. Heuristic score (robust CSS features)
            heuristic_score = self._compute_heuristic_score(
                node,
                query_text
            )
            
            # 3. Promotion score (from self-heal/history)
            promotion_score = 0.0
            if promotion_scores and node.backend_node_id in promotion_scores:
                promotion_score = promotion_scores[node.backend_node_id]
                
            # 4. Fusion (weighted combination)
            raw_score = (
                self.alpha * semantic_score +
                self.beta * heuristic_score +
                self.gamma * promotion_score
            )
            
            # Normalize to [0, 1]
            max_possible = self.alpha + self.beta + self.gamma
            final_score = raw_score / max_possible if max_possible > 0 else 0
            
            # Create explanation
            explanation = self._create_explanation(
                semantic_score,
                heuristic_score,
                promotion_score,
                final_score
            )
            
            results.append(RankingResult(
                node=node,
                semantic_score=semantic_score,
                heuristic_score=heuristic_score,
                promotion_score=promotion_score,
                final_score=final_score,
                rank=0,  # Will be set after sorting
                explanation=explanation
            ))
            
        # Sort by final score (descending)
        results.sort(key=lambda r: r.final_score, reverse=True)
        
        # Assign ranks
        for i, result in enumerate(results):
            result.rank = i + 1
            
        # Log top results
        if results:
            top = results[0]
            logger.debug(
                f"Top ranked: {top.node.node_name} "
                f"(semantic={top.semantic_score:.3f}, "
                f"heuristic={top.heuristic_score:.3f}, "
                f"final={top.final_score:.3f})"
            )
            
        return results
        
    def _compute_semantic_score(
        self,
        query_embedding: np.ndarray,
        element_embedding: np.ndarray
    ) -> float:
        """Compute semantic similarity score.
        
        Args:
            query_embedding: Query vector
            element_embedding: Element vector
            
        Returns:
            Similarity score in [0, 1]
        """
        # Cosine similarity
        similarity = 1.0 - cosine(query_embedding, element_embedding)
        
        # Ensure in [0, 1] range
        return max(0.0, min(1.0, similarity))
        
    def _compute_heuristic_score(
        self,
        node: DOMNode,
        query_text: str
    ) -> float:
        """Compute heuristic score based on robust CSS features.
        
        Penalizes:
        - Hash-like IDs/classes
        - Deeply nested elements
        - Hidden/disabled elements
        
        Rewards:
        - Semantic HTML tags
        - ARIA labels matching query
        - Visible, clickable elements
        
        Args:
            node: DOM node
            query_text: Query text
            
        Returns:
            Heuristic score in [0, 1]
        """
        score = 0.5  # Start neutral
        
        # Parse query for better matching
        query_lower = query_text.lower()
        query_tokens = set(query_lower.split())
        
        # 1. Semantic HTML bonus
        semantic_tags = {
            'button': 0.3,
            'a': 0.2,
            'input': 0.2,
            'select': 0.2,
            'textarea': 0.2,
            'form': 0.1,
            'nav': 0.1,
            'main': 0.1,
            'header': 0.1,
            'footer': 0.1
        }
        tag_name = node.node_name.lower()
        if tag_name in semantic_tags:
            score += semantic_tags[tag_name]
            
        # 2. Check attributes
        if node.attributes:
            # Penalize hash-like IDs
            if 'id' in node.attributes:
                id_val = node.attributes['id']
                if self._is_hash_like(id_val):
                    score -= 0.2
                elif any(token in id_val.lower() for token in query_tokens):
                    score += 0.2
                    
            # Penalize hash-like classes
            if 'class' in node.attributes:
                classes = node.attributes['class'].split()
                hash_classes = sum(1 for c in classes if self._is_hash_like(c))
                if hash_classes > 0:
                    score -= 0.1 * min(hash_classes, 3)
                    
                # Bonus for matching classes
                for cls in classes:
                    if any(token in cls.lower() for token in query_tokens):
                        score += 0.1
                        break
                        
            # Check type attribute for inputs
            if 'type' in node.attributes:
                input_type = node.attributes['type'].lower()
                if input_type in ['submit', 'button'] and 'submit' in query_tokens:
                    score += 0.2
                elif input_type == 'email' and 'email' in query_tokens:
                    score += 0.3
                elif input_type == 'password' and 'password' in query_tokens:
                    score += 0.3
                    
        # 3. ARIA and role matching
        if node.aria_label:
            label_lower = node.aria_label.lower()
            matching_tokens = sum(1 for token in query_tokens if token in label_lower)
            if matching_tokens > 0:
                score += 0.3 * (matching_tokens / len(query_tokens))
                
        if node.role:
            if node.role.lower() in query_lower:
                score += 0.2
                
        # 4. Text content matching
        if node.text_content:
            text_lower = node.text_content.lower()
            matching_tokens = sum(1 for token in query_tokens if token in text_lower)
            if matching_tokens > 0:
                score += 0.2 * (matching_tokens / len(query_tokens))
                
        # 5. Visibility and interaction penalties/bonuses
        if not node.is_visible:
            score *= 0.3  # Heavy penalty for hidden
        if node.is_clickable:
            score += 0.1
            
        # 6. XPath depth penalty (prefer less nested)
        depth = node.xpath.count('/')
        if depth > 10:
            score -= 0.1
        elif depth < 5:
            score += 0.1
            
        # Ensure in [0, 1] range
        return max(0.0, min(1.0, score))
        
    def _is_hash_like(self, value: str) -> bool:
        """Check if a value looks like a hash/generated ID.
        
        Args:
            value: String to check
            
        Returns:
            True if hash-like
        """
        if not value or len(value) < 8:
            return False
            
        # Check for common hash patterns
        patterns = [
            # Long random strings
            len(value) > 20 and sum(c.isdigit() for c in value) > len(value) * 0.3,
            # UUID-like
            '-' in value and len(value) == 36,
            # Base64-like
            value.endswith('==') or value.endswith('='),
            # Webpack/build hashes
            any(pattern in value for pattern in ['_', '__', '--']) and 
            sum(c.isdigit() or c in 'abcdef' for c in value.lower()) > len(value) * 0.5
        ]
        
        return any(patterns)
        
    def _create_explanation(self,
        semantic_score: float,
        heuristic_score: float,
        promotion_score: float,
        final_score: float
    ) -> str:
        """Create human-readable explanation of scoring.
        
        Args:
            semantic_score: Semantic similarity score
            heuristic_score: Heuristic score
            promotion_score: Promotion score
            final_score: Final fused score
            
        Returns:
            Explanation string
        """
        parts = []
        
        # Semantic contribution
        semantic_contrib = (self.alpha * semantic_score) / (final_score + 0.001)
        if semantic_contrib > 0.5:
            parts.append("strong semantic match")
        elif semantic_contrib > 0.3:
            parts.append("moderate semantic match")
        elif semantic_contrib > 0.1:
            parts.append("weak semantic match")
            
        # Heuristic contribution
        heuristic_contrib = (self.beta * heuristic_score) / (final_score + 0.001)
        if heuristic_contrib > 0.3:
            parts.append("good structural features")
        elif heuristic_contrib > 0.1:
            parts.append("decent structural features")
            
        # Promotion contribution
        if promotion_score > 0:
            parts.append("historically successful")
            
        if not parts:
            parts.append("low overall match")
            
        return f"Ranked due to: {', '.join(parts)} (score: {final_score:.3f})"
        
    def adjust_weights(self, alpha: float, beta: float, gamma: float) -> None:
        """Adjust fusion weights.
        
        Args:
            alpha: Semantic weight
            beta: Heuristic weight
            gamma: Promotion weight
        """
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        
        logger.info(f"Adjusted fusion weights: α={alpha}, β={beta}, γ={gamma}")