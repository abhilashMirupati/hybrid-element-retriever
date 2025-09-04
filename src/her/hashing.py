from __future__ import annotations
import hashlib
import json
from typing import Dict, List
from urllib.parse import urlparse

# Canonical descriptor helpers
def _host_path(href: str) -> str:
    try:
        u = urlparse(href or "")
        return (u.netloc or "") + (u.path or "")
    except Exception:
        return ""

def canonical_descriptor(el: Dict) -> str:
    """
    Deterministic descriptor built from the same signals used in normalization:
    role, aria-label, title, alt, placeholder, name, value, TAG, #id/.classes, text, href(host/path)
    """
    attrs = (el.get("attrs") or {})
    tag = (el.get("tag") or "").upper()
    role = attrs.get("role") or ""
    lab = attrs.get("aria-label") or ""
    title = attrs.get("title") or ""
    alt = attrs.get("alt") or ""
    ph = attrs.get("placeholder") or ""
    name = attrs.get("name") or ""
    val = attrs.get("value") or ""
    text = el.get("text") or ""
    idv = attrs.get("id") or ""
    classes = " ".join((attrs.get("class") or "").split())
    href = _host_path(attrs.get("href") or "")
    desc = {
        "tag": tag, "role": role, "aria": lab, "title": title, "alt": alt,
        "placeholder": ph, "name": name, "value": val, "id": idv, "class": classes,
        "text": " ".join(text.split()), "href": href
    }
    return json.dumps(desc, sort_keys=True, ensure_ascii=False)

def sha1(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8", "ignore")).hexdigest()

def element_dom_hash(el: Dict) -> str:
    return sha1(canonical_descriptor(el))

def frame_hash(frame_url: str, items: List[Dict]) -> str:
    """
    Unique (enough) per frame: URL host+path + count + top-k tags.
    Avoids extra deps; deterministic.
    """
    try:
        u = urlparse(frame_url or "")
        hp = (u.netloc or "") + (u.path or "")
    except Exception:
        hp = frame_url or ""
    tags = [ (it.get("tag") or "").upper() for it in items[:50] ]
    sketch = json.dumps({"hp": hp, "n": len(items), "tags": tags[:10]}, sort_keys=True)
    return sha1(sketch)

def page_signature(url: str) -> str:
    try:
        u = urlparse(url or "")
        return sha1((u.scheme + "://" + u.netloc + u.path).lower())
    except Exception:
        return sha1(url or "")


def dom_hash(frames: List[Dict]) -> str:
    """
    Deterministic page-level DOM hash derived from per-frame sketches.

    Accepts a list of frame dicts with at least:
      - frame_url or url
      - elements/items/descriptors: list of element dicts (used for frame sketch)

    The hash is stable under frame ordering differences.
    """
    try:
        sketches: List[Dict[str, str]] = []
        for fr in (frames or []):
            url = (fr.get("frame_url") or fr.get("url") or "")
            # Resolve elements list under common keys
            elements = fr.get("elements")
            if elements is None:
                elements = fr.get("items")
            if elements is None:
                elements = fr.get("descriptors")
            if not isinstance(elements, list):
                elements = []

            fh = fr.get("frame_hash") or frame_hash(url, elements)  # type: ignore[arg-type]
            sketches.append({"u": _host_path(url), "h": fh})

        # Sort by normalized host+path to ensure determinism
        sketches.sort(key=lambda d: d["u"])  # type: ignore[index]
        blob = json.dumps(sketches, sort_keys=True, ensure_ascii=False)
        return sha1(blob)
    except Exception:
        # Fallback to best-effort
        try:
            return sha1(json.dumps(frames, sort_keys=True, default=str))
        except Exception:
            return sha1(str(frames))
