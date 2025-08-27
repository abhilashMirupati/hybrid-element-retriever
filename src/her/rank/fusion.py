"""Fusion ranking combining semantic, heuristic, and promotion scores."""
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)

# Default weight configuration
DEFAULT_ALPHA = 0.4  # Semantic similarity weight
DEFAULT_BETA = 0.4   # Heuristic score weight
DEFAULT_GAMMA = 0.2  # Promotion score weight


@dataclass
class FusionConfig:
    """Configuration for fusion ranking."""
    alpha: float = DEFAULT_ALPHA
    beta: float = DEFAULT_BETA
    gamma: float = DEFAULT_GAMMA
    
    def __post_init__(self):
        # Normalize weights to sum to 1.0
        total = self.alpha + self.beta + self.gamma
        if total > 0:
            self.alpha /= total
            self.beta /= total
            self.gamma /= total


class RankFusion:
    """Fuses multiple ranking signals with configurable weights."""
    
    def __init__(
        self,
        config: Optional[FusionConfig] = None,
        promotion_store_path: Optional[Path] = None
    ):
        self.config = config or FusionConfig()
        self.promotion_store_path = promotion_store_path or Path.home() / ".cache" / "her" / "promotions.json"
        self.promotions = self._load_promotions()
    
    def _load_promotions(self) -> Dict[str, float]:
        """Load promotion scores from persistent store."""
        if self.promotion_store_path.exists():
            try:
                with open(self.promotion_store_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load promotions: {e}")
        return {}
    
    def _save_promotions(self) -> None:
        """Save promotion scores to persistent store."""
        try:
            self.promotion_store_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.promotion_store_path, 'w') as f:
                json.dump(self.promotions, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save promotions: {e}")
    
    def _get_promotion_key(self, descriptor: Dict[str, Any], context: str) -> str:
        """Generate unique key for promotion lookup."""
        # Create stable key from element properties and context
        sig = {
            "tag": descriptor.get("tag"),
            "id": descriptor.get("id"),
            "classes": sorted(descriptor.get("classes", [])),
            "role": descriptor.get("role"),
            "name": descriptor.get("name"),
            "context": context,
        }
        return json.dumps(sig, sort_keys=True)
    
    def fuse(
        self,
        semantic_scores: List[Tuple[Dict[str, Any], float]],
        heuristic_scores: List[Tuple[Dict[str, Any], float]],
        context: str = "",
        top_k: int = 10
    ) -> List[Tuple[Dict[str, Any], float, Dict[str, Any]]]:
        """Fuse multiple ranking signals.
        
        Args:
            semantic_scores: List of (descriptor, semantic_score) tuples
            heuristic_scores: List of (descriptor, heuristic_score) tuples
            context: Context string for promotion lookup
            top_k: Number of top results to return
        
        Returns:
            List of (descriptor, fused_score, reasons) tuples
        """
        # Index scores by element (using backend node ID as key)
        semantic_by_id = {}
        for desc, score in semantic_scores:
            node_id = desc.get("backendNodeId")
            if node_id:
                semantic_by_id[node_id] = (desc, score)
        
        heuristic_by_id = {}
        for desc, score in heuristic_scores:
            node_id = desc.get("backendNodeId")
            if node_id:
                heuristic_by_id[node_id] = (desc, score)
        
        # Combine all unique elements
        all_node_ids = set(semantic_by_id.keys()) | set(heuristic_by_id.keys())
        
        fused_results = []
        for node_id in all_node_ids:
            # Get descriptor (prefer from semantic since it should have full data)
            desc = None
            semantic_score = 0.0
            heuristic_score = 0.0
            
            if node_id in semantic_by_id:
                desc, semantic_score = semantic_by_id[node_id]
            
            if node_id in heuristic_by_id:
                h_desc, heuristic_score = heuristic_by_id[node_id]
                if desc is None:
                    desc = h_desc
            
            if desc is None:
                continue
            
            # Get promotion score
            promotion_key = self._get_promotion_key(desc, context)
            promotion_score = self.promotions.get(promotion_key, 0.0)
            
            # Calculate fused score
            fused_score = (
                self.config.alpha * semantic_score +
                self.config.beta * heuristic_score +
                self.config.gamma * promotion_score
            )
            
            # Build reasons dictionary
            reasons = {
                "semantic_score": semantic_score,
                "heuristic_score": heuristic_score,
                "promotion_score": promotion_score,
                "weights": {
                    "alpha": self.config.alpha,
                    "beta": self.config.beta,
                    "gamma": self.config.gamma,
                },
                "fused_score": fused_score,
                "explanation": self._explain_fusion(
                    semantic_score, heuristic_score, promotion_score, fused_score
                ),
            }
            
            fused_results.append((desc, fused_score, reasons))
        
        # Sort by fused score descending
        fused_results.sort(key=lambda x: x[1], reverse=True)
        
        # Log top results
        if fused_results:
            top = fused_results[0]
            logger.info(
                f"Top fusion result: score={top[1]:.3f}, "
                f"semantic={top[2]['semantic_score']:.3f}, "
                f"heuristic={top[2]['heuristic_score']:.3f}, "
                f"promotion={top[2]['promotion_score']:.3f}"
            )
        
        return fused_results[:top_k]
    
    def _explain_fusion(
        self,
        semantic: float,
        heuristic: float,
        promotion: float,
        fused: float
    ) -> str:
        """Generate human-readable explanation of fusion."""
        parts = []
        
        if semantic > 0.5:
            parts.append("Strong semantic match")
        elif semantic > 0.2:
            parts.append("Moderate semantic match")
        
        if heuristic > 0.5:
            parts.append("Strong heuristic match")
        elif heuristic > 0.2:
            parts.append("Moderate heuristic match")
        
        if promotion > 0.5:
            parts.append("Previously successful (promoted)")
        elif promotion > 0:
            parts.append("Some prior success")
        
        if not parts:
            parts.append("Weak overall match")
        
        return f"Fusion score {fused:.3f}: {', '.join(parts)}"
    
    def promote(
        self,
        descriptor: Dict[str, Any],
        context: str = "",
        boost: float = 0.1
    ) -> None:
        """Promote an element that was successfully used.
        
        Args:
            descriptor: Element descriptor
            context: Context string
            boost: Amount to boost promotion score
        """
        key = self._get_promotion_key(descriptor, context)
        current = self.promotions.get(key, 0.0)
        self.promotions[key] = min(1.0, current + boost)
        self._save_promotions()
        
        logger.info(f"Promoted element: {key[:50]}... -> {self.promotions[key]:.3f}")
    
    def demote(
        self,
        descriptor: Dict[str, Any],
        context: str = "",
        penalty: float = 0.05
    ) -> None:
        """Demote an element that failed.
        
        Args:
            descriptor: Element descriptor
            context: Context string
            penalty: Amount to reduce promotion score
        """
        key = self._get_promotion_key(descriptor, context)
        current = self.promotions.get(key, 0.0)
        self.promotions[key] = max(0.0, current - penalty)
        self._save_promotions()
        
        logger.info(f"Demoted element: {key[:50]}... -> {self.promotions[key]:.3f}")
    
    def clear_promotions(self) -> None:
        """Clear all promotion scores."""
        self.promotions = {}
        self._save_promotions()
        logger.info("Cleared all promotions")
    
    def update_weights(
        self,
        alpha: Optional[float] = None,
        beta: Optional[float] = None,
        gamma: Optional[float] = None
    ) -> None:
        """Update fusion weights.
        
        Args:
            alpha: Semantic weight
            beta: Heuristic weight
            gamma: Promotion weight
        """
        if alpha is not None:
            self.config.alpha = alpha
        if beta is not None:
            self.config.beta = beta
        if gamma is not None:
            self.config.gamma = gamma
        
        # Re-normalize
        total = self.config.alpha + self.config.beta + self.config.gamma
        if total > 0:
            self.config.alpha /= total
            self.config.beta /= total
            self.config.gamma /= total
        
        logger.info(
            f"Updated fusion weights: α={self.config.alpha:.3f}, "
            f"β={self.config.beta:.3f}, γ={self.config.gamma:.3f}"
        )