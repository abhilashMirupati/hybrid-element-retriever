# PLACE: src/her/bridge/cdp_bridge.py
"""
CDP bridge utilities for HER.
- Provides accessors to DOM.getFlattenedDocument and Accessibility.getFullAXTree.
- Works even when Playwright isn't installed (returns empty lists).
"""
from typing import Any, Dict, List, Optional

try:
    from playwright.sync_api import Page  # type: ignore
except Exception:  # pragma: no cover
    Page = Any  # type: ignore

def get_flattened_document(page: Optional["Page"], pierce: bool = True) -> List[Dict[str, Any]]:
    """Return flattened DOM nodes via CDP, or [] if unavailable."""
    if page is None:
        return []
    try:
        client = page.context.new_cdp_session(page)
        resp = client.send("DOM.getFlattenedDocument", {"depth": -1, "pierce": pierce})
        return resp.get("nodes", [])
    except Exception:
        return []

def get_full_ax_tree(page: Optional["Page"]) -> List[Dict[str, Any]]:
    """Return full Accessibility tree via CDP, or [] if unavailable."""
    if page is None:
        return []
    try:
        client = page.context.new_cdp_session(page)
        resp = client.send("Accessibility.getFullAXTree", {})
        if isinstance(resp, dict):
            return resp.get("nodes", [])
        return resp if isinstance(resp, list) else []
    except Exception:
        return []
