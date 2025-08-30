"""Snapshot module for capturing DOM and accessibility trees via CDP."""

import asyncio
import hashlib
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import logging

from playwright.async_api import Page, CDPSession

logger = logging.getLogger(__name__)


@dataclass
class DOMNode:
    """Represents a DOM node."""
    node_id: int
    backend_node_id: int
    node_type: int
    node_name: str
    node_value: Optional[str]
    attributes: Dict[str, str]
    parent_id: Optional[int]
    frame_id: Optional[str]
    xpath: str
    css_path: str
    bounding_box: Optional[Dict[str, float]]
    is_visible: bool
    is_clickable: bool
    text_content: Optional[str]
    input_value: Optional[str]
    input_type: Optional[str]
    role: Optional[str]
    aria_label: Optional[str]
    

@dataclass 
class AXNode:
    """Represents an accessibility tree node."""
    node_id: str
    role: str
    name: Optional[str]
    value: Optional[str]
    description: Optional[str]
    properties: Dict[str, Any]
    backend_dom_node_id: Optional[int]
    

@dataclass
class Frame:
    """Represents a frame snapshot."""
    frame_id: str
    url: str
    dom_hash: str
    dom_nodes: List[DOMNode]
    ax_nodes: List[AXNode]
    parent_frame_id: Optional[str] = None
    

@dataclass
class SnapshotResult:
    """Complete snapshot result."""
    frames: List[Frame]
    total_nodes: int
    timestamp: float
    viewport: Dict[str, int]
    

