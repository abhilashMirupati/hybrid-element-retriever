"""DOM and AX tree snapshot utilities."""
from typing import Any, Dict, List, Optional, Tuple
import hashlib
import json
import logging
from .cdp_bridge import get_flattened_document, get_full_ax_tree, get_frame_tree

logger = logging.getLogger(__name__)

try:
    from playwright.sync_api import Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    Page = Any
    PLAYWRIGHT_AVAILABLE = False


def compute_dom_hash(descriptors: List[Dict[str, Any]]) -> str:
    """Compute hash of DOM structure for change detection.
    
    Args:
        descriptors: List of element descriptors
    
    Returns:
        SHA256 hash of DOM structure
    """
    # Create signature from key attributes
    sig_parts = []
    for desc in descriptors:
        sig = (
            desc.get("backendNodeId", ""),
            desc.get("tag", ""),
            desc.get("text", "")[:50],  # Limit text length
            desc.get("role", ""),
            desc.get("name", ""),
            desc.get("id", ""),
            str(desc.get("classes", [])),
        )
        sig_parts.append(json.dumps(sig, sort_keys=True))
    
    combined = "\n".join(sig_parts)
    return hashlib.sha256(combined.encode()).hexdigest()


def index_by_backend_id(nodes: List[Dict[str, Any]], id_field: str = "backendNodeId") -> Dict[int, Dict[str, Any]]:
    """Index nodes by backend node ID.
    
    Args:
        nodes: List of nodes (DOM or AX)
        id_field: Field name containing backend node ID
    
    Returns:
        Dict mapping backend node ID to node
    """
    indexed = {}
    for node in nodes:
        # Try different field names
        backend_id = node.get(id_field) or node.get("backendDOMNodeId")
        if isinstance(backend_id, int):
            indexed[backend_id] = node
    return indexed


def merge_dom_and_ax(
    dom_nodes: List[Dict[str, Any]],
    ax_nodes: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Merge DOM and accessibility tree nodes by backend node ID.
    
    Args:
        dom_nodes: Flattened DOM nodes
        ax_nodes: Accessibility tree nodes
    
    Returns:
        List of merged element descriptors
    """
    # Index AX nodes by backend ID
    ax_by_id = index_by_backend_id(ax_nodes, "backendDOMNodeId")
    
    descriptors = []
    for dom_node in dom_nodes:
        backend_id = dom_node.get("backendNodeId")
        
        # Extract DOM attributes
        tag = (dom_node.get("nodeName") or "").lower()
        node_type = dom_node.get("nodeType", 1)
        
        # Skip non-element nodes
        if node_type != 1:  # ELEMENT_NODE
            continue
        
        # Get text content
        text = dom_node.get("nodeValue") or ""
        
        # Get attributes
        attributes = {}
        attr_list = dom_node.get("attributes", [])
        # Attributes come as flat list [name, value, name, value, ...]
        for i in range(0, len(attr_list), 2):
            if i + 1 < len(attr_list):
                attributes[attr_list[i]] = attr_list[i + 1]
        
        # Get AX node if available
        ax_node = ax_by_id.get(backend_id, {})
        
        # Extract AX properties
        ax_role = None
        ax_name = None
        ax_description = None
        ax_value = None
        ax_disabled = False
        ax_hidden = False
        
        if ax_node:
            # Role
            role_prop = ax_node.get("role", {})
            if isinstance(role_prop, dict):
                ax_role = role_prop.get("value")
            
            # Name
            name_prop = ax_node.get("name", {})
            if isinstance(name_prop, dict):
                ax_name = name_prop.get("value")
            
            # Description
            desc_prop = ax_node.get("description", {})
            if isinstance(desc_prop, dict):
                ax_description = desc_prop.get("value")
            
            # Value
            value_prop = ax_node.get("value", {})
            if isinstance(value_prop, dict):
                ax_value = value_prop.get("value")
            
            # Properties
            props = ax_node.get("properties", [])
            if isinstance(props, list):
                for prop in props:
                    if isinstance(prop, dict):
                        prop_name = prop.get("name")
                        prop_value = prop.get("value", {})
                        if prop_name == "disabled" and isinstance(prop_value, dict):
                            ax_disabled = prop_value.get("value", False)
                        elif prop_name == "hidden" and isinstance(prop_value, dict):
                            ax_hidden = prop_value.get("value", False)
        
        # Build descriptor
        descriptor = {
            "backendNodeId": backend_id,
            "tag": tag,
            "text": text or ax_name or "",
            "role": ax_role,
            "name": ax_name,
            "description": ax_description,
            "value": ax_value,
            "id": attributes.get("id"),
            "classes": attributes.get("class", "").split() if attributes.get("class") else [],
            "type": attributes.get("type"),
            "placeholder": attributes.get("placeholder"),
            "href": attributes.get("href"),
            "src": attributes.get("src"),
            "alt": attributes.get("alt"),
            "title": attributes.get("title"),
            "aria": {k[5:]: v for k, v in attributes.items() if k.startswith("aria-")},
            "data": {k[5:]: v for k, v in attributes.items() if k.startswith("data-")},
            "disabled": ax_disabled or attributes.get("disabled") is not None,
            "hidden": ax_hidden or attributes.get("hidden") is not None,
            "attributes": attributes,
        }
        
        descriptors.append(descriptor)
    
    return descriptors


def capture_snapshot(
    page: Optional[Page],
    frame_path: str = "main",
    pierce_shadow: bool = True,
    include_frames: bool = True
) -> Tuple[List[Dict[str, Any]], str]:
    """Capture complete DOM + AX snapshot.
    
    Args:
        page: Playwright page instance
        frame_path: Frame identifier
        pierce_shadow: Whether to pierce shadow DOM
        include_frames: Whether to include iframe content
    
    Returns:
        Tuple of (element_descriptors, dom_hash)
    """
    if not page or not PLAYWRIGHT_AVAILABLE:
        logger.warning("Page not available, returning empty snapshot")
        return [], ""
    
    try:
        # Get DOM nodes
        dom_nodes = get_flattened_document(page, pierce=pierce_shadow)
        
        # Get AX nodes
        ax_nodes = get_full_ax_tree(page)
        
        # Merge DOM and AX data
        descriptors = merge_dom_and_ax(dom_nodes, ax_nodes)
        
        # Add frame path to each descriptor
        for desc in descriptors:
            desc["framePath"] = frame_path
        
        # Handle iframes if requested
        if include_frames:
            frame_tree = get_frame_tree(page)
            # TODO: Recursively capture iframe content
        
        # Compute DOM hash
        dom_hash = compute_dom_hash(descriptors)
        
        logger.info(f"Captured snapshot: {len(descriptors)} elements, hash={dom_hash[:8]}...")
        
        return descriptors, dom_hash
        
    except Exception as e:
        logger.error(f"Failed to capture snapshot: {e}")
        return [], ""


def detect_dom_change(old_hash: str, new_hash: str, threshold: float = 0.0) -> bool:
    """Detect if DOM has changed significantly.
    
    Args:
        old_hash: Previous DOM hash
        new_hash: Current DOM hash  
        threshold: Change threshold (0.0 means any change)
    
    Returns:
        True if DOM has changed beyond threshold
    """
    if not old_hash or not new_hash:
        return True
    
    # For now, simple equality check
    # Could implement more sophisticated similarity metrics
    return old_hash != new_hash