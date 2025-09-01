from __future__ import annotations
from typing import Dict, Any, List

DEFAULT_WEIGHTS = {
    "semantic": 0.55,
    "clickable": 0.10,
    "role_match": 0.18,
    "token_boost": 0.14,
    "visibility": 0.05,
    "deterministic_tie": 0.08,
}

BOOST_TOKENS = {"email", "password", "laptop", "phone", "tablet", "add to cart", "login", "signin", "sign in"}

CLICKABLE_ROLES = {"button", "link", "menuitem", "tab", "checkbox", "radio", "combobox"}

def _contains_token(desc_text: str, attrs: Dict[str, Any]) -> bool:
    txt = (desc_text or "").lower()
    hay = [txt]
    for k in ("aria-label", "data-testid", "id", "name", "title", "placeholder"):
        v = (attrs or {}).get(k) or ""
        hay.append(str(v).lower())
    blob = " ".join(hay)
    return any(tok in blob for tok in BOOST_TOKENS)

def fuse_scores(
    base_semantic: float,
    intent_action: str,
    descriptor: Dict[str, Any],
    is_visible: bool = True,
    is_clickable: bool = True,
    weights: Dict[str, float] = None,
    idx: int = 0,
) -> float:
    w = dict(DEFAULT_WEIGHTS)
    if weights:
        w.update(weights)

    score = base_semantic * w["semantic"]

    role = (descriptor.get("attributes") or {}).get("role")
    tag = (descriptor.get("tag") or "").lower()
    if intent_action == "click":
        role_match = 1.0 if (role in CLICKABLE_ROLES or tag in ("button", "a")) else 0.0
    elif intent_action == "type":
        role_match = 1.0 if (tag in ("input", "textarea")) else 0.0
    elif intent_action == "select":
        role_match = 1.0 if (tag in ("select",)) else 0.0
    else:
        role_match = 0.5
    score += role_match * w["role_match"]

    score += (1.0 if is_clickable else 0.0) * w["clickable"]
    score += (1.0 if is_visible else 0.0) * w["visibility"]

    if _contains_token(descriptor.get("text") or "", descriptor.get("attributes") or {}):
        score += 1.0 * w["token_boost"]

    score += (max(0.0, 0.01 - (idx * 0.00001))) * w["deterministic_tie"]

    return float(score)


# Back-compat FusionScorer shim expected by tests
class FusionScorer:  # pragma: no cover - thin shim
    def score_elements(self, query: str, elements: List[Dict[str, Any]]):
        # Lightweight keyword+role heuristic aligned with tests
        results: List[Dict[str, Any]] = []
        ql = str(query or "").lower()
        action = "select" if any(w in ql for w in ["select", "choose"]) else ("type" if any(w in ql for w in ["type", "enter", "fill"]) else "click")
        words = [w for w in ql.replace("'", " ").split() if w]
        for idx, e in enumerate(elements):
            text = str(e.get("text", "")).lower()
            base = 0.0
            for w in words:
                if w and w in text:
                    base += 0.1
            tag = str(e.get("tag", "")).lower()
            attrs = e.get("attributes", {}) or {}
            clickable = bool(attrs.get("role") in CLICKABLE_ROLES or tag in ("button", "a"))
            score = fuse_scores(base, action, e, bool(e.get("is_visible", True)), clickable, None, idx)
            results.append({"element": e, "score": min(1.0, max(0.0, score)), "xpath": e.get("xpath", "")})
        results.sort(key=lambda x: x["score"], reverse=True)
        return results