class Snapshot:
    """Captures DOM and accessibility tree snapshots via CDP."""
    
    def __init__(self, page: Page):
        self.page = page
        self._cdp_session: Optional[CDPSession] = None
        self._node_cache: Dict[int, DOMNode] = {}
        
    async def _ensure_cdp(self) -> CDPSession:
        """Ensure CDP session is initialized."""
        if not self._cdp_session:
            self._cdp_session = await self.page.context.new_cdp_session(self.page)
            await self._cdp_session.send("DOM.enable")
            await self._cdp_session.send("Accessibility.enable")
            await self._cdp_session.send("Page.enable")
        return self._cdp_session
        
    async def capture(self, pierce_shadow: bool = True) -> SnapshotResult:
        """Capture complete DOM and AX tree snapshot.
        
        Args:
            pierce_shadow: Whether to pierce shadow DOM boundaries
            
        Returns:
            SnapshotResult with all frames and nodes
        """
        cdp = await self._ensure_cdp()
        
        # Get flattened DOM
        dom_result = await cdp.send("DOM.getFlattenedDocument", {
            "depth": -1,
            "pierce": pierce_shadow
        })
        
        # Get full accessibility tree
        ax_result = await cdp.send("Accessibility.getFullAXTree")
        
        # Get frame tree
        frame_tree = await cdp.send("Page.getFrameTree")
        
        # Get viewport
        viewport = await self.page.viewport_size()
        
        # Process nodes into frames
        frames = await self._process_frames(
            dom_result["nodes"],
            ax_result.get("nodes", []),
            frame_tree["frameTree"]
        )
        
        # Calculate total nodes
        total_nodes = sum(len(f.dom_nodes) for f in frames)
        
        return SnapshotResult(
            frames=frames,
            total_nodes=total_nodes,
            timestamp=asyncio.get_event_loop().time(),
            viewport=viewport or {"width": 1920, "height": 1080}
        )
        
    async def _process_frames(
        self,
        dom_nodes: List[Dict],
        ax_nodes: List[Dict],
        frame_tree: Dict
    ) -> List[Frame]:
        """Process raw CDP data into Frame objects."""
        frames = []
        
        # Build node maps
        dom_map = {n["nodeId"]: n for n in dom_nodes}
        ax_map = {n["nodeId"]: n for n in ax_nodes}
        backend_to_ax = {}
        for ax_node in ax_nodes:
            if "backendDOMNodeId" in ax_node:
                backend_to_ax[ax_node["backendDOMNodeId"]] = ax_node
        
        # Process main frame
        main_frame = await self._process_single_frame(
            frame_tree["frame"],
            dom_nodes,
            ax_nodes,
            dom_map,
            backend_to_ax
        )
        frames.append(main_frame)
        
        # Process child frames
        if "childFrames" in frame_tree:
            for child in frame_tree["childFrames"]:
                child_frame = await self._process_single_frame(
                    child["frame"],
                    dom_nodes,
                    ax_nodes,
                    dom_map,
                    backend_to_ax,
                    parent_frame_id=frame_tree["frame"]["id"]
                )
                frames.append(child_frame)
                
        return frames
        
    async def _process_single_frame(
        self,
        frame_info: Dict,
        dom_nodes: List[Dict],
        ax_nodes: List[Dict],
        dom_map: Dict,
        backend_to_ax: Dict,
        parent_frame_id: Optional[str] = None
    ) -> Frame:
        """Process a single frame."""
        frame_id = frame_info["id"]
        url = frame_info["url"]
        
        # Filter DOM nodes for this frame
        frame_dom_nodes = []
        for node in dom_nodes:
            if node.get("frameId") == frame_id or (not node.get("frameId") and not parent_frame_id):
                dom_node = await self._create_dom_node(node, dom_map, backend_to_ax)
                if dom_node:
                    frame_dom_nodes.append(dom_node)
                    
        # Filter AX nodes for this frame
        frame_ax_nodes = []
        for ax_node in ax_nodes:
            ax_obj = self._create_ax_node(ax_node)
            if ax_obj:
                frame_ax_nodes.append(ax_obj)
                
        # Calculate DOM hash
        dom_content = json.dumps([asdict(n) for n in frame_dom_nodes], sort_keys=True)
        dom_hash = hashlib.sha256(dom_content.encode()).hexdigest()[:16]
        
        return Frame(
            frame_id=frame_id,
            url=url,
            dom_hash=dom_hash,
            dom_nodes=frame_dom_nodes,
            ax_nodes=frame_ax_nodes,
            parent_frame_id=parent_frame_id
        )
        
    async def _create_dom_node(
        self,
        node_data: Dict,
        dom_map: Dict,
        backend_to_ax: Dict
    ) -> Optional[DOMNode]:
        """Create DOMNode from raw CDP data."""
        try:
            node_id = node_data["nodeId"]
            backend_id = node_data.get("backendNodeId", 0)
            
            # Extract attributes
            attributes = {}
            if "attributes" in node_data:
                attrs = node_data["attributes"]
                for i in range(0, len(attrs), 2):
                    attributes[attrs[i]] = attrs[i + 1]
                    
            # Get accessibility info
            ax_info = backend_to_ax.get(backend_id, {})
            role = ax_info.get("role", {}).get("value")
            aria_label = ax_info.get("name", {}).get("value")
            
            # Build paths
            xpath = await self._build_xpath(node_data, dom_map)
            css_path = await self._build_css_path(node_data, dom_map)
            
            # Get bounding box if available
            bbox = None
            if backend_id:
                try:
                    cdp = await self._ensure_cdp()
                    box_result = await cdp.send("DOM.getBoxModel", {
                        "backendNodeId": backend_id
                    })
                    if "model" in box_result:
                        content = box_result["model"]["content"]
                        bbox = {
                            "x": content[0],
                            "y": content[1],
                            "width": content[4] - content[0],
                            "height": content[5] - content[1]
                        }
                except:
                    pass
                    
            # Determine visibility and clickability
            is_visible = bbox is not None and bbox["width"] > 0 and bbox["height"] > 0
            is_clickable = node_data.get("nodeName", "").lower() in [
                "a", "button", "input", "select", "textarea"
            ] or attributes.get("onclick") is not None
            
            return DOMNode(
                node_id=node_id,
                backend_node_id=backend_id,
                node_type=node_data.get("nodeType", 1),
                node_name=node_data.get("nodeName", ""),
                node_value=node_data.get("nodeValue"),
                attributes=attributes,
                parent_id=node_data.get("parentId"),
                frame_id=node_data.get("frameId"),
                xpath=xpath,
                css_path=css_path,
                bounding_box=bbox,
                is_visible=is_visible,
                is_clickable=is_clickable,
                text_content=node_data.get("value"),
                input_value=attributes.get("value"),
                input_type=attributes.get("type"),
                role=role,
                aria_label=aria_label
            )
        except Exception as e:
            logger.warning(f"Failed to create DOM node: {e}")
            return None
            
    def _create_ax_node(self, ax_data: Dict) -> Optional[AXNode]:
        """Create AXNode from raw CDP data."""
        try:
            return AXNode(
                node_id=ax_data["nodeId"],
                role=ax_data.get("role", {}).get("value", "unknown"),
                name=ax_data.get("name", {}).get("value"),
                value=ax_data.get("value", {}).get("value"),
                description=ax_data.get("description", {}).get("value"),
                properties=ax_data.get("properties", {}),
                backend_dom_node_id=ax_data.get("backendDOMNodeId")
            )
        except Exception as e:
            logger.warning(f"Failed to create AX node: {e}")
            return None
            
    async def _build_xpath(self, node: Dict, dom_map: Dict) -> str:
        """Build XPath for a node."""
        path_parts = []
        current = node
        
        while current:
            node_name = current.get("nodeName", "").lower()
            if node_name == "#document":
                break
                
            # Count siblings of same type
            parent_id = current.get("parentId")
            if parent_id and parent_id in dom_map:
                parent = dom_map[parent_id]
                siblings = [n for n in dom_map.values() 
                           if n.get("parentId") == parent_id 
                           and n.get("nodeName", "").lower() == node_name]
                if len(siblings) > 1:
                    index = siblings.index(current) + 1
                    path_parts.insert(0, f"{node_name}[{index}]")
                else:
                    path_parts.insert(0, node_name)
            else:
                path_parts.insert(0, node_name)
                
            current = dom_map.get(parent_id) if parent_id else None
            
        return "//" + "/".join(path_parts) if path_parts else "/"
        
    async def _build_css_path(self, node: Dict, dom_map: Dict) -> str:
        """Build CSS selector path for a node."""
        path_parts = []
        current = node
        
        while current:
            node_name = current.get("nodeName", "").lower()
            if node_name == "#document":
                break
                
            # Build selector for current node
            selector = node_name
            
            # Add ID if present
            attrs = current.get("attributes", [])
            for i in range(0, len(attrs), 2):
                if attrs[i] == "id" and attrs[i + 1]:
                    selector = f"#{attrs[i + 1]}"
                    path_parts.insert(0, selector)
                    return " > ".join(path_parts) if path_parts else selector
                elif attrs[i] == "class" and attrs[i + 1]:
                    classes = attrs[i + 1].strip().split()
                    if classes:
                        selector += "." + ".".join(classes[:2])  # Limit classes
                        
            # Add index if needed
            parent_id = current.get("parentId")
            if parent_id and parent_id in dom_map:
                siblings = [n for n in dom_map.values()
                           if n.get("parentId") == parent_id
                           and n.get("nodeName", "").lower() == node_name]
                if len(siblings) > 1:
                    index = siblings.index(current) + 1
                    selector += f":nth-of-type({index})"
                    
            path_parts.insert(0, selector)
            current = dom_map.get(parent_id) if parent_id else None
            
        return " > ".join(path_parts) if path_parts else "*"