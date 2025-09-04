from __future__ import annotations

import re
from typing import Dict, Iterable
from urllib.parse import urlparse

# Collapse whitespace and strip control chars (but preserve visible spacing).
_WS = re.compile(r"\s+")
_CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")

def _clean(s: str) -> str:
    s = s or ""
    s = _CTRL.sub("", s)
    s = _WS.sub(" ", s).strip()
    return s

def _href_hostpath(href: str) -> str:
    # Keep only host + path (drop query/fragment) to avoid overfitting & noise.
    try:
        u = urlparse(href or "")
        host = u.netloc or ""
        path = u.path or ""
        out = f"{host}{path}"
        return _clean(out)[:256]
    except Exception:
        return ""

def _join(parts: Iterable[str], max_length: int) -> str:
    out = " ".join([p for p in parts if p])
    return out[:max_length]

def element_to_text(el: Dict, max_length: int = 1024) -> str:
    """
    Canonical text for element embeddings (deterministic, attribute-aware).

    Order of signals (most informative first):
    [role] [aria-label] [title] [alt] [placeholder] [name] [value]
    [TAG] [#id .classes] [visible text] [href(host/path)]
    """
    attrs = (el.get("attrs") or {})
    tag   = _clean((el.get("tag") or "").upper())
    role  = _clean(attrs.get("role") or el.get("role") or "")
    label = _clean(attrs.get("aria-label") or "")
    title = _clean(attrs.get("title") or "")
    alt   = _clean(attrs.get("alt") or "")
    ph    = _clean(attrs.get("placeholder") or "")
    name  = _clean(attrs.get("name") or "")
    val   = _clean(attrs.get("value") or "")
    text  = _clean(el.get("text") or "")

    # Compact id + class
    idp   = f"#{_clean(attrs['id'])}" if attrs.get("id") else ""
    classes = _clean(attrs.get("class") or "")
    clsp  = ("." + ".".join([c for c in classes.split() if c])) if classes else ""

    hrefp = _href_hostpath(attrs.get("href") or "")

    parts = [
        role, label, title, alt, ph, name, val,
        tag, idp + clsp, text, hrefp
    ]
    return _join(parts, max_length)
