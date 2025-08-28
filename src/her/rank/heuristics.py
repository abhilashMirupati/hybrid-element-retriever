from __future__ import annotations
from typing import Dict, List, Tuple, Any


def robust_css_score(attrs: Dict[str, str]) -> float:
    score = 0.0
    idv = attrs.get('id') or ''
    if idv:
        score += 0.6
        # penalize hash-like ids
        if any(len(tok) >= 8 for tok in idv.replace('_','-').split('-')):
            score -= 0.3
    for k in ('data-testid', 'data-test', 'data-qa', 'aria-label', 'name'):
        if attrs.get(k):
            score += 0.2
    cls = attrs.get('class') or ''
    if 'active' in cls or 'selected' in cls:
        score += 0.1
    return max(0.0, min(1.0, score))


def heuristic_score(descriptor: Dict[str, Any], phrase: str = "", action: str = "") -> float:
    phrase_l = (phrase or '').lower()
    score = 0.0
    # tag bias
    tag = (descriptor.get('tag') or descriptor.get('tagName') or '').lower()
    if tag == 'button':
        score += 0.25
    elif tag == 'a':
        score += 0.15
    if tag in {'input', 'select', 'textarea'}:
        score += 0.35
    # text-like matching (consider placeholder, aria-label, name as well)
    text_sources = [
        descriptor.get('text'),
        descriptor.get('placeholder'),
        descriptor.get('ariaLabel'),
        descriptor.get('aria-label'),
        descriptor.get('name'),
    ]
    text = ' '.join([str(t) for t in text_sources if t]).lower()
    if phrase_l and text:
        if phrase_l in text:
            score += 0.6
        else:
            # Weight partial matches slightly lower to keep unrelated under 0.3 for some cases
            partial = sum(1 for w in phrase_l.split() if w and w in text)
            if partial >= 2:
                score += 0.25
            elif partial == 1:
                # Keep weak partials modest to allow <0.3 for unrelated combos
                score += 0.05
    # attribute matches (include top-level id/class/name as attrs)
    attrs = dict(descriptor.get('attributes', {}) or {})
    for key in ('id', 'class', 'name', 'aria-label'):
        if key not in attrs and descriptor.get(key) is not None:
            attrs[key] = descriptor.get(key)
    if attrs.get('id') and phrase_l and phrase_l in attrs.get('id', '').lower():
        score += 0.05
    cls = attrs.get('class') or ''
    if phrase_l and cls and any(w for w in phrase_l.split() if w in cls.lower()):
        score += 0.1
    # role/name
    role = (descriptor.get('role') or '').lower()
    name = (descriptor.get('name') or '').lower()
    if phrase_l and (phrase_l in role or phrase_l in name):
        score += 0.3
    # robust CSS signal
    score += 0.15 * robust_css_score({
        'id': attrs.get('id',''),
        'class': attrs.get('class',''),
        'data-testid': attrs.get('data-testid',''),
        'data-test': attrs.get('data-test',''),
        'data-qa': attrs.get('data-qa',''),
        'aria-label': attrs.get('aria-label',''),
        'name': attrs.get('name',''),
    })
    # phrase-tag compatibility boost
    tokens = set(phrase_l.split()) if phrase_l else set()
    if tag == 'button' and 'button' in tokens:
        score += 0.06
    if 'button' in tokens and tag in {'input','select','textarea'}:
        score -= 0.15
    # action-aware adjustments
    act = (action or '').lower()
    if act == 'type' and tag in {'button', 'a'}:
        score -= 0.35
    if act == 'click' and tag == 'button':
        score += 0.1
    return max(0.0, min(1.0, score))


def rank_by_heuristics(descriptors: List[Dict[str, Any]], phrase: str = "", action: str = "", top_k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
    scored = [(d, heuristic_score(d, phrase, action)) for d in descriptors]
    scored.sort(key=lambda t: t[1], reverse=True)
    return scored[:top_k] if top_k else scored


def explain_heuristic_score(descriptor: Dict[str, Any], phrase: str = "", action: str = "") -> Dict[str, Any]:
    score = heuristic_score(descriptor, phrase, action)
    reasons: List[str] = []
    matched_properties: List[str] = []
    phrase_l = (phrase or '').lower()
    if phrase_l:
        if phrase_l in (descriptor.get('text') or '').lower():
            reasons.append('text contains phrase'); matched_properties.append('text')
        if phrase_l in (descriptor.get('name') or '').lower():
            reasons.append('name contains phrase'); matched_properties.append('name')
    if (descriptor.get('tag') or '').lower() in {'button','input'}:
        reasons.append('actionable tag')
    return {
        'score': score,
        'reasons': reasons or ['default'],
        'matched_properties': matched_properties,
    }

