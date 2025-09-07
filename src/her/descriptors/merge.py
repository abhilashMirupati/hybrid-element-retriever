"""DOM and Accessibility Tree merging functionality."""

from typing import Any, Dict, List, Optional, Tuple
import logging

from ..config import get_config, CanonicalMode

logger = logging.getLogger(__name__)


def extract_text_content(node: Dict[str, Any]) -> str:
    """
    Extract text content from a DOM node, including child text nodes.
    This is important for interactive elements where text is in child nodes.
    
    Args:
        node: DOM node with potential child nodes
        
    Returns:
        Combined text content from the node and its children
    """
    text_parts = []
    
    # Get direct text content
    node_value = node.get('nodeValue', '').strip()
    if node_value:
        text_parts.append(node_value)
    
    # Get text from accessibility tree
    if 'accessibility' in node:
        ax_name = node['accessibility'].get('name', '').strip()
        if ax_name:
            text_parts.append(ax_name)
    
    # For interactive elements, get text from attributes
    attrs = node.get('attributes', {})
    if isinstance(attrs, list):
        # Convert list format ['key1', 'value1', 'key2', 'value2'] to dict
        attrs_dict = {}
        for i in range(0, len(attrs), 2):
            if i + 1 < len(attrs):
                attrs_dict[attrs[i]] = attrs[i + 1]
        attrs = attrs_dict
    
    if isinstance(attrs, dict):
        # Priority order for text content in attributes
        text_attrs = ['aria-label', 'data-placeholder-text', 'title', 'value', 'alt']
        for attr in text_attrs:
            if attr in attrs and attrs[attr]:
                text_parts.append(attrs[attr].strip())
    
    # Get text from children (if available)
    children = node.get('children', [])
    if children:
        for child in children:
            if isinstance(child, dict):
                child_text = child.get('nodeValue', '').strip()
                if child_text:
                    text_parts.append(child_text)
    
    return ' '.join(text_parts).strip()


