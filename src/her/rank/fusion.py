"""Fusion ranking combining semantic, heuristic, and promotion scores."""

from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
import logging
import json
from pathlib import Path

from ..config import FUSION_ALPHA, FUSION_BETA, FUSION_GAMMA, get_promotion_store_path

logger = logging.getLogger(__name__)


@dataclass
class FusionConfig:
    """Configuration for fusion ranking."""

    alpha: float = FUSION_ALPHA  # Semantic similarity weight (1.0)
    beta: float = FUSION_BETA  # Heuristic score weight (0.5)
    gamma: float = FUSION_GAMMA  # Promotion score weight (0.2)

    def __post_init__(self):
        # Normalize weights to sum to 1.0
        total = self.alpha + self.beta + self.gamma
        if total > 0:
            self.alpha /= total
            self.beta /= total
            self.gamma /= total

        logger.debug(
            f"Fusion weights normalized: α={self.alpha:.3f}, β={self.beta:.3f}, γ={self.gamma:.3f}"
        )


class RankFusion:
    """Fuses multiple ranking signals with configurable weights."""

    def __init__(
        self,
        config: Optional[FusionConfig] = None,
        promotion_store_path: Optional[Path] = None,
    ):
        self.config = config or FusionConfig()
        self.promotion_store_path = promotion_store_path or get_promotion_store_path()
        self.promotions = self._load_promotions()

    def _load_promotions(self) -> Dict[str, float]:
        """Load promotion scores from persistent store."""
        if self.promotion_store_path.exists():
            try:
                with open(self.promotion_store_path, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load promotions: {e}")
        return {}

    def _save_promotions(self) -> None:
        """Save promotion scores to persistent store."""
        try:
            self.promotion_store_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.promotion_store_path, "w") as f:
                json.dump(self.promotions, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save promotions: {e}")

    def fuse_scores(
        self, semantic_score: float, heuristic_score: float, element: Dict[str, Any]
    ) -> float:
        """Fuse multiple ranking scores into final score.

        Args:
            semantic_score: Semantic similarity score [0, 1]
            heuristic_score: Heuristic-based score [0, 1]
            element: Element descriptor for promotion lookup

        Returns:
            Fused score [0, 1]
        """
        # Clamp scores to [0, 1]
        semantic_score = max(0.0, min(1.0, semantic_score))
        heuristic_score = max(0.0, min(1.0, heuristic_score))

        # Get promotion score
        promotion_key = self._get_promotion_key(element)
        promotion_score = self.promotions.get(promotion_key, 0.5)  # Default to neutral

        # Apply fusion formula: score = α*semantic + β*heuristic + γ*promotion
        fused = (
            self.config.alpha * semantic_score
            + self.config.beta * heuristic_score
            + self.config.gamma * promotion_score
        )

        # Ensure result is in [0, 1]
        fused = max(0.0, min(1.0, fused))

        logger.debug(
            f"Fusion: semantic={semantic_score:.3f}, heuristic={heuristic_score:.3f}, "
            f"promotion={promotion_score:.3f} -> fused={fused:.3f}"
        )

        return fused

    def rank_candidates(
        self, candidates: List[Tuple[Dict[str, Any], float, float]]
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Rank candidates using fusion scoring.

        Args:
            candidates: List of (element, semantic_score, heuristic_score) tuples

        Returns:
            Sorted list of (element, fused_score) tuples
        """
        ranked = []

        for element, semantic_score, heuristic_score in candidates:
            fused_score = self.fuse_scores(semantic_score, heuristic_score, element)
            ranked.append((element, fused_score))

        # Sort by fused score (descending)
        ranked.sort(key=lambda x: x[1], reverse=True)

        return ranked

    def _get_promotion_key(self, element: Dict[str, Any]) -> str:
        """Generate promotion key for element.

        Args:
            element: Element descriptor

        Returns:
            Stable key for promotion lookup
        """
        # Use combination of stable attributes
        parts = []

        # Tag name
        tag = element.get("tagName", "")
        if tag:
            parts.append(f"tag:{tag}")

        # ID attribute
        attrs = element.get("attributes", {})
        elem_id = attrs.get("id", "")
        if elem_id:
            parts.append(f"id:{elem_id}")

        # Role
        role = element.get("role", "")
        if role:
            parts.append(f"role:{role}")

        # Text (truncated)
        text = element.get("text", "")[:50]
        if text:
            parts.append(f"text:{text}")

        # Name from accessibility
        name = element.get("name", "")[:50]
        if name:
            parts.append(f"name:{name}")

        return "|".join(parts) if parts else "unknown"

    def promote(self, element: Dict[str, Any], amount: float = 0.1) -> None:
        """Promote an element by increasing its promotion score.

        Args:
            element: Element to promote
            amount: Amount to increase score by
        """
        key = self._get_promotion_key(element)
        current = self.promotions.get(key, 0.5)

        # Increase score (max 1.0)
        self.promotions[key] = min(1.0, current + amount)

        logger.info(f"Promoted element: {key[:50]} -> {self.promotions[key]:.3f}")

        # Save to persistent store
        self._save_promotions()

    def demote(self, element: Dict[str, Any], amount: float = 0.1) -> None:
        """Demote an element by decreasing its promotion score.

        Args:
            element: Element to demote
            amount: Amount to decrease score by
        """
        key = self._get_promotion_key(element)
        current = self.promotions.get(key, 0.5)

        # Decrease score (min 0.0)
        self.promotions[key] = max(0.0, current - amount)

        logger.info(f"Demoted element: {key[:50]} -> {self.promotions[key]:.3f}")

        # Save to persistent store
        self._save_promotions()

    def get_promotion_score(self, element: Dict[str, Any]) -> float:
        """Get current promotion score for element.

        Args:
            element: Element descriptor

        Returns:
            Promotion score [0, 1]
        """
        key = self._get_promotion_key(element)
        return self.promotions.get(key, 0.5)  # Default to neutral

    def reset_promotions(self) -> None:
        """Reset all promotion scores."""
        self.promotions = {}
        self._save_promotions()
        logger.info("Reset all promotion scores")

    def explain_score(
        self, semantic_score: float, heuristic_score: float, element: Dict[str, Any]
    ) -> str:
        """Explain how the fused score was calculated.

        Args:
            semantic_score: Semantic similarity score
            heuristic_score: Heuristic-based score
            element: Element descriptor

        Returns:
            Human-readable explanation
        """
        promotion_score = self.get_promotion_score(element)
        fused_score = self.fuse_scores(semantic_score, heuristic_score, element)

        explanation = [
            f"Fusion Score: {fused_score:.3f}",
            f"  Semantic (α={self.config.alpha:.2f}): {semantic_score:.3f} * {self.config.alpha:.2f} = {semantic_score * self.config.alpha:.3f}",
            f"  Heuristic (β={self.config.beta:.2f}): {heuristic_score:.3f} * {self.config.beta:.2f} = {heuristic_score * self.config.beta:.3f}",
            f"  Promotion (γ={self.config.gamma:.2f}): {promotion_score:.3f} * {self.config.gamma:.2f} = {promotion_score * self.config.gamma:.3f}",
        ]

        return "\n".join(explanation)

    def fuse(
        self, rankings: Dict[str, List[Tuple[str, float]]]
    ) -> List[Tuple[str, float]]:
        """Simple fusion method for compatibility.

        Args:
            rankings: Dictionary of ranking sources

        Returns:
            Fused rankings
        """
        # Combine all rankings
        combined = {}
        for source, items in rankings.items():
            for item, score in items:
                if item not in combined:
                    combined[item] = []
                combined[item].append(score)

        # Average scores
        result = []
        for item, scores in combined.items():
            avg_score = sum(scores) / len(scores)
            result.append((item, avg_score))

        return sorted(result, key=lambda x: x[1], reverse=True)

    def update_weights(
        self, alpha: float = None, beta: float = None, gamma: float = None
    ):
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

        # Renormalize
        self.config.__post_init__()
