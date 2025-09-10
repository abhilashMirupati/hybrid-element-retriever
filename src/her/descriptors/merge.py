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
        ax_name = node['accessibility'].get('name', '')
        if ax_name:
            clean_name = extract_clean_text(ax_name)
            if clean_name:
                text_parts.append(clean_name)
    
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
        logger.debug("ACCESSIBILITY_ONLY mode: Converting accessibility nodes to element descriptors")
        # Convert accessibility nodes to element descriptors
        processed_nodes = []
        for ax_node in ax_nodes:
            # Convert accessibility node to element descriptor format
            element_descriptor = convert_accessibility_to_element(ax_node)
            if element_descriptor:
                processed_nodes.append(element_descriptor)
        logger.debug(f"ACCESSIBILITY_ONLY mode: Processed {len(processed_nodes)} accessibility nodes")
        return processed_nodes
    
    # BOTH mode - merge DOM and accessibility tree
    if not ax_nodes:
        if config.is_accessibility_mandatory():
            logger.warning("⚠️  Accessibility extraction is mandatory but no accessibility nodes found!")
            logger.warning("   Falling back to DOM nodes only")
        else:
            logger.debug("No accessibility tree nodes available, returning DOM nodes as-is")
        return dom_nodes
    
    # Create a mapping from accessibility backendDOMNodeId to accessibility data
    ax_by_backend_id = {}
    for ax_node in ax_nodes:
        backend_id = ax_node.get('backendDOMNodeId')
        if backend_id is not None:
            ax_by_backend_id[backend_id] = ax_node
    
    logger.debug(f"Merging {len(dom_nodes)} DOM nodes with {len(ax_by_backend_id)} accessibility nodes")
    
    # Use list comprehension for better performance
    merged_nodes = []
    for dom_node in dom_nodes:
        # Get the backend node ID from DOM node
        backend_id = dom_node.get('backendNodeId')
        if backend_id is None:
            # If no backend ID, use the DOM node as-is
            merged_node = dom_node.copy()
        else:
            # Find matching accessibility node
            ax_node = ax_by_backend_id.get(backend_id)
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
    
    # Add any accessibility nodes that don't have corresponding DOM nodes
    # This ensures we don't lose accessibility-only elements
    dom_backend_ids = {node.get('backendNodeId') for node in dom_nodes if node.get('backendNodeId') is not None}
    for ax_node in ax_nodes:
        backend_id = ax_node.get('backendDOMNodeId')
        if backend_id is not None and backend_id not in dom_backend_ids:
            # This accessibility node doesn't have a corresponding DOM node
            # Convert it to element descriptor format and add it
            element_descriptor = convert_accessibility_to_element(ax_node)
            if element_descriptor:
                merged_nodes.append(element_descriptor)
    
    logger.debug(f"Successfully merged {len(merged_nodes)} nodes (DOM: {len(dom_nodes)}, Accessibility: {len(ax_nodes)})")
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
    ax_name_raw = ax_node.get('name', '')
    ax_name = extract_clean_text(ax_name_raw) if ax_name_raw else ''
    
    # Avoid duplication - if both are the same, just return one
    if ax_name and dom_text and ax_name == dom_text:
        return ax_name
    
    # Prioritize accessibility name if available and meaningful
    if ax_name and len(ax_name) > 0:
        # If accessibility name is more descriptive, use it
        if len(ax_name) > len(dom_text) or not dom_text:
            return ax_name
        # If both are available and different, combine them
        elif dom_text and ax_name != dom_text:
            return f"{ax_name} {dom_text}".strip()
    
    # Fall back to DOM text
    return dom_text


def extract_clean_text(text_value: Any) -> str:
    """
    Extract clean text from accessibility tree text values.
    
    Args:
        text_value: Text value from accessibility tree (can be string or computed object)
        
    Returns:
        Clean text string
    """
    if isinstance(text_value, str):
        return text_value.strip()
    elif isinstance(text_value, dict):
        if 'value' in text_value:
            return str(text_value['value']).strip()
        elif 'type' in text_value and 'value' in text_value:
            return str(text_value['value']).strip()
        else:
            # Try to extract any string value from the dict
            for key, value in text_value.items():
                if isinstance(value, str) and value.strip():
                    return value.strip()
    else:
        return str(text_value).strip() if text_value else ''