def merge_dom_ax(
    dom_nodes: List[Dict[str, Any]], 
    ax_nodes: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Merge DOM nodes with accessibility tree nodes using backend node IDs.
    Respects canonical descriptor building mode configuration.
    
    Args:
        dom_nodes: List of DOM nodes with backendNodeId
        ax_nodes: List of accessibility tree nodes with nodeId
        
    Returns:
        List of merged nodes with combined DOM + accessibility attributes
    """
    config = get_config()
    canonical_mode = config.get_canonical_mode()
    
    logger.debug(f"Canonical mode: {canonical_mode.value}")
    logger.debug(f"DOM nodes: {len(dom_nodes)}, Accessibility nodes: {len(ax_nodes)}")
    
    # Handle different canonical modes
    if canonical_mode == CanonicalMode.DOM_ONLY:
        logger.debug("DOM_ONLY mode: Using DOM nodes as-is")
        return dom_nodes
    
    if canonical_mode == CanonicalMode.ACCESSIBILITY_ONLY:
        logger.debug("ACCESSIBILITY_ONLY mode: Using accessibility nodes as-is")
        return ax_nodes
    
    # BOTH mode - merge DOM and accessibility tree
    if not ax_nodes:
        if config.is_accessibility_mandatory():
            logger.warning("⚠️  Accessibility extraction is mandatory but no accessibility nodes found!")
            logger.warning("   Falling back to DOM nodes only")
        else:
            logger.debug("No accessibility tree nodes available, returning DOM nodes as-is")
        return dom_nodes
    
    # Create a mapping from accessibility nodeId to accessibility data
    ax_by_id = {}
    for ax_node in ax_nodes:
        node_id = ax_node.get('nodeId')
        if node_id is not None:
            ax_by_id[node_id] = ax_node
    
    logger.debug(f"Merging {len(dom_nodes)} DOM nodes with {len(ax_by_id)} accessibility nodes")
    
    merged_nodes = []
    for dom_node in dom_nodes:
        # Get the backend node ID from DOM node
        backend_id = dom_node.get('backendNodeId')
        if backend_id is None:
            # If no backend ID, use the DOM node as-is
            merged_nodes.append(dom_node)
            continue
            
        # Find matching accessibility node
        ax_node = ax_by_id.get(backend_id)
        if ax_node is None:
            # No matching accessibility node, use DOM node as-is but still extract text
            merged_node = dom_node.copy()
        else:
            # Merge DOM and accessibility attributes based on mode
            merged_node = merge_node_attributes(dom_node, ax_node, canonical_mode)
        
        # Extract text content for better MiniLM matching - ALWAYS do this
        text_content = extract_text_content(merged_node)
        merged_node['text'] = text_content  # Always store text content, even if empty
        
        merged_nodes.append(merged_node)
    
    logger.debug(f"Successfully merged {len(merged_nodes)} nodes")
    return merged_nodes


def merge_node_attributes(dom_node: Dict[str, Any], ax_node: Dict[str, Any], canonical_mode: CanonicalMode = CanonicalMode.BOTH) -> Dict[str, Any]:
    """
    Merge attributes from DOM and accessibility tree nodes based on canonical mode.
    
    Args:
        dom_node: DOM node with attributes
        ax_node: Accessibility tree node with accessibility properties
        canonical_mode: Canonical descriptor building mode
        
    Returns:
        Merged node with combined attributes
    """
    config = get_config()
    
    if canonical_mode == CanonicalMode.DOM_ONLY:
        # DOM only mode - return DOM node as-is
        return dom_node
    
    if canonical_mode == CanonicalMode.ACCESSIBILITY_ONLY:
        # Accessibility only mode - return accessibility node as-is
        return ax_node
    
    # BOTH mode - merge DOM and accessibility tree
    # Start with DOM node as base
    merged = dom_node.copy()
    
    # Get existing attributes or create new dict
    attrs = merged.get('attributes', {})
    if isinstance(attrs, list):
        # Convert alternating [name, value] entries to dictionary
        attrs_dict = {}
        for i in range(0, len(attrs), 2):
            if i + 1 < len(attrs):
                attrs_dict[str(attrs[i])] = attrs[i + 1]
        attrs = attrs_dict
    
    # Add accessibility tree properties as attributes
    ax_props = {
        'role': ax_node.get('role', ''),
        'name': ax_node.get('name', ''),
        'value': ax_node.get('value', ''),
        'description': ax_node.get('description', ''),
        'checked': ax_node.get('checked', ''),
        'selected': ax_node.get('selected', ''),
        'expanded': ax_node.get('expanded', ''),
        'disabled': ax_node.get('disabled', ''),
        'focused': ax_node.get('focused', ''),
        'modal': ax_node.get('modal', ''),
        'multiline': ax_node.get('multiline', ''),
        'multiselectable': ax_node.get('multiselectable', ''),
        'readonly': ax_node.get('readonly', ''),
        'required': ax_node.get('required', ''),
        'autocomplete': ax_node.get('autocomplete', ''),
        'haspopup': ax_node.get('haspopup', ''),
        'level': ax_node.get('level', ''),
        'valuemin': ax_node.get('valuemin', ''),
        'valuemax': ax_node.get('valuemax', ''),
        'valuetext': ax_node.get('valuetext', ''),
        'orientation': ax_node.get('orientation', ''),
        'setsize': ax_node.get('setsize', ''),
        'posinset': ax_node.get('posinset', ''),
        'activedescendant': ax_node.get('activedescendant', ''),
        'controls': ax_node.get('controls', ''),
        'describedby': ax_node.get('describedby', ''),
        'flowto': ax_node.get('flowto', ''),
        'labelledby': ax_node.get('labelledby', ''),
        'owns': ax_node.get('owns', ''),
        'live': ax_node.get('live', ''),
        'atomic': ax_node.get('atomic', ''),
        'relevant': ax_node.get('relevant', ''),
        'busy': ax_node.get('busy', ''),
        'current': ax_node.get('current', ''),
        'invalid': ax_node.get('invalid', ''),
        'keyshortcuts': ax_node.get('keyshortcuts', ''),
        'roledescription': ax_node.get('roledescription', '')
    }
    
    # Only add non-empty accessibility properties
    for key, value in ax_props.items():
        if value and str(value).strip():
            attrs[key] = str(value).strip()
    
    # Update the merged node with combined attributes
    merged['attributes'] = attrs
    
    # Add accessibility metadata
    merged['accessibility'] = {
        'role': ax_node.get('role', ''),
        'name': ax_node.get('name', ''),
        'description': ax_node.get('description', ''),
        'value': ax_node.get('value', ''),
        'nodeId': ax_node.get('nodeId', ''),
        'backendNodeId': ax_node.get('backendNodeId', ''),
        'childIds': ax_node.get('childIds', []),
        'parentId': ax_node.get('parentId', ''),
        'frameId': ax_node.get('frameId', '')
    }
    
    return merged


def get_enhanced_text_content(dom_node: Dict[str, Any], ax_node: Dict[str, Any]) -> str:
    """
    Get enhanced text content combining DOM text with accessibility name.
    
    Args:
        dom_node: DOM node with text content
        ax_node: Accessibility tree node with name
        
    Returns:
        Enhanced text content prioritizing accessibility name
    """
    # Get text from DOM
    dom_text = dom_node.get('text', '').strip()
    
    # Get name from accessibility tree
    ax_name = ax_node.get('name', '').strip()
    
    # Prioritize accessibility name if available and meaningful
    if ax_name and len(ax_name) > 0:
        # If accessibility name is more descriptive, use it
        if len(ax_name) > len(dom_text) or not dom_text:
            return ax_name
        # If both are available, combine them
        elif dom_text and ax_name != dom_text:
            return f"{ax_name} {dom_text}".strip()
    
    # Fall back to DOM text
    return dom_text


def enhance_element_descriptor(element: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enhance element descriptor with accessibility information.
    
    Args:
        element: Element descriptor from DOM
        
    Returns:
        Enhanced element descriptor
    """
    # Get accessibility data if available
    accessibility = element.get('accessibility', {})
    
    # Enhance text content
    if accessibility:
        enhanced_text = get_enhanced_text_content(element, accessibility)
        if enhanced_text:
            element['text'] = enhanced_text
    
    # Add accessibility-specific metadata
    element['is_accessible'] = bool(accessibility.get('role'))
    element['accessibility_role'] = accessibility.get('role', '')
    element['accessibility_name'] = accessibility.get('name', '')
    element['accessibility_description'] = accessibility.get('description', '')
    
    return element