"""CDP bridge utilities for DOM and Accessibility tree extraction."""
from typing import Any, Dict, List, Optional, Tuple
import logging
import json

logger = logging.getLogger(__name__)

try:
    from playwright.sync_api import Page, CDPSession
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    logger.warning("Playwright not available, CDP bridge will return empty data")
    Page = Any
    CDPSession = Any
    PLAYWRIGHT_AVAILABLE = False


def get_flattened_document(
    page: Optional[Page],
    pierce: bool = True,
    depth: int = -1
) -> List[Dict[str, Any]]:
    """Get flattened DOM via CDP DOM.getFlattenedDocument.
    
    Args:
        page: Playwright page instance
        pierce: Whether to pierce shadow DOM
        depth: Maximum depth (-1 for unlimited)
    
    Returns:
        List of DOM node descriptors
    """
    if not page or not PLAYWRIGHT_AVAILABLE:
        return []
    
    try:
        # Create CDP session
        client = page.context.new_cdp_session(page)
        
        # Enable DOM domain
        client.send("DOM.enable")
        
        # Get flattened document
        response = client.send("DOM.getFlattenedDocument", {
            "depth": depth,
            "pierce": pierce
        })
        
        nodes = response.get("nodes", [])
        logger.debug(f"Retrieved {len(nodes)} DOM nodes")
        
        return nodes
        
    except Exception as e:
        logger.error(f"Failed to get flattened document: {e}")
        return []


def get_full_ax_tree(page: Optional[Page]) -> List[Dict[str, Any]]:
    """Get full accessibility tree via CDP Accessibility.getFullAXTree.
    
    Args:
        page: Playwright page instance
    
    Returns:
        List of accessibility tree nodes
    """
    if not page or not PLAYWRIGHT_AVAILABLE:
        return []
    
    try:
        # Create CDP session
        client = page.context.new_cdp_session(page)
        
        # Enable Accessibility domain
        client.send("Accessibility.enable")
        
        # Get full AX tree
        response = client.send("Accessibility.getFullAXTree", {})
        
        # Handle response format variations
        if isinstance(response, dict):
            nodes = response.get("nodes", [])
        elif isinstance(response, list):
            nodes = response
        else:
            nodes = []
        
        logger.debug(f"Retrieved {len(nodes)} AX nodes")
        
        return nodes
        
    except Exception as e:
        logger.error(f"Failed to get accessibility tree: {e}")
        return []


def get_frame_tree(page: Optional[Page]) -> Dict[str, Any]:
    """Get frame tree structure via CDP Page.getFrameTree.
    
    Args:
        page: Playwright page instance
    
    Returns:
        Frame tree structure
    """
    if not page or not PLAYWRIGHT_AVAILABLE:
        return {}
    
    try:
        client = page.context.new_cdp_session(page)
        response = client.send("Page.getFrameTree")
        return response.get("frameTree", {})
    except Exception as e:
        logger.error(f"Failed to get frame tree: {e}")
        return {}


def execute_cdp_command(
    page: Optional[Page],
    method: str,
    params: Optional[Dict[str, Any]] = None
) -> Any:
    """Execute arbitrary CDP command.
    
    Args:
        page: Playwright page instance
        method: CDP method name
        params: Method parameters
    
    Returns:
        CDP response
    """
    if not page or not PLAYWRIGHT_AVAILABLE:
        return None
    
    try:
        client = page.context.new_cdp_session(page)
        return client.send(method, params or {})
    except Exception as e:
        logger.error(f"Failed to execute CDP command {method}: {e}")
        return None


def get_document_with_styles(page: Optional[Page]) -> Tuple[List[Dict[str, Any]], Dict[int, Dict[str, str]]]:
    """Get DOM nodes with computed styles.
    
    Args:
        page: Playwright page instance
    
    Returns:
        Tuple of (nodes, styles_by_node_id)
    """
    if not page or not PLAYWRIGHT_AVAILABLE:
        return [], {}
    
    try:
        client = page.context.new_cdp_session(page)
        
        # Enable necessary domains
        client.send("DOM.enable")
        client.send("CSS.enable")
        
        # Get document
        nodes = get_flattened_document(page)
        
        # Get computed styles for each node
        styles = {}
        for node in nodes:
            node_id = node.get("nodeId")
            if node_id:
                try:
                    style_response = client.send("CSS.getComputedStyleForNode", {
                        "nodeId": node_id
                    })
                    computed = style_response.get("computedStyle", [])
                    # Convert to dict
                    style_dict = {item["name"]: item["value"] for item in computed}
                    styles[node_id] = style_dict
                except:
                    pass
        
        return nodes, styles
        
    except Exception as e:
        logger.error(f"Failed to get document with styles: {e}")
        return [], {}