def extract_comprehensive_text(node: Dict[str, Any]) -> str:
    """
    Extract comprehensive text content from a node, trying multiple sources.
    
    Args:
        node: DOM or accessibility node
        
    Returns:
        Best available text content
    """
    text_parts = []
    
    # 1. Direct text content
    node_value = node.get('nodeValue', '').strip()
    if node_value:
        text_parts.append(node_value)
    
    # 2. Text from accessibility tree
    if 'accessibility' in node:
        ax_name = node['accessibility'].get('name', '')
        if ax_name:
            clean_name = extract_clean_text(ax_name)
            if clean_name and clean_name != node_value:  # Avoid duplication
                text_parts.append(clean_name)
        
        ax_value = node['accessibility'].get('value', '')
        if ax_value:
            clean_value = extract_clean_text(ax_value)
            if clean_value and clean_value != node_value and clean_value != clean_name:  # Avoid duplication
                text_parts.append(clean_value)
    
    # 3. Text from attributes
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
        text_attrs = ['aria-label', 'data-placeholder-text', 'title', 'value', 'alt', 'placeholder']
        for attr in text_attrs:
            if attr in attrs and attrs[attr]:
                text_parts.append(str(attrs[attr]).strip())
    
    # 4. Text from children (if available)
    children = node.get('children', [])
    if children:
        for child in children:
            if isinstance(child, dict):
                child_text = child.get('nodeValue', '').strip()
                if child_text:
                    text_parts.append(child_text)
    
    # 5. Text from computed properties (skip to avoid circular reference)
    # computed_text = node.get('text', '').strip()
    # if computed_text:
    #     text_parts.append(computed_text)
    
    # Return the longest meaningful text
    meaningful_texts = [t for t in text_parts if t and len(t) > 1]
    if meaningful_texts:
        # Return the longest text, or the first one if they're similar length
        return max(meaningful_texts, key=len)
    
    return ' '.join(text_parts).strip()

