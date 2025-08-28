from __future__ import annotations
from typing import Dict

def robust_css_score(attrs: Dict[str,str])->float:
    score=0.0; idv=attrs.get('id') or ''
    if idv:
        score+=0.6
        if any(len(tok)>=8 for tok in idv.split('-')): score-=0.3
    for k in ('data-testid','data-test','data-qa','aria-label','name'):
        if attrs.get(k): score+=0.2
    cls=attrs.get('class') or ''
    if 'active' in cls or 'selected' in cls: score+=0.1
    return max(0.0, min(1.0, score))
