from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional

_ACTION_ALIASES = {
    "click": {"click","tap","press","hit","open","choose","select"},
    "type":  {"type","enter","fill","input","write","set"},
    "press": {"press","hit","send"},
    "list":  {"list","show","find all","get all"},
}

@dataclass
class Intent:
    action: str
    target: str
    value: Optional[str] = None
    raw: str = ""
    label_tokens: List[str] = None

def _guess_action(q: str) -> str:
    ql = q.lower()
    for act, kws in _ACTION_ALIASES.items():
        if any(k in ql for k in kws):
            return act
    # default to click for UI
    return "click"

def _extract_value(q: str) -> Optional[str]:
    # type "VALUE" into TARGET
    m = re.search(r'(?:type|enter|fill|set)\s+"([^"]+)"\s+into\s+(.+)$', q, re.I)
    if m:
        return m.group(1)
    m = re.search(r'(?:type|enter|fill|set)\s+([^\s].*?)\s+into\s+(.+)$', q, re.I)
    if m:
        return m.group(1)
    return None

def _extract_target(q: str) -> str:
    ql = q.strip()
    # try "into TARGET"
    m = re.search(r'into\s+(.+)$', ql, re.I)
    if m:
        return m.group(1).strip().strip('"')
    # try after action verb
    m = re.search(r'^(?:click|tap|press|open|select|choose)\s+(.+)$', ql, re.I)
    if m:
        return m.group(1).strip().strip('"')
    # else remainder
    return ql

def _label_tokens(s: str) -> List[str]:
    # rudimentary tokenizer for promotion lookup
    return [t for t in re.split(r'[^a-z0-9]+', s.lower()) if t]

def parse_intent(query: str) -> Intent:
    act = _guess_action(query)
    val = _extract_value(query)
    tgt = _extract_target(query)
    return Intent(action=act, target=tgt, value=val, raw=query, label_tokens=_label_tokens(tgt))
