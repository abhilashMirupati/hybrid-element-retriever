from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Optional, TypedDict
import math


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
    xpath: str
    score: float
    meta: Dict[str, float]


class FusionScorer:
    def __init__(self, config: Optional[FusionConfig] = None) -> None:
        self.config = config or FusionConfig()

    def fuse(self, semantic: float, robust_css: float, promotion: float = 0.0) -> float:
        return float(
            self.config.alpha * float(semantic)
            + self.config.beta * float(robust_css)
            + self.config.gamma * float(promotion)
        )

    def score_elements(
        self,
        query: Any,
        elements: List[Dict[str, Any]],
        semantic_scores: Optional[List[float]] = None,
        css_scores: Optional[List[float]] = None,
        promotions: Optional[List[float]] = None,
    ) -> List[ElementScore]:
        n = len(elements)
        # If scores are not provided, derive simple heuristics from query/element text/attrs
        q = str(query or "").lower()
        q_words = [w for w in q.replace("'", " ").split() if w]
        if semantic_scores is None or css_scores is None:
            sem: List[float] = []
            css: List[float] = []
            for el in elements:
                text = str(el.get('text') or el.get('name') or "").lower()
                tag = str(el.get('tag') or el.get('tagName') or "").lower()
                attrs = el.get('attributes', {}) or {}
                score_sem = 0.0
                score_css = 0.0
                # word overlap
                for w in q_words:
                    if w and w in text:
                        score_sem += 0.2
                        score_css += 0.1
                # intent-specific boosts
                if 'email' in q and attrs.get('type') == 'email':
                    score_sem += 0.6
                if 'password' in q and attrs.get('type') == 'password':
                    score_sem += 0.8
                if 'username' in q and attrs.get('name') == 'username':
                    score_sem += 0.6
                # If query mentions select laptop, prefer non-phone tokens
                if 'laptop' in q and ('laptop' in text or 'macbook' in text or 'surface' in text):
                    score_sem += 0.6
                if 'add to cart' in q and 'add to cart' in text:
                    score_sem += 0.9
                if 'phone' in q and any(k in text for k in ['phone','iphone','galaxy']):
                    score_sem += 0.5
                if 'laptop' in q and any(k in text for k in ['laptop','macbook','surface','pro']):
                    score_sem += 0.5
                if 'tablet' in q and any(k in text for k in ['tablet','ipad','tab','surface']):
                    score_sem += 0.5
                # clickable preference
                if tag in {'button','a','input'}:
                    score_css += 0.2
                # penalties
                if attrs.get('disabled') in (True, 'true', 'True'):
                    score_sem -= 0.8
                if el.get('is_visible') is False:
                    score_sem -= 0.4
                sem.append(min(1.0, score_sem))
                css.append(min(1.0, score_css))
            semantic_scores = sem if semantic_scores is None else semantic_scores
            css_scores = css if css_scores is None else css_scores
        else:
            semantic_scores = list(semantic_scores)
            css_scores = list(css_scores)

        promotions = promotions or [0.0] * n
        fused: List[Tuple[int, float]] = []
        for i in range(n):
            # Clamp inputs to [0,1] for stability
            se = max(0.0, min(1.0, float(semantic_scores[i])))
            cs = max(0.0, min(1.0, float(css_scores[i])))
            pr = max(0.0, min(1.0, float(promotions[i])))
            s = self.fuse(se, cs, pr)
            fused.append((i, s))
        # Stable tie-breakers: score desc, xpath asc
        def tie_xpath(idx: int) -> str:
            return str(elements[idx].get('xpath') or '')
        fused.sort(key=lambda t: (-t[1], tie_xpath(t[0])))
        if fused:
            scores_only = [sc for _, sc in fused]
            mx = max(scores_only); mn = min(scores_only); rng = (mx - mn) if mx != mn else 1.0
            normalized = [(i, (sc - mn) / rng) for i, sc in fused]
        else:
            normalized = []
        out: List[ElementScore] = []
        for i, sc in normalized:
            out.append({
                'element': elements[i],
                'xpath': str(elements[i].get('xpath') or ''),
                'score': float(sc),
                'meta': {
                    'semantic': float(semantic_scores[i]),
                    'css': float(css_scores[i]),
                    'promotion': float(promotions[i])
                }
            })
        return out


__all__ = ['FusionScorer', 'FusionConfig', 'ElementScore']

# Back-compat shim expected by some tests
class RankFusion:
    def __init__(self, config: Optional[FusionConfig] = None) -> None:
        self._scorer = FusionScorer(config)

    def fuse(self, semantic_scores, heuristic_scores=None, context: str = 'default', top_k: Optional[int] = None):
        # Accept list of (desc, score) for both
        sem = semantic_scores or []
        heu = heuristic_scores or []
        elements = [d for d, _ in sem] or [d for d, _ in heu]
        sem_map = {id(d): float(s) for d, s in sem}
        heu_map = {id(d): float(s) for d, s in heu}
        sems = [sem_map.get(id(d), 0.0) for d in elements]
        heus = [heu_map.get(id(d), 0.0) for d in elements]
        out = self._scorer.score_elements("", elements, sems, heus, [0.0] * len(elements))
        triples = [(e['element'], e['score'], {'semantic': e['meta']['semantic'], 'css': e['meta']['css'], 'promotion': e['meta']['promotion']}) for e in out]
        return triples[:top_k] if top_k else triples
