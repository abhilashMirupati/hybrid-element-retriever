"""DOM and AX tree snapshot capture and merging."""
from typing import Any, Dict, List, Optional, Tuple, Set
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
    # Create stable representation
    stable_parts = []
    
    for desc in descriptors:
        parts = [
            desc.get("tagName", ""),
            desc.get("text", "")[:100],  # Truncate text for stability
            str(desc.get("attributes", {}).get("id", "")),
            str(desc.get("attributes", {}).get("class", "")),
            desc.get("role", ""),
            desc.get("framePath", "")
        ]
        stable_parts.append("|".join(parts))
    
    # Sort for consistency
    stable_parts.sort()
    
    # Compute hash
    content = "\n".join(stable_parts)
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def merge_dom_and_ax(
    dom_nodes: List[Dict[str, Any]],
    ax_nodes: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Merge DOM and accessibility tree data.
    
    Args:
        dom_nodes: List of DOM nodes
        ax_nodes: List of accessibility nodes
    
    Returns:
        List of merged element descriptors
    """
    descriptors = []
    
    # Create mapping of backend node IDs to AX data
    ax_by_backend = {}
    for ax_node in ax_nodes:
        backend_id = ax_node.get("backendDOMNodeId")
        if backend_id:
            ax_by_backend[backend_id] = ax_node
    
    # Process DOM nodes
    for dom_node in dom_nodes:
        # Skip non-element nodes
        node_type = dom_node.get("nodeType")
        if node_type != 1:  # Not an element
            continue
        
        # Extract basic info
        descriptor = {
            "nodeId": dom_node.get("nodeId"),
            "backendNodeId": dom_node.get("backendNodeId"),
            "tagName": dom_node.get("nodeName", "").lower(),
            "attributes": {},
            "text": "",
            "visible": True,
            "role": "",
            "name": "",
            "description": "",
            "value": "",
            "disabled": False,
            "checked": False,
            "selected": False,
            "focused": False,
            "framePath": ""
        }
        
        # Parse attributes
        attr_list = dom_node.get("attributes", [])
        # Attributes come as flat list [name, value, name, value, ...]
        for i in range(0, len(attr_list), 2):
            if i + 1 < len(attr_list):
                attr_name = attr_list[i]
                attr_value = attr_list[i + 1]
                descriptor["attributes"][attr_name] = attr_value
        
        # Get text content
        node_value = dom_node.get("nodeValue", "")
        if node_value:
            descriptor["text"] = node_value.strip()
        
        # Look for child text nodes
        children = dom_node.get("children", [])
        text_parts = []
        for child in children:
            if child.get("nodeType") == 3:  # Text node
                child_text = child.get("nodeValue", "").strip()
                if child_text:
                    text_parts.append(child_text)
        if text_parts and not descriptor["text"]:
            descriptor["text"] = " ".join(text_parts)
        
        # Merge accessibility data if available
        backend_id = descriptor.get("backendNodeId")
        if backend_id and backend_id in ax_by_backend:
            ax_data = ax_by_backend[backend_id]
            
            # Role
            role = ax_data.get("role", {})
            if isinstance(role, dict):
                descriptor["role"] = role.get("value", "")
            elif isinstance(role, str):
                descriptor["role"] = role
            
            # Name
            name = ax_data.get("name", {})
            if isinstance(name, dict):
                descriptor["name"] = name.get("value", "")
            elif isinstance(name, str):
                descriptor["name"] = name
            
            # Description
            description = ax_data.get("description", {})
            if isinstance(description, dict):
                descriptor["description"] = description.get("value", "")
            elif isinstance(description, str):
                descriptor["description"] = description
            
            # Value
            value = ax_data.get("value", {})
            if isinstance(value, dict):
                descriptor["value"] = value.get("value", "")
            elif isinstance(value, str):
                descriptor["value"] = value
            
            # Properties
            properties = ax_data.get("properties", [])
            for prop in properties:
                prop_name = prop.get("name", "")
                prop_value = prop.get("value", {})
                
                if prop_name == "disabled" and prop_value.get("value"):
                    descriptor["disabled"] = True
                elif prop_name == "checked" and prop_value.get("value"):
                    descriptor["checked"] = True
                elif prop_name == "selected" and prop_value.get("value"):
                    descriptor["selected"] = True
                elif prop_name == "focused" and prop_value.get("value"):
                    descriptor["focused"] = True
                elif prop_name == "hidden" and prop_value.get("value"):
                    descriptor["visible"] = False
        
        # Add to descriptors
        descriptors.append(descriptor)
    
    return descriptors


def capture_frame_snapshot(
    page: Page,
    frame_info: Dict[str, Any],
    frame_path: str = "",
    visited_frames: Optional[Set[str]] = None
) -> List[Dict[str, Any]]:
    """Recursively capture snapshot for a frame and its children.
    
    Args:
        page: Playwright page instance
        frame_info: Frame tree info from CDP
        frame_path: Path to this frame (e.g., "0.1.2")
        visited_frames: Set of already visited frame IDs to prevent loops
    
    Returns:
        List of element descriptors for this frame and children
    """
    if visited_frames is None:
        visited_frames = set()
    
    frame_id = frame_info.get("frame", {}).get("id", "")
    
    # Prevent infinite loops
    if frame_id in visited_frames:
        return []
    visited_frames.add(frame_id)
    
    descriptors = []
    
    try:
        # Get frame handle
        frame_url = frame_info.get("frame", {}).get("url", "")
        
        # Find matching Playwright frame
        pw_frame = None
        for f in page.frames:
            if f.url == frame_url or f.name == frame_info.get("frame", {}).get("name", ""):
                pw_frame = f
                break
        
        if pw_frame:
            # Get DOM and AX data for this frame
            # Note: This is simplified - real implementation would use CDP per frame
            dom_nodes = get_flattened_document(pw_frame, pierce=True)
            ax_nodes = get_full_ax_tree(pw_frame)
            
            # Merge and add frame path
            frame_descriptors = merge_dom_and_ax(dom_nodes, ax_nodes)
            for desc in frame_descriptors:
                desc["framePath"] = frame_path
            
            descriptors.extend(frame_descriptors)
    
    except Exception as e:
        logger.warning(f"Failed to capture frame {frame_id}: {e}")
    
    # Process child frames recursively
    child_frames = frame_info.get("childFrames", [])
    for i, child in enumerate(child_frames):
        child_path = f"{frame_path}.{i}" if frame_path else str(i)
        child_descriptors = capture_frame_snapshot(page, child, child_path, visited_frames)
        descriptors.extend(child_descriptors)
    
    return descriptors


def capture_snapshot(
    page: Optional[Page],
    include_frames: bool = True,
    frame_path: str = ""
) -> Tuple[List[Dict[str, Any]], str]:
    """Capture full DOM and AX tree snapshot.
    
    Args:
        page: Playwright page instance
        include_frames: Whether to include iframe content
        frame_path: Frame path for nested frames
    
    Returns:
        Tuple of (element_descriptors, dom_hash)
    """
    if not page or not PLAYWRIGHT_AVAILABLE:
        return [], ""
    
    try:
        # Get DOM nodes with shadow DOM piercing
        dom_nodes = get_flattened_document(page, pierce=True)
        
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
            if frame_tree:
                # Recursively capture iframe content
                child_frames = frame_tree.get("childFrames", [])
                for i, child_frame in enumerate(child_frames):
                    child_path = f"{frame_path}.{i}" if frame_path else str(i)
                    frame_descriptors = capture_frame_snapshot(page, child_frame, child_path)
                    descriptors.extend(frame_descriptors)
        
        # Compute DOM hash
        dom_hash = compute_dom_hash(descriptors)
        
        logger.info(f"Captured snapshot: {len(descriptors)} elements, hash={dom_hash[:8]}")
        
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