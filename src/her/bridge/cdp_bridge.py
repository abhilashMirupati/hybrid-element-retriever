"""CDP bridge utilities for DOM and Accessibility tree extraction."""

from typing import Any, Dict, List, Optional, Tuple
import logging

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
    page: Optional[Page], pierce: bool = True, depth: int = -1
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

        # Try getFlattenedDocument first (Chrome 86+)
        try:
            response = client.send(
                "DOM.getFlattenedDocument", {"depth": depth, "pierce": pierce}
            )
            nodes = response.get("nodes", [])
            logger.debug(f"Retrieved {len(nodes)} DOM nodes via getFlattenedDocument")
            return nodes
        except Exception as e:
            # Fall back to getDocument if getFlattenedDocument not available
            logger.debug(
                f"getFlattenedDocument not available, falling back to getDocument: {e}"
            )

            # Get document root
            doc_response = client.send(
                "DOM.getDocument", {"depth": depth, "pierce": pierce}
            )

            root = doc_response.get("root", {})
            if not root:
                return []

            # Flatten the tree manually
            nodes = []
            _flatten_dom_tree(root, nodes)
            logger.debug(f"Retrieved {len(nodes)} DOM nodes via getDocument")
            return nodes

    except Exception as e:
        logger.error(f"Failed to get DOM document: {e}")
        return []


def _flatten_dom_tree(node: Dict[str, Any], result: List[Dict[str, Any]]) -> None:
    """Recursively flatten DOM tree.

    Args:
        node: Current DOM node
        result: List to append flattened nodes to
    """
    # Add current node
    result.append(node)

    # Process children
    children = node.get("children", [])
    for child in children:
        _flatten_dom_tree(child, result)

    # Process shadow roots
    shadow_roots = node.get("shadowRoots", [])
    for shadow in shadow_roots:
        _flatten_dom_tree(shadow, result)

    # Process content document (for iframes)
    content_doc = node.get("contentDocument")
    if content_doc:
        _flatten_dom_tree(content_doc, result)


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
    page: Optional[Page], method: str, params: Optional[Dict[str, Any]] = None
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


def get_document_with_styles(
    page: Optional[Page],
) -> Tuple[List[Dict[str, Any]], Dict[int, Dict[str, str]]]:
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
        nodes = get_flattened_document(page, pierce=True)

        # Get computed styles for each node
        styles = {}
        for node in nodes:
            node_id = node.get("nodeId")
            if node_id and node.get("nodeType") == 1:  # Element nodes only
                try:
                    style_response = client.send(
                        "CSS.getComputedStyleForNode", {"nodeId": node_id}
                    )
                    computed = style_response.get("computedStyle", [])
                    # Convert to dict
                    style_dict = {item["name"]: item["value"] for item in computed}
                    styles[node_id] = style_dict
                except Exception as style_error:
                    logger.debug(
                        f"Could not get styles for node {node_id}: {style_error}"
                    )
                    styles[node_id] = {}

        return nodes, styles

    except Exception as e:
        logger.error(f"Failed to get document with styles: {e}")
        return [], {}


def get_box_model(page: Optional[Page], node_id: int) -> Optional[Dict[str, Any]]:
    """Get box model for a specific node.

    Args:
        page: Playwright page instance
        node_id: DOM node ID

    Returns:
        Box model data or None
    """
    if not page or not PLAYWRIGHT_AVAILABLE:
        return None

    try:
        client = page.context.new_cdp_session(page)
        response = client.send("DOM.getBoxModel", {"nodeId": node_id})
        return response.get("model")
    except Exception as e:
        logger.debug(f"Failed to get box model for node {node_id}: {e}")
        return None
