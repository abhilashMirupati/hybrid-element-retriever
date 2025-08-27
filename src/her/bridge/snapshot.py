# PLACE: src/her/bridge/snapshot.py
"""
Snapshot utilities:
- capture_snapshot(page) -> (descriptors, dom_hash)
- Descriptors join flattened DOM and AX tree by backendNodeId.
"""
from typing import Any, Dict, List, Optional, Tuple
from .cdp_bridge import get_flattened_document, get_full_ax_tree
from ..utils import sha1_of

try:
    from playwright.sync_api import Page  # type: ignore
except Exception:  # pragma: no cover
    Page = Any  # type: ignore

def _index_ax(ax_nodes: List[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
    by_backend = {}
    for n in ax_nodes or []:
        bid = n.get("backendDOMNodeId") or n.get("backendNodeId")
        if isinstance(bid, int):
            by_backend[bid] = n
    return by_backend

def capture_snapshot(
    page: Optional["Page"],
    frame_path: str = "main",
    dom_max_wait_ms: int = 10000,
    network_idle_ms: int = 250,
    ax_presence_timeout_ms: int = 2000,
) -> Tuple[List[Dict[str, Any]], str]:
    dom_nodes = get_flattened_document(page, pierce=True)
    ax_nodes = get_full_ax_tree(page)
    ax_by = _index_ax(ax_nodes)
    descriptors: List[Dict[str, Any]] = []
    for n in dom_nodes:
        bid = n.get("backendNodeId")
        tag = (n.get("nodeName") or "").lower()
        text = n.get("nodeValue") or ""
        ax = ax_by.get(bid, {})
        role = (ax.get("role") or {}).get("value")
        name = (ax.get("name") or {}).get("value")
        descriptors.append({
            "backendNodeId": bid,
            "tag": tag,
            "text": text,
            "role": role,
            "name": name,
        })
    dom_hash = sha1_of(tuple((d.get("backendNodeId"), d.get("tag"), d.get("text"), d.get("role"), d.get("name")) for d in descriptors))
    return descriptors, dom_hash
