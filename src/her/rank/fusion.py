from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Optional, TypedDict


ALPHA_DEFAULT = 1.0
BETA_DEFAULT = 0.5
GAMMA_DEFAULT = 0.2


@dataclass
class FusionConfig:
    alpha: float = ALPHA_DEFAULT
    beta: float = BETA_DEFAULT
    gamma: float = GAMMA_DEFAULT


class ElementScore(TypedDict):
    element: Dict[str, Any]
    score: float
    details: Dict[str, float]


class FusionScorer:
    def __init__(self, config: Optional[FusionConfig] = None) -> None:
        self.config = config or FusionConfig()

    def fuse(self, semantic: float, robust_css: float, promotion: float = 0.0) -> float:
        return float(self.config.alpha * semantic + self.config.beta * robust_css + self.config.gamma * promotion)

    def score_elements(
        self,
        elements: List[Dict[str, Any]],
        semantic_scores: List[float],
        css_scores: List[float],
        promotions: Optional[List[float]] = None,
    ) -> List[ElementScore]:
        n = len(elements)
        promotions = promotions or [0.0] * n
        fused: List[Tuple[int, float]] = []
        for i in range(n):
            s = self.fuse(float(semantic_scores[i]), float(css_scores[i]), float(promotions[i]))
            fused.append((i, s))
        # Stable tie-breakers by deterministic string rep
        fused.sort(key=lambda t: (t[1], str(elements[t[0]].get('id') or elements[t[0]].get('xpath') or elements[t[0]].get('text') or '')), reverse=True)
        if fused:
            scores_only = [sc for _, sc in fused]
            mx = max(scores_only); mn = min(scores_only); rng = (mx - mn) if mx != mn else 1.0
            normalized = [(i, (sc - mn) / rng) for i, sc in fused]
        else:
            normalized = []
        out: List[ElementScore] = []
        for i, sc in normalized:
            out.append({'element': elements[i], 'score': float(sc), 'details': {'semantic': float(semantic_scores[i]), 'css': float(css_scores[i]), 'promotion': float(promotions[i])}})
        return out


__all__ = ['FusionScorer', 'FusionConfig', 'ElementScore']
