"""CDP bridge utilities for DOM and Accessibility tree extraction with full shadow DOM and iframe support."""

from typing import Any, Dict, List, Optional, Tuple
import logging
import hashlib
import json
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

try:
    from playwright.sync_api import Page, CDPSession, Frame

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    logger.warning("Playwright not available, CDP bridge will return empty data")
    Page = Any
    CDPSession = Any
    Frame = Any
    PLAYWRIGHT_AVAILABLE = False


@dataclass
class DOMSnapshot:
    """Complete DOM snapshot with accessibility information."""

    dom_nodes: List[Dict[str, Any]] = field(default_factory=list)
    ax_nodes: List[Dict[str, Any]] = field(default_factory=list)
    frames: Dict[str, "DOMSnapshot"] = field(default_factory=dict)
    shadow_roots: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    dom_hash: str = ""
    timestamp: float = 0.0
    url: str = ""

    def compute_hash(self) -> str:
        """Compute hash of DOM structure for change detection."""
        content = json.dumps(
            {
                "nodes": len(self.dom_nodes),
                "ax": len(self.ax_nodes),
                "frames": list(self.frames.keys()),
                "shadows": list(self.shadow_roots.keys()),
            },
            sort_keys=True,
        )
        return hashlib.md5(content.encode()).hexdigest()


def wait_for_dom_stable(page: Page, timeout_ms: int = 5000) -> bool:
    """Wait for DOM to be stable (no mutations, network idle).

    Args:
        page: Playwright page instance
        timeout_ms: Maximum time to wait

    Returns:
        True if DOM is stable, False if timeout
    """
    if not page or not PLAYWRIGHT_AVAILABLE:
        return False

    try:
        # Wait for document ready state
        page.wait_for_load_state("domcontentloaded", timeout=timeout_ms)
        page.wait_for_load_state("networkidle", timeout=timeout_ms)

        # Additional wait for any async rendering
        page.wait_for_timeout(100)

        return True
    except Exception as e:
        logger.warning(f"DOM not stable within timeout: {e}")
        return False


def get_flattened_document(
    page: Optional[Page], pierce: bool = True, depth: int = -1, wait_stable: bool = True
) -> List[Dict[str, Any]]:
    """Get flattened DOM via CDP DOM.getFlattenedDocument with stability check.

    Args:
        page: Playwright page instance
        pierce: Whether to pierce shadow DOM
        depth: Maximum depth (-1 for unlimited)
        wait_stable: Wait for DOM to be stable first

    Returns:
        List of DOM node descriptors
    """
    if not page or not PLAYWRIGHT_AVAILABLE:
        return []

    # Wait for DOM stability if requested
    if wait_stable:
        wait_for_dom_stable(page)

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


