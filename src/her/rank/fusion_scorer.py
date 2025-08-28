"""Advanced fusion scoring system for element ranking."""

from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import numpy as np
import logging
from enum import Enum

from ..config import FUSION_ALPHA, FUSION_BETA, FUSION_GAMMA

logger = logging.getLogger(__name__)


class ScoreType(Enum):
    """Types of scoring components."""

    SEMANTIC = "semantic"
    HEURISTIC = "heuristic"
    PROMOTION = "promotion"
    POSITION = "position"
    VISIBILITY = "visibility"
    ACCESSIBILITY = "accessibility"


@dataclass
class ElementScore:
    """Complete scoring information for an element."""

    element_id: str
    semantic_score: float = 0.0
    heuristic_score: float = 0.0
    promotion_score: float = 0.0
    position_score: float = 0.0
    visibility_score: float = 0.0
    accessibility_score: float = 0.0

    # Component weights
    alpha: float = FUSION_ALPHA  # Semantic weight
    beta: float = FUSION_BETA  # Heuristic weight
    gamma: float = FUSION_GAMMA  # Promotion weight

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    explanations: List[str] = field(default_factory=list)

    @property
    def fusion_score(self) -> float:
        """Calculate weighted fusion score."""
        # Normalize weights
        total_weight = self.alpha + self.beta + self.gamma
        if total_weight == 0:
            return 0.0

        normalized_alpha = self.alpha / total_weight
        normalized_beta = self.beta / total_weight
        normalized_gamma = self.gamma / total_weight

        # Calculate weighted sum
        score = (
            normalized_alpha * self.semantic_score
            + normalized_beta * self.heuristic_score
            + normalized_gamma * self.promotion_score
        )

        # Apply position and visibility modifiers
        if self.position_score > 0:
            score *= 1 + self.position_score * 0.1  # Up to 10% boost

        if self.visibility_score < 1.0:
            score *= self.visibility_score  # Penalize hidden elements

        # Apply accessibility bonus
        if self.accessibility_score > 0:
            score *= 1 + self.accessibility_score * 0.05  # Up to 5% boost

        return min(1.0, max(0.0, score))  # Clamp to [0, 1]

    def add_explanation(self, explanation: str) -> None:
        """Add scoring explanation."""
        self.explanations.append(explanation)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "element_id": self.element_id,
            "fusion_score": self.fusion_score,
            "components": {
                "semantic": self.semantic_score,
                "heuristic": self.heuristic_score,
                "promotion": self.promotion_score,
                "position": self.position_score,
                "visibility": self.visibility_score,
                "accessibility": self.accessibility_score,
            },
            "weights": {"alpha": self.alpha, "beta": self.beta, "gamma": self.gamma},
            "explanations": self.explanations,
            "metadata": self.metadata,
        }


