"""
Canonical element-to-text normalization for element embeddings.

Builds a robust, deterministic string from mixed DOM/AX element dicts.

Order of included signals:
  [role] [aria-label] [title] [alt] [placeholder] [name] [value] [tag]
  [id/class] [text] [href-host/path]

Whitespace is collapsed and control characters are stripped. The result
is truncated to ``max_length`` characters. When no usable signals are
present, an empty string is returned.
"""

from __future__ import annotations

from typing import Dict, Iterable, Optional, List
from urllib.parse import urlparse
import re


_CONTROL_CHARS_RE = re.compile(r"[\x00-\x1F\x7F]")
_WS_RE = re.compile(r"\s+")


def _get_attr(el: Dict, key: str) -> Optional[str]:
    """Fetch attribute from top-level or nested ``attributes`` dict.

    Returns a string if present and non-empty after stripping; otherwise None.
    """
    if key in el and el[key] is not None:
        v = str(el[key]).strip()
        if v:
            return v
    attrs = el.get("attributes") or {}
    if isinstance(attrs, dict):
        v = attrs.get(key)
        if v is not None:
            v = str(v).strip()
            if v:
                return v
    return None


def _clean(s: str) -> str:
    """Remove control chars and trim."""
    if not s:
        return ""
    s = _CONTROL_CHARS_RE.sub(" ", s)
    return s.strip()


def _collapse_ws(s: str) -> str:
    """Collapse all whitespace runs to a single space and trim."""
    if not s:
        return ""
    return _WS_RE.sub(" ", s).strip()


def _id_and_classes(el: Dict) -> str:
    ident = _get_attr(el, "id")
    classes_raw = _get_attr(el, "class") or _get_attr(el, "className")
    classes: List[str] = []
    if classes_raw:
        # Classes may be space or list separated
        classes = [c for c in re.split(r"[\s,]+", classes_raw) if c]
    parts: List[str] = []
    if ident:
        parts.append(f"#{ident}")
    parts.extend(f".{c}" for c in classes)
    return _collapse_ws(" ".join(parts))


def _href_host_path(el: Dict) -> str:
    href = _get_attr(el, "href")
    if not href:
        return ""
    try:
        parsed = urlparse(href)
        host = parsed.netloc
        path = parsed.path or "/"
        hp = f"{host}{path}"
        return _collapse_ws(hp)
    except Exception:
        return ""


def element_to_text(el: Dict, max_length: int = 1024) -> str:
    """
    Build a robust, canonical text for element embedding:
    - Deterministic order of signals:
      [role] [aria-label] [title] [alt] [placeholder] [name] [value] [tag] [id/class] [text] [href-host/path]
    - Collapse whitespace; strip control characters.
    - Truncate to max_length chars.
    - If nothing usable, return "" (caller will handle zero-vector).
    """
    parts: List[str] = []

    # 1. Semantic roles/labels
    role = _get_attr(el, "role")
    if role:
        parts.append(_clean(role))
    for key in ("aria-label", "title", "alt", "placeholder", "name", "value"):
        v = _get_attr(el, key)
        if v:
            parts.append(_clean(v))

    # 2. Tag uppercased
    tag = _get_attr(el, "tag") or _get_attr(el, "tagName")
    if tag:
        parts.append(_clean(str(tag).upper()))

    # 3. id and classes
    id_classes = _id_and_classes(el)
    if id_classes:
        parts.append(id_classes)

    # 4. Visible text content
    text = _get_attr(el, "text") or _get_attr(el, "innerText") or _get_attr(el, "content")
    if text:
        parts.append(_clean(text))

    # 5. Href host/path when present
    hp = _href_host_path(el)
    if hp:
        parts.append(hp)

    combined = _collapse_ws(" ".join(p for p in parts if p))
    if not combined:
        return ""
    if len(combined) > max_length:
        return combined[:max_length]
    return combined


__all__ = ["element_to_text", "_clean", "_collapse_ws"]

