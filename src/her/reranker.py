from __future__ import annotations
from typing import List, Dict
import numpy as np
from urllib.parse import urlparse

_TAG_PRIORITY = {"BUTTON": 3, "A": 2, "INPUT": 2, "SELECT": 2, "TEXTAREA": 2, "SPAN": 1, "DIV": 0}
_ROLE_BONUS = {"button": 0.02, "link": 0.015, "textbox": 0.015}
_ACTION_ROLE_PREF = {
    "click": {"button": 0.02, "link": 0.015},
    "type":  {"textbox": 0.02, "combobox": 0.015},
    "press": {},
    "list":  {},
}

def _hostpath(href: str) -> str:
    try:
        u = urlparse(href or "")
        return (u.netloc or "") + (u.path or "")
    except Exception:
        return ""

def _bonus_href(attrs: dict, tokens: List[str]) -> float:
    hp = _hostpath((attrs or {}).get("href", ""))
    if not hp: return 0.0
    hp = hp.lower()
    for t in tokens:
        if t and t in hp:
            return 0.02
    return 0.0

def _tag_bias(tag: str) -> float:
    return 0.005 * _TAG_PRIORITY.get((tag or "").upper(), 0)

def _role_bias(attrs: dict) -> float:
    role = (attrs or {}).get("role", "").lower()
    return _ROLE_BONUS.get(role, 0.0)

def _intent_bias(action: str, attrs: dict) -> float:
    role = (attrs or {}).get("role", "").lower()
    return _ACTION_ROLE_PREF.get(action, {}).get(role, 0.0)

def _bbox_area(meta: dict) -> int:
    b = meta.get("bbox") or {}
    return max(0, int(b.get("w", 0))) * max(0, int(b.get("h", 0)))

def _depth(meta: dict) -> int:
    # approximate from xpath depth
    xp = meta.get("xpath") or ""
    return max(0, xp.count("/"))

def finalize_ranking(candidates: List[Dict], intent, dedupe_eps: float = 0.995) -> List[Dict]:
    """
    Apply small hybrid bonuses and tie-breakers.
    candidates: [{score, meta, (optional)frame_hash}]
    """
    # bonuses
    for c in candidates:
        m = c["meta"]
        c["score"] += _tag_bias(m.get("tag"))
        c["score"] += _role_bias(m.get("attrs"))
        c["score"] += _intent_bias(intent.action, m.get("attrs"))
        c["score"] += _bonus_href(m.get("attrs"), intent.label_tokens)

    # tie-break sort
    def key(c):
        m = c["meta"]
        visible = 1 if m.get("visible", True) else 0
        area = _bbox_area(m)
        depth = _depth(m)
        tagp = _TAG_PRIORITY.get((m.get("tag") or "").upper(), 0)
        return (round(c["score"], 6), visible, tagp, area, -depth)

    candidates.sort(key=key, reverse=True)

    # dedupe near-identical (by identical xpath or very close cosine if provided)
    seen = set()
    out = []
    for c in candidates:
        xp = c["meta"].get("xpath")
        dup_key = xp or f"{c['meta'].get('_dom_hash','')}"
        if dup_key in seen:
            continue
        seen.add(dup_key)
        out.append(c)

    return out