def get_full_ax_tree(
    page: Optional[Page], include_frames: bool = True
) -> List[Dict[str, Any]]:
    """Get full accessibility tree via CDP Accessibility.getFullAXTree.

    Args:
        page: Playwright page instance
        include_frames: Whether to include iframe AX trees

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

        logger.debug(f"Retrieved {len(nodes)} AX nodes from main frame")

        # Get AX trees from iframes if requested
        if include_frames:
            for frame in page.frames:
                if frame != page.main_frame:
                    try:
                        frame_nodes = get_full_ax_tree_for_frame(frame)
                        nodes.extend(frame_nodes)
                    except Exception as frame_error:
                        logger.debug(f"Could not get AX tree for frame: {frame_error}")

        return nodes

    except Exception as e:
        logger.error(f"Failed to get accessibility tree: {e}")
        return []


def get_full_ax_tree_for_frame(frame: Frame) -> List[Dict[str, Any]]:
    """Get accessibility tree for a specific frame.

    Args:
        frame: Playwright frame instance

    Returns:
        List of AX nodes for the frame
    """
    if not frame or not PLAYWRIGHT_AVAILABLE:
        return []

    try:
        # Execute in frame context
        ax_data = frame.evaluate(
            """
            () => {
                const collectAXNodes = (element) => {
                    const nodes = [];
                    const walker = document.createTreeWalker(
                        element,
                        NodeFilter.SHOW_ELEMENT,
                        null,
                        false
                    );

                    let node = walker.nextNode();
                    while (node) {
                        const axNode = {
                            role: node.getAttribute('role') || '',
                            name: node.getAttribute('aria-label') || node.innerText || '',
                            value: node.value || '',
                            description: node.getAttribute('aria-description') || '',
                            nodeId: nodes.length
                        };
                        nodes.push(axNode);
                        node = walker.nextNode();
                    }
                    return nodes;
                };
                return collectAXNodes(document.body);
            }
        """
        )
        return ax_data or []
    except Exception as e:
        logger.debug(f"Could not get frame AX tree: {e}")
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


def capture_complete_snapshot(
    page: Page,
    include_styles: bool = False,
    include_frames: bool = True,
    wait_stable: bool = True,
) -> DOMSnapshot:
    """Capture complete DOM snapshot with all information.

    Args:
        page: Playwright page instance
        include_styles: Whether to include computed styles
        include_frames: Whether to include iframe content
        wait_stable: Wait for DOM stability first

    Returns:
        Complete DOM snapshot
    """
    import time

    if not page or not PLAYWRIGHT_AVAILABLE:
        return DOMSnapshot()

    snapshot = DOMSnapshot(timestamp=time.time(), url=page.url)

    # Get flattened DOM
    snapshot.dom_nodes = get_flattened_document(
        page, pierce=True, wait_stable=wait_stable
    )

    # Get accessibility tree
    snapshot.ax_nodes = get_full_ax_tree(page, include_frames=include_frames)

    # Process frames
    if include_frames:
        for frame in page.frames:
            if frame != page.main_frame:
                try:
                    frame_snapshot = DOMSnapshot(
                        dom_nodes=get_flattened_document_for_frame(frame),
                        ax_nodes=get_full_ax_tree_for_frame(frame),
                        url=frame.url,
                    )
                    snapshot.frames[frame.name or frame.url] = frame_snapshot
                except Exception as e:
                    logger.debug(f"Could not snapshot frame {frame.url}: {e}")

    # Detect and collect shadow roots
    shadow_hosts = page.query_selector_all("[shadowroot]")
    for host in shadow_hosts:
        try:
            shadow_content = host.evaluate(
                """
                (element) => {
                    const collectShadowDOM = (root) => {
                        const nodes = [];
                        const walker = document.createTreeWalker(
                            root,
                            NodeFilter.SHOW_ELEMENT,
                            null,
                            false
                        );

                        let node = walker.nextNode();
                        while (node) {
                            nodes.push({
                                tagName: node.tagName,
                                id: node.id,
                                className: node.className,
                                attributes: Array.from(node.attributes).map(a => ({
                                    name: a.name,
                                    value: a.value
                                }))
                            });
                            node = walker.nextNode();
                        }
                        return nodes;
                    };

                    if (element.shadowRoot) {
                        return collectShadowDOM(element.shadowRoot);
                    }
                    return [];
                }
            """
            )
            if shadow_content:
                host_id = (
                    host.get_attribute("id") or host.get_attribute("class") or "unknown"
                )
                snapshot.shadow_roots[host_id] = shadow_content
        except Exception as e:
            logger.debug(f"Could not collect shadow DOM: {e}")

    # Compute hash for change detection
    snapshot.dom_hash = snapshot.compute_hash()

    return snapshot


def get_flattened_document_for_frame(frame: Frame) -> List[Dict[str, Any]]:
    """Get flattened DOM for a specific frame.

    Args:
        frame: Playwright frame instance

    Returns:
        List of DOM nodes
    """
    if not frame or not PLAYWRIGHT_AVAILABLE:
        return []

    try:
        # Execute in frame context
        dom_data = frame.evaluate(
            """
            () => {
                const collectNodes = (element) => {
                    const nodes = [];
                    const walker = document.createTreeWalker(
                        element,
                        NodeFilter.SHOW_ELEMENT,
                        null,
                        false
                    );

                    let node = walker.nextNode();
                    while (node) {
                        const domNode = {
                            nodeType: node.nodeType,
                            nodeName: node.nodeName,
                            nodeValue: node.nodeValue,
                            localName: node.localName,
                            attributes: Array.from(node.attributes || []).map(a => ({
                                name: a.name,
                                value: a.value
                            })),
                            nodeId: nodes.length
                        };
                        nodes.push(domNode);
                        node = walker.nextNode();
                    }
                    return nodes;
                };
                return collectNodes(document.body);
            }
        """
        )
        return dom_data or []
    except Exception as e:
        logger.debug(f"Could not get frame DOM: {e}")
        return []


def detect_dom_changes(snapshot1: DOMSnapshot, snapshot2: DOMSnapshot) -> bool:
    """Detect if DOM has changed between snapshots.

    Args:
        snapshot1: First snapshot
        snapshot2: Second snapshot

    Returns:
        True if DOM has changed
    """
    return snapshot1.dom_hash != snapshot2.dom_hash


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