def convert_accessibility_to_element(ax_node: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert accessibility tree node to element descriptor format.
    
    Args:
        ax_node: Raw accessibility tree node
        
    Returns:
        Element descriptor in standard format
    """
    if not ax_node:
        return None
    
    # Get role and determine if interactive
    role = ax_node.get('role', '')
    # Handle case where role might be a complex object
    if isinstance(role, dict):
        if 'value' in role:
            role = role['value']
        elif 'type' in role and 'value' in role:
            role = role['value']
        else:
            role = str(role)
    elif not isinstance(role, str):
        role = str(role) if role else ''
    
    is_interactive = is_accessibility_role_interactive(role)
    
    # Map accessibility role to HTML tag
    tag_mapping = {
        'button': 'BUTTON',
        'link': 'A',
        'textbox': 'INPUT',
        'checkbox': 'INPUT',
        'radio': 'INPUT',
        'combobox': 'SELECT',
        'menu': 'UL',
        'menuitem': 'LI',
        'list': 'UL',
        'listitem': 'LI',
        'heading': 'H1',
        'img': 'IMG',
        'text': 'SPAN',
        'paragraph': 'P',
        'article': 'ARTICLE',
        'section': 'SECTION',
        'navigation': 'NAV',
        'main': 'MAIN',
        'banner': 'HEADER',
        'contentinfo': 'FOOTER',
        'form': 'FORM',
        'search': 'FORM',
        'dialog': 'DIALOG',
        'alert': 'DIV',
        'status': 'DIV',
        'progressbar': 'PROGRESS',
        'slider': 'INPUT',
        'spinbutton': 'INPUT',
        'tab': 'BUTTON',
        'tablist': 'DIV',
        'tabpanel': 'DIV',
        'tree': 'UL',
        'treeitem': 'LI',
        'grid': 'TABLE',
        'gridcell': 'TD',
        'row': 'TR',
        'columnheader': 'TH',
        'rowheader': 'TH',
        'table': 'TABLE',
        'cell': 'TD',
        'rowgroup': 'TBODY',
        'columnheader': 'TH',
        'rowheader': 'TH'
    }
    
    # Determine HTML tag from accessibility role
    html_tag = tag_mapping.get(role.lower(), 'DIV')
    
    # Extract basic information from accessibility node
    element = {
        'backendNodeId': ax_node.get('nodeId'),
        'framePath': ax_node.get('frameId', 'main'),
        'tag': html_tag,
        'type': role,
        'id': ax_node.get('id', ''),
        'classes': [],
        'placeholder': extract_clean_text(ax_node.get('name', '')),
        'aria': {
            'label': extract_clean_text(ax_node.get('name', '')),
            'description': extract_clean_text(ax_node.get('description', '')),
            'role': role,
            'hidden': ax_node.get('ignored', False),
            'disabled': ax_node.get('disabled', False)
        },
        'labels': [extract_clean_text(ax_node.get('name', ''))] if ax_node.get('name') else [],
        'ax_role': role,
        'ax_name': extract_clean_text(ax_node.get('name', '')),
        'ax_hidden': ax_node.get('ignored', False),
        'ax_disabled': ax_node.get('disabled', False),
        'visible': not ax_node.get('ignored', False),
        'bbox': ax_node.get('boundingRect', {}),
        'neighbors': [],
        'dom_hash': '',
        'shadowPath': '',
        'text': extract_clean_text(ax_node.get('name', '')),
        'attributes': {},
        'interactive': is_interactive,
        'accessibility_role': role,
        'accessibility_name': extract_clean_text(ax_node.get('name', '')),
        'accessibility_description': extract_clean_text(ax_node.get('description', ''))
    }
    
    # Add accessibility-specific attributes
    if ax_node.get('value'):
        element['attributes']['value'] = ax_node['value']
    if ax_node.get('description'):
        element['attributes']['aria-describedby'] = ax_node['description']
    if ax_node.get('checked') is not None:
        element['attributes']['aria-checked'] = str(ax_node['checked']).lower()
    if ax_node.get('expanded') is not None:
        element['attributes']['aria-expanded'] = str(ax_node['expanded']).lower()
    if ax_node.get('selected') is not None:
        element['attributes']['aria-selected'] = str(ax_node['selected']).lower()
    if ax_node.get('haspopup') is not None:
        element['attributes']['aria-haspopup'] = str(ax_node['haspopup']).lower()
    if ax_node.get('level'):
        element['attributes']['aria-level'] = str(ax_node['level'])
    if ax_node.get('posinset'):
        element['attributes']['aria-posinset'] = str(ax_node['posinset'])
    if ax_node.get('setsize'):
        element['attributes']['aria-setsize'] = str(ax_node['setsize'])
    
    return element


def is_accessibility_role_interactive(role: str) -> bool:
    """
    Determine if an accessibility role represents an interactive element.
    
    Args:
        role: Accessibility role string
        
    Returns:
        True if the role represents an interactive element
    """
    interactive_roles = {
        'button', 'link', 'textbox', 'checkbox', 'radio', 'combobox', 'menu', 
        'menuitem', 'tab', 'tabpanel', 'slider', 'spinbutton', 'searchbox',
        'switch', 'progressbar', 'scrollbar', 'tree', 'treeitem', 'grid',
        'gridcell', 'cell', 'row', 'columnheader', 'rowheader', 'option',
        'listbox', 'listitem', 'menubar', 'menuitemcheckbox', 'menuitemradio',
        'toolbar', 'tooltip', 'dialog', 'alertdialog', 'form', 'search',
        'text', 'paragraph', 'heading', 'img', 'article', 'section',
        'navigation', 'main', 'banner', 'contentinfo', 'complementary',
        'region', 'status', 'alert', 'log', 'marquee', 'timer', 'tablist'
    }
    
    return role.lower() in interactive_roles


def enhance_element_descriptor(element: Dict[str, Any], use_hierarchy: bool = False, hierarchy_builder=None) -> Dict[str, Any]:
    """
    Enhance element descriptor with accessibility information and optional hierarchy context.
    
    Args:
        element: Element descriptor from DOM
        use_hierarchy: Whether to add hierarchical context
        hierarchy_builder: HierarchyContextBuilder instance
        
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
    
    # Add hierarchical context if requested
    if use_hierarchy and hierarchy_builder:
        try:
            # This will be called for individual elements, so we need to handle it differently
            # For now, we'll add a placeholder that will be filled by the hierarchy builder
            element['context'] = {
                'parent': None,
                'siblings': [],
                'ancestors': [],
                'hierarchy_path': 'PENDING',
                'depth': 0,
                'has_children': False,
                'children_count': 0
            }
        except Exception as e:
            logger.warning(f"Failed to add hierarchy context: {e}")
            element['context'] = {
                'parent': None,
                'siblings': [],
                'ancestors': [],
                'hierarchy_path': 'ERROR',
                'depth': 0,
                'has_children': False,
                'children_count': 0
            }
    
    return element