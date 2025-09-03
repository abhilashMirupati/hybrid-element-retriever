from __future__ import annotations
import hashlib
from urllib.parse import urlparse
from typing import Any, Dict, Optional


def _host_path(u: str) -> str:
    try:
        p = urlparse(u or "")
        host = (p.hostname or "").lower()
        path = p.path or "/"
        # Normalize duplicate slashes
        while "//" in path:
            path = path.replace("//", "/")
        return f"{host}{path}"
    except Exception:
        return ""


def _stable_json_blob(d: Dict[str, Any]) -> str:
    # stable mini-hash for extra_context (order-independent)
    try:
        # Avoid importing json just for hashing; rely on key order of sorted items
        items = sorted(d.items(), key=lambda kv: str(kv[0]))
        material = "|".join(f"{k}={v}" for k, v in items)
    except Exception:
        material = str(d)
    return hashlib.sha1(material.encode("utf-8", errors="ignore")).hexdigest()[:8]


def make_context_key(
    url: str,
    dom_hash: Optional[str] = None,
    extra_context: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Build a compact, stable context key:
       host+path | domHash8? | xtra8?
    """
    base = _host_path(url)
    parts = [base] if base else []

    if dom_hash:
        parts.append(str(dom_hash)[:8])

    if extra_context:
        parts.append(_stable_json_blob(extra_context))

    return "|".join(parts) or "global"