class FusionScorer:
    """Advanced fusion scoring for element ranking."""

    def __init__(
        self,
        alpha: float = FUSION_ALPHA,
        beta: float = FUSION_BETA,
        gamma: float = FUSION_GAMMA,
        adaptive: bool = True,
    ):
        """Initialize fusion scorer.

        Args:
            alpha: Semantic similarity weight
            beta: Heuristic score weight
            gamma: Promotion score weight
            adaptive: Enable adaptive weight adjustment
        """
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.adaptive = adaptive

        # Track scoring history for adaptation
        self.history: List[ElementScore] = []
        self.success_feedback: Dict[str, float] = {}

    def score(self, semantic: float, heuristic: float, promotion: float) -> float:
        """Calculate fusion score from component scores.
        
        Args:
            semantic: Semantic similarity score (0-1)
            heuristic: Heuristic matching score (0-1)
            promotion: Historical success score (0-1)
            
        Returns:
            Fusion score (0-1)
        """
        # Apply weights from config
        weighted_score = (
            self.alpha * semantic +
            self.beta * heuristic +
            self.gamma * promotion
        )
        
        # Normalize to [0, 1]
        return min(1.0, max(0.0, weighted_score))
    
    def score_element(
        self,
        element: Dict[str, Any],
        query_embedding: Optional[np.ndarray] = None,
        element_embedding: Optional[np.ndarray] = None,
        promotion_data: Optional[Dict[str, float]] = None,
    ) -> ElementScore:
        """Score a single element.

        Args:
            element: Element descriptor
            query_embedding: Query embedding vector
            element_embedding: Element embedding vector
            promotion_data: Historical promotion scores

        Returns:
            Element score
        """
        element_id = element.get("xpath", element.get("id", "unknown"))

        score = ElementScore(
            element_id=element_id, alpha=self.alpha, beta=self.beta, gamma=self.gamma
        )

        # Calculate semantic similarity
        if query_embedding is not None and element_embedding is not None:
            score.semantic_score = self._compute_semantic_similarity(
                query_embedding, element_embedding
            )
            score.add_explanation(f"Semantic similarity: {score.semantic_score:.3f}")

        # Calculate heuristic score
        score.heuristic_score = self._compute_heuristic_score(element)
        score.add_explanation(f"Heuristic score: {score.heuristic_score:.3f}")

        # Get promotion score
        if promotion_data and element_id in promotion_data:
            score.promotion_score = promotion_data[element_id]
            score.add_explanation(f"Promotion score: {score.promotion_score:.3f}")

        # Calculate position score
        score.position_score = self._compute_position_score(element)
        if score.position_score > 0:
            score.add_explanation(f"Position bonus: {score.position_score:.3f}")

        # Calculate visibility score
        score.visibility_score = self._compute_visibility_score(element)
        if score.visibility_score < 1.0:
            score.add_explanation(f"Visibility penalty: {1-score.visibility_score:.3f}")

        # Calculate accessibility score
        score.accessibility_score = self._compute_accessibility_score(element)
        if score.accessibility_score > 0:
            score.add_explanation(
                f"Accessibility bonus: {score.accessibility_score:.3f}"
            )

        # Adaptive weight adjustment
        if self.adaptive:
            self._adapt_weights(score)

        # Store in history
        self.history.append(score)

        return score

    def score_batch(
        self,
        elements: List[Dict[str, Any]],
        query_embedding: Optional[np.ndarray] = None,
        element_embeddings: Optional[List[np.ndarray]] = None,
        promotion_data: Optional[Dict[str, float]] = None,
    ) -> List[ElementScore]:
        """Score multiple elements.

        Args:
            elements: List of element descriptors
            query_embedding: Query embedding vector
            element_embeddings: List of element embedding vectors
            promotion_data: Historical promotion scores

        Returns:
            List of element scores
        """
        scores = []

        for i, element in enumerate(elements):
            element_embedding = element_embeddings[i] if element_embeddings else None
            score = self.score_element(
                element, query_embedding, element_embedding, promotion_data
            )
            scores.append(score)

        return scores

    def rank_elements(
        self,
        scores: List[ElementScore],
        top_k: Optional[int] = None,
        threshold: Optional[float] = None,
    ) -> List[Tuple[str, float]]:
        """Rank elements by fusion score.

        Args:
            scores: List of element scores
            top_k: Return only top K elements
            threshold: Minimum score threshold

        Returns:
            List of (element_id, score) tuples
        """
        # Sort by fusion score
        sorted_scores = sorted(scores, key=lambda s: s.fusion_score, reverse=True)

        # Apply threshold
        if threshold:
            sorted_scores = [s for s in sorted_scores if s.fusion_score >= threshold]

        # Apply top_k
        if top_k:
            sorted_scores = sorted_scores[:top_k]

        return [(s.element_id, s.fusion_score) for s in sorted_scores]

    def _compute_semantic_similarity(
        self, query_embedding: np.ndarray, element_embedding: np.ndarray
    ) -> float:
        """Compute semantic similarity between embeddings.

        Args:
            query_embedding: Query embedding
            element_embedding: Element embedding

        Returns:
            Similarity score [0, 1]
        """
        # Cosine similarity
        dot_product = np.dot(query_embedding, element_embedding)
        norm_query = np.linalg.norm(query_embedding)
        norm_element = np.linalg.norm(element_embedding)

        if norm_query == 0 or norm_element == 0:
            return 0.0

        similarity = dot_product / (norm_query * norm_element)

        # Normalize to [0, 1]
        return (similarity + 1) / 2

    def _compute_heuristic_score(self, element: Dict[str, Any]) -> float:
        """Compute heuristic score based on element properties.

        Args:
            element: Element descriptor

        Returns:
            Heuristic score [0, 1]
        """
        score = 0.0
        max_score = 0.0

        # Check for semantic HTML elements
        tag_name = element.get("tag", "").lower()
        semantic_tags = {
            "button": 0.3,
            "input": 0.25,
            "a": 0.2,
            "select": 0.25,
            "textarea": 0.25,
            "form": 0.15,
            "label": 0.1,
        }

        if tag_name in semantic_tags:
            score += semantic_tags[tag_name]
        max_score += 0.3

        # Check for actionable attributes
        attributes = element.get("attributes", {})

        if attributes.get("type") in ["submit", "button", "checkbox", "radio"]:
            score += 0.2
        max_score += 0.2

        # Check for ARIA attributes
        aria_attrs = [k for k in attributes.keys() if k.startswith("aria-")]
        if aria_attrs:
            score += min(0.2, len(aria_attrs) * 0.05)
        max_score += 0.2

        # Check for ID or unique class
        if attributes.get("id"):
            score += 0.15
        elif attributes.get("class"):
            classes = attributes["class"].split()
            if len(classes) <= 3:  # Prefer specific classes
                score += 0.1
        max_score += 0.15

        # Check for text content
        text = element.get("text", "").strip()
        if text and len(text) < 100:  # Reasonable text length
            score += 0.15
        max_score += 0.15

        return score / max_score if max_score > 0 else 0.0

    def _compute_position_score(self, element: Dict[str, Any]) -> float:
        """Compute position score based on element location.

        Args:
            element: Element descriptor

        Returns:
            Position score [0, 1]
        """
        bbox = element.get("bbox", {})
        if not bbox:
            return 0.0

        x = bbox.get("x", 0)
        y = bbox.get("y", 0)
        width = bbox.get("width", 0)
        height = bbox.get("height", 0)

        # Prefer elements in viewport
        viewport_width = 1280  # Default viewport
        viewport_height = 720

        if x < 0 or y < 0 or x > viewport_width or y > viewport_height:
            return 0.0

        # Prefer elements above the fold
        if y < viewport_height:
            position_score = 1.0 - (y / viewport_height) * 0.5
        else:
            position_score = 0.5 - min(
                0.5, (y - viewport_height) / viewport_height * 0.5
            )

        # Prefer reasonably sized elements
        if width > 20 and height > 20:
            size_score = min(1.0, (width * height) / (200 * 50))
        else:
            size_score = 0.0

        return (position_score + size_score) / 2

    def _compute_visibility_score(self, element: Dict[str, Any]) -> float:
        """Compute visibility score.

        Args:
            element: Element descriptor

        Returns:
            Visibility score [0, 1]
        """
        # Check computed styles
        styles = element.get("styles", {})

        # Check display
        if styles.get("display") == "none":
            return 0.0

        # Check visibility
        if styles.get("visibility") == "hidden":
            return 0.0

        # Check opacity
        opacity = styles.get("opacity", "1")
        try:
            opacity_val = float(opacity)
            if opacity_val < 0.1:
                return opacity_val
        except Exception:
            # Element might not have computed styles yet
            return 1.0

        # Check if occluded
        if element.get("occluded", False):
            return 0.5

        return 1.0

    def _compute_accessibility_score(self, element: Dict[str, Any]) -> float:
        """Compute accessibility score.

        Args:
            element: Element descriptor

        Returns:
            Accessibility score [0, 1]
        """
        score = 0.0
        attributes = element.get("attributes", {})

        # Check for accessibility attributes
        if attributes.get("role"):
            score += 0.3

        if attributes.get("aria-label") or attributes.get("aria-labelledby"):
            score += 0.3

        if attributes.get("aria-describedby") or attributes.get("aria-description"):
            score += 0.2

        if attributes.get("tabindex"):
            try:
                tabindex = int(attributes["tabindex"])
                if tabindex >= 0:
                    score += 0.2
            except Exception:
                # Tabindex might not be available or parseable
                pass

        return min(1.0, score)

    def _adapt_weights(self, score: ElementScore) -> None:
        """Adapt weights based on feedback.

        Args:
            score: Element score
        """
        if not self.success_feedback:
            return

        # Get feedback for this element
        element_id = score.element_id
        if element_id in self.success_feedback:
            success_rate = self.success_feedback[element_id]

            # Adjust weights based on success rate
            if success_rate > 0.8:
                # Increase weight of dominant component
                if score.semantic_score > score.heuristic_score:
                    self.alpha = min(1.5, self.alpha * 1.05)
                else:
                    self.beta = min(1.0, self.beta * 1.05)
            elif success_rate < 0.3:
                # Reduce weights proportionally
                self.alpha *= 0.95
                self.beta *= 0.95
                self.gamma *= 1.1  # Increase promotion weight

    def update_feedback(self, element_id: str, success: bool) -> None:
        """Update success feedback for adaptation.

        Args:
            element_id: Element identifier
            success: Whether the element selection was successful
        """
        if element_id not in self.success_feedback:
            self.success_feedback[element_id] = 0.0

        # Exponential moving average
        alpha = 0.3
        self.success_feedback[element_id] = (
            alpha * (1.0 if success else 0.0)
            + (1 - alpha) * self.success_feedback[element_id]
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get scoring statistics."""
        if not self.history:
            return {}

        fusion_scores = [s.fusion_score for s in self.history]

        return {
            "total_scored": len(self.history),
            "avg_fusion_score": np.mean(fusion_scores),
            "std_fusion_score": np.std(fusion_scores),
            "current_weights": {
                "alpha": self.alpha,
                "beta": self.beta,
                "gamma": self.gamma,
            },
            "success_feedback_count": len(self.success_feedback),
        }
