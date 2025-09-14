"""Snapshot functionality for DOM and accessibility tree capture."""

from typing import Any, Dict, List, Optional
import logging

from .cdp_bridge import (
    capture_complete_snapshot,
    get_flattened_document,
    get_full_ax_tree,
    compute_dom_hash,
    detect_dom_changes,
    DOMSnapshot
)

logger = logging.getLogger(__name__)


def capture_frame_snapshot(page, include_frames: bool = True, wait_stable: bool = True) -> Dict[str, Any]:
    """Capture snapshot for a specific frame.
    
    Args:
        page: Playwright page instance
        include_frames: Whether to include iframe content
        wait_stable: Wait for DOM stability first
        
    Returns:
        Dictionary containing snapshot data
    """
    if not page:
        logger.warning("No page provided for snapshot")
        return {}
    
    try:
        snapshot = capture_complete_snapshot(
            page=page,
            include_frames=include_frames,
            wait_stable=wait_stable
        )
        
        return {
            "dom_nodes": snapshot.dom_nodes,
            "ax_nodes": snapshot.ax_nodes,
            "frames": {k: {
                "dom_nodes": v.dom_nodes,
                "ax_nodes": v.ax_nodes,
                "url": v.url
            } for k, v in snapshot.frames.items()},
            "shadow_roots": snapshot.shadow_roots,
            "dom_hash": snapshot.dom_hash,
            "timestamp": snapshot.timestamp,
            "url": snapshot.url
        }
    except Exception as e:
        logger.error(f"Failed to capture frame snapshot: {e}")
        return {}


def capture_snapshot(page, include_frames: bool = True, wait_stable: bool = True) -> Dict[str, Any]:
    """Capture complete page snapshot.
    
    Args:
        page: Playwright page instance
        include_frames: Whether to include iframe content
        wait_stable: Wait for DOM stability first
        
    Returns:
        Dictionary containing complete snapshot data
    """
    return capture_frame_snapshot(page, include_frames, wait_stable)


def compute_dom_hash(frames: List[Dict[str, Any]]) -> str:
    """Compute hash of DOM structure for change detection.
    
    Args:
        frames: List of frame data
        
    Returns:
        MD5 hash of DOM structure
    """
    try:
        return compute_dom_hash(frames)
    except Exception as e:
        logger.error(f"Failed to compute DOM hash: {e}")
        return ""


def detect_dom_change(snapshot1: Dict[str, Any], snapshot2: Dict[str, Any]) -> bool:
    """Detect if DOM has changed between snapshots.
    
    Args:
        snapshot1: First snapshot
        snapshot2: Second snapshot
        
    Returns:
        True if DOM has changed
    """
    try:
        hash1 = snapshot1.get("dom_hash", "")
        hash2 = snapshot2.get("dom_hash", "")
        return hash1 != hash2
    except Exception as e:
        logger.error(f"Failed to detect DOM change: {e}")
        return False


def get_flat_snapshot(page, include_frames: bool = True) -> Dict[str, Any]:
    """Get flattened snapshot of page elements.
    
    Args:
        page: Playwright page instance
        include_frames: Whether to include iframe content
        
    Returns:
        Flattened snapshot data
    """
    try:
        dom_nodes = get_flattened_document(page, pierce=True)
        ax_nodes = get_full_ax_tree(page, include_frames=include_frames)
        
        return {
            "dom_nodes": dom_nodes,
            "ax_nodes": ax_nodes,
            "total_nodes": len(dom_nodes),
            "total_ax_nodes": len(ax_nodes)
        }
    except Exception as e:
        logger.error(f"Failed to get flat snapshot: {e}")
        return {}


def get_flattened_document(page, pierce: bool = True, depth: int = -1, wait_stable: bool = True) -> List[Dict[str, Any]]:
    """Get flattened DOM document.
    
    Args:
        page: Playwright page instance
        pierce: Whether to pierce shadow DOM
        depth: Maximum depth (-1 for unlimited)
        wait_stable: Wait for DOM stability first
        
    Returns:
        List of DOM nodes
    """
    try:
        return get_flattened_document(page, pierce=pierce, depth=depth, wait_stable=wait_stable)
    except Exception as e:
        logger.error(f"Failed to get flattened document: {e}")
        return []


def get_full_ax_tree(page, include_frames: bool = True) -> List[Dict[str, Any]]:
    """Get full accessibility tree.
    
    Args:
        page: Playwright page instance
        include_frames: Whether to include iframe AX trees
        
    Returns:
        List of accessibility tree nodes
    """
    try:
        return get_full_ax_tree(page, include_frames=include_frames)
    except Exception as e:
        logger.error(f"Failed to get full AX tree: {e}")
        return []


def merge_dom_and_ax(dom_nodes: List[Dict[str, Any]], ax_nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Merge DOM and accessibility tree nodes.
    
    Args:
        dom_nodes: List of DOM nodes
        ax_nodes: List of accessibility nodes
        
    Returns:
        List of merged nodes
    """
    try:
        from ..descriptors.merge import merge_dom_ax
        return merge_dom_ax(dom_nodes, ax_nodes)
    except Exception as e:
        logger.error(f"Failed to merge DOM and AX: {e}")
        return []