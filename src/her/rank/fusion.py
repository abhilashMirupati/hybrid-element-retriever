"""Heuristic rank fusion for candidates given an intent.

Avoid heavy imports; combine any existing candidate score with lightweight
signals like tag/role priority and token overlap with the intent target.
"""

from typing import Any, Dict, List


def _tokenize(text: str) -> List[str]:
    return [t for t in (text or "").lower().split() if t]


def _token_overlap(a: str, b: str) -> float:
    ta, tb = set(_tokenize(a)), set(_tokenize(b))
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / float(len(ta | tb))


def _tag_bias(tag: str) -> float:
    t = (tag or "").lower()
    if t == "button":
        return 0.05
    if t == "a":
        return 0.03
    if t == "input":
        return 0.02
    return 0.0


def _role_bonus(role: str) -> float:
    r = (role or "").lower()
    if r in ("button", "link", "tab", "menuitem"):
        return 0.02
    return 0.0


def fuse(candidates: List[Dict[str, Any]], intent: Dict[str, Any]) -> List[Dict[str, Any]]:
    target = str(intent.get("target") or intent.get("target_phrase") or "")
    scored: List[Dict[str, Any]] = []
    for c in candidates:
        base = float(c.get("score", 0.0))
        desc = c.get("descriptor") or c
        tag = (desc.get("tag") or desc.get("tagName") or "")
        role = (desc.get("role") or (desc.get("attrs") or {}).get("role") or "")
        text = str(desc.get("text") or "")
        score = base + _tag_bias(tag) + _role_bonus(role) + 0.1 * _token_overlap(text, target)
        out = dict(c)
        out["score"] = score
        scored.append(out)
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored


class FusionScorer:
    """Fusion scorer for combining multiple scoring signals."""
    
    def score(self, query_embedding: Any, element_embedding: Any, element_descriptor: Dict[str, Any], intent: Any) -> float:
        """Score an element based on embeddings and intent."""
        # Basic scoring based on element properties
        base_score = 0.0
        
        # Text similarity
        if hasattr(intent, 'target_phrase') and intent.target_phrase:
            text = str(element_descriptor.get("text", ""))
            base_score += _token_overlap(text, intent.target_phrase)
        
        # Tag bias
        tag = element_descriptor.get("tag", "")
        base_score += _tag_bias(tag)
        
        # Role bonus
        role = element_descriptor.get("role", "")
        base_score += _role_bonus(role)
        
        return base_score
