"""Merge DOM and Accessibility tree descriptors."""

from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


def merge_dom_ax(
    dom_nodes: List[Dict[str, Any]],
    ax_nodes: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Merge DOM and accessibility tree nodes into unified descriptors.
    
    Args:
        dom_nodes: List of DOM node descriptors
        ax_nodes: List of accessibility tree nodes
        
    Returns:
        List of merged descriptors with both DOM and AX properties
    """
    merged = []
    
    # Create mapping of backend node IDs to AX nodes
    ax_by_id = {}
    for ax_node in ax_nodes:
        backend_id = ax_node.get("backendDOMNodeId")
        if backend_id:
            ax_by_id[backend_id] = ax_node
    
    # Merge DOM nodes with their AX counterparts
    for dom_node in dom_nodes:
        descriptor = {
            # DOM properties
            "backendNodeId": dom_node.get("backendNodeId"),
            "tag": dom_node.get("nodeName", "").lower(),
            "nodeType": dom_node.get("nodeType"),
            "nodeValue": dom_node.get("nodeValue"),
            "text": extract_text(dom_node),
            "attributes": parse_attributes(dom_node.get("attributes", [])),
            "childNodeCount": dom_node.get("childNodeCount", 0),
            "frameId": dom_node.get("frameId"),
        }
        
        # Extract common attributes
        attrs = descriptor["attributes"]
        descriptor["id"] = attrs.get("id", "")
        descriptor["classes"] = attrs.get("class", "").split() if attrs.get("class") else []
        descriptor["type"] = attrs.get("type", "")
        descriptor["name"] = attrs.get("name", "")
        descriptor["value"] = attrs.get("value", "")
        descriptor["href"] = attrs.get("href", "")
        descriptor["src"] = attrs.get("src", "")
        descriptor["placeholder"] = attrs.get("placeholder", "")
        
        # Add accessibility properties if available
        backend_id = dom_node.get("backendNodeId")
        if backend_id and backend_id in ax_by_id:
            ax_node = ax_by_id[backend_id]
            descriptor.update({
                "role": ax_node.get("role", {}).get("value", ""),
                "name": ax_node.get("name", {}).get("value", "") or descriptor.get("name", ""),
                "description": ax_node.get("description", {}).get("value", ""),
                "value": ax_node.get("value", {}).get("value", "") or descriptor.get("value", ""),
                "disabled": ax_node.get("disabled", False),
                "expanded": ax_node.get("expanded"),
                "focused": ax_node.get("focused", False),
                "modal": ax_node.get("modal", False),
                "multiline": ax_node.get("multiline", False),
                "multiselectable": ax_node.get("multiselectable", False),
                "readonly": ax_node.get("readonly", False),
                "required": ax_node.get("required", False),
                "selected": ax_node.get("selected", False),
                "checked": extract_checked_state(ax_node),
                "pressed": extract_pressed_state(ax_node),
                "level": ax_node.get("level"),
                "valueMin": ax_node.get("valueMin"),
                "valueMax": ax_node.get("valueMax"),
                "childIds": ax_node.get("childIds", []),
            })
        
        # Add ARIA attributes
        aria_attrs = {}
        for key, value in attrs.items():
            if key.startswith("aria-"):
                aria_attrs[key[5:]] = value  # Remove 'aria-' prefix
        if aria_attrs:
            descriptor["aria"] = aria_attrs
        
        # Add data attributes
        data_attrs = {}
        for key, value in attrs.items():
            if key.startswith("data-"):
                data_attrs[key[5:]] = value  # Remove 'data-' prefix
        if data_attrs:
            descriptor["data"] = data_attrs
        
        # Only include actionable elements
        if is_actionable(descriptor):
            merged.append(descriptor)
    
    logger.debug(f"Merged {len(merged)} actionable elements from {len(dom_nodes)} DOM nodes")
    return merged


def extract_text(node: Dict[str, Any]) -> str:
    """Extract visible text from a DOM node."""
    text_parts = []
    
    # Direct text content
    if node.get("nodeValue"):
        text_parts.append(node["nodeValue"])
    
    # Check for pseudo elements
    if "pseudoElements" in node:
        for pseudo in node["pseudoElements"]:
            if pseudo.get("nodeValue"):
                text_parts.append(pseudo["nodeValue"])
    
    # For input elements, use value
    if node.get("nodeName", "").lower() == "input":
        attrs = parse_attributes(node.get("attributes", []))
        if attrs.get("value"):
            text_parts.append(attrs["value"])
    
    return " ".join(text_parts).strip()


def parse_attributes(attributes: List[Any]) -> Dict[str, str]:
    """Parse attribute list into dictionary."""
    attrs = {}
    if attributes:
        # Attributes come as [name, value, name, value, ...]
        for i in range(0, len(attributes), 2):
            if i + 1 < len(attributes):
                attrs[attributes[i]] = attributes[i + 1]
    return attrs


def extract_checked_state(ax_node: Dict[str, Any]) -> Optional[str]:
    """Extract checked state from AX node."""
    checked = ax_node.get("checked")
    if checked:
        return checked.get("value")
    return None


def extract_pressed_state(ax_node: Dict[str, Any]) -> Optional[str]:
    """Extract pressed state from AX node."""
    pressed = ax_node.get("pressed")
    if pressed:
        return pressed.get("value")
    return None


def is_actionable(descriptor: Dict[str, Any]) -> bool:
    """Determine if an element is actionable (can be interacted with)."""
    tag = descriptor.get("tag", "").lower()
    role = descriptor.get("role", "").lower()
    
    # Actionable HTML elements
    actionable_tags = {
        "a", "button", "input", "select", "textarea", "option",
        "label", "summary", "details", "video", "audio"
    }
    
    # Actionable ARIA roles
    actionable_roles = {
        "button", "link", "checkbox", "radio", "textbox", "combobox",
        "listbox", "menu", "menuitem", "menuitemcheckbox", "menuitemradio",
        "option", "progressbar", "scrollbar", "searchbox", "slider",
        "spinbutton", "switch", "tab", "tabpanel", "tree", "treeitem"
    }
    
    # Check if actionable
    if tag in actionable_tags:
        return True
    
    if role in actionable_roles:
        return True
    
    # Check for click handlers (data attributes often indicate interactivity)
    if descriptor.get("data", {}).get("click"):
        return True
    
    # Check for contenteditable
    attrs = descriptor.get("attributes", {})
    if attrs.get("contenteditable") == "true":
        return True
    
    # Check for tabindex (indicates focusable/interactive)
    if attrs.get("tabindex") and attrs["tabindex"] != "-1":
        return True
    
    return False