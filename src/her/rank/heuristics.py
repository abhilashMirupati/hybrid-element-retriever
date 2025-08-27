# PLACE: src/her/rank/heuristics.py
"""Simple heuristic scorer based on tag/text/role/name."""
from typing import Dict, Any

def heuristic_score(descriptor: Dict[str, Any], phrase: str) -> float:
    p = phrase.lower()
    score = 0.0
    tag = (descriptor.get("tag") or "").lower()
    text = (descriptor.get("text") or "").lower()
    role = (descriptor.get("role") or "") or ""
    name = (descriptor.get("name") or "") or ""
    if "button" in p and tag == "button":
        score += 0.6
    if any(w in (text or "") for w in p.split()):
        score += 0.2
    if isinstance(role, str) and "button" in role.lower():
        score += 0.2
    if isinstance(name, str) and any(w in name.lower() for w in p.split()):
        score += 0.2
    return min(score, 1.0)
