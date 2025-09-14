"""
Canonical Descriptor Builder for HER Framework

Builds deterministic canonical descriptors per element that can be used for:
- Stable element identification across page loads
- Deterministic string signatures for caching
- Robust element matching and retrieval

Each canonical descriptor includes:
- tag, role, attributes (id, name, aria-label, title, placeholder)
- innerText (trimmed)
- backendNodeId
- hierarchy context (parent tag, siblings count)
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class CanonicalNode:
    """Canonical descriptor for a DOM element."""
    
    # Core element properties
    tag: str
    role: str
    inner_text: str
    backend_node_id: Optional[int]
    
    # Key attributes for matching
    element_id: str
    name: str
    aria_label: str
    title: str
    placeholder: str
    
    # Hierarchy context
    parent_tag: str
    siblings_count: int
    
    # Deterministic signature
    signature: str
    
    # Additional metadata
    attributes: Dict[str, str]
    is_interactive: bool
    frame_hash: str


class CanonicalDescriptorBuilder:
    """Builds canonical descriptors for DOM elements."""
    
    def __init__(self):
        # Attributes that are most important for element identification
        self.key_attributes = {
            'id', 'name', 'aria-label', 'title', 'placeholder', 'value',
            'data-testid', 'data-id', 'class', 'type', 'href'
        }
        
        # Interactive element tags
        self.interactive_tags = {
            'button', 'a', 'input', 'select', 'textarea', 'option', 'label',
            'form', 'fieldset', 'summary', 'details'
        }
        
        # Interactive roles
        self.interactive_roles = {
            'button', 'link', 'menuitem', 'tab', 'option', 'radio', 'checkbox',
            'switch', 'textbox', 'combobox', 'listbox', 'menu', 'menubar',
            'toolbar', 'slider', 'progressbar', 'scrollbar', 'tablist', 'tree',
            'grid', 'cell', 'row', 'columnheader', 'rowheader', 'dialog',
            'alertdialog', 'log', 'marquee', 'status', 'timer', 'tooltip',
            'searchbox', 'spinbutton', 'tabpanel'
        }
    
    def build_canonical_descriptor(
        self, 
        element: Dict[str, Any], 
        parent_element: Optional[Dict[str, Any]] = None,
        siblings: List[Dict[str, Any]] = None
    ) -> CanonicalNode:
        """
        Build a canonical descriptor for a DOM element.
        
        Args:
            element: DOM element descriptor
            parent_element: Parent element for hierarchy context
            siblings: List of sibling elements for context
            
        Returns:
            CanonicalNode with deterministic signature
        """
        # Extract core properties
        tag = self._extract_tag(element)
        role = self._extract_role(element)
        inner_text = self._extract_inner_text(element)
        backend_node_id = element.get('backendNodeId')
        
        # Extract key attributes
        attributes = self._extract_attributes(element)
        element_id = attributes.get('id', '')
        name = attributes.get('name', '')
        aria_label = attributes.get('aria-label', '')
        title = attributes.get('title', '')
        placeholder = attributes.get('placeholder', '')
        
        # Build hierarchy context
        parent_tag = self._extract_parent_tag(parent_element)
        siblings_count = len(siblings) if siblings else 0
        
        # Determine if element is interactive
        is_interactive = self._is_element_interactive(tag, role, attributes)
        
        # Get frame hash
        frame_hash = element.get('meta', {}).get('frame_hash', '')
        
        # Build deterministic signature
        signature = self._build_signature(
            tag=tag,
            role=role,
            inner_text=inner_text,
            element_id=element_id,
            name=name,
            aria_label=aria_label,
            title=title,
            placeholder=placeholder,
            parent_tag=parent_tag,
            siblings_count=siblings_count,
            backend_node_id=backend_node_id
        )
        
        return CanonicalNode(
            tag=tag,
            role=role,
            inner_text=inner_text,
            backend_node_id=backend_node_id,
            element_id=element_id,
            name=name,
            aria_label=aria_label,
            title=title,
            placeholder=placeholder,
            parent_tag=parent_tag,
            siblings_count=siblings_count,
            signature=signature,
            attributes=attributes,
            is_interactive=is_interactive,
            frame_hash=frame_hash
        )
    
    def _extract_tag(self, element: Dict[str, Any]) -> str:
        """Extract and normalize tag name."""
        tag = element.get('tag', '').upper()
        if not tag or tag == '#TEXT':
            return ''
        return tag
    
    def _extract_role(self, element: Dict[str, Any]) -> str:
        """Extract accessibility role."""
        # Check attributes first
        attrs = element.get('attributes', {})
        if isinstance(attrs, dict):
            role = attrs.get('role', '')
            if role:
                return role.lower()
        
        # Check accessibility data
        accessibility = element.get('accessibility', {})
        if isinstance(accessibility, dict):
            role = accessibility.get('role', '')
            if role:
                return role.lower()
        
        return ''
    
    def _extract_inner_text(self, element: Dict[str, Any]) -> str:
        """Extract and normalize inner text content."""
        text = element.get('text', '').strip()
        
        # If no text, try to get from accessibility
        if not text:
            accessibility = element.get('accessibility', {})
            if isinstance(accessibility, dict):
                name = accessibility.get('name', '')
                if name:
                    text = str(name).strip()
        
        # Normalize whitespace
        if text:
            text = ' '.join(text.split())
        
        return text
    
    def _extract_attributes(self, element: Dict[str, Any]) -> Dict[str, str]:
        """Extract key attributes for element identification."""
        attrs = element.get('attributes', {})
        
        # Handle list format ['key1', 'value1', 'key2', 'value2']
        if isinstance(attrs, list):
            attrs_dict = {}
            for i in range(0, len(attrs), 2):
                if i + 1 < len(attrs):
                    attrs_dict[str(attrs[i])] = str(attrs[i + 1])
            attrs = attrs_dict
        
        # Extract only key attributes
        key_attrs = {}
        for attr_name in self.key_attributes:
            if attr_name in attrs:
                value = str(attrs[attr_name]).strip()
                if value:
                    key_attrs[attr_name] = value
        
        return key_attrs
    
    def _extract_parent_tag(self, parent_element: Optional[Dict[str, Any]]) -> str:
        """Extract parent tag for hierarchy context."""
        if not parent_element:
            return ''
        
        tag = parent_element.get('tag', '')
        if isinstance(tag, str):
            return tag.upper()
        return ''
    
    def _is_element_interactive(self, tag: str, role: str, attributes: Dict[str, str]) -> bool:
        """Determine if element is interactive."""
        # Check tag
        if tag.lower() in self.interactive_tags:
            return True
        
        # Check role
        if role and role.lower() in self.interactive_roles:
            return True
        
        # Check for interactive attributes
        interactive_attrs = {'onclick', 'href', 'tabindex', 'data-click', 'data-action'}
        if any(attr in attributes for attr in interactive_attrs):
            return True
        
        # Check input types
        if tag.lower() == 'input':
            input_type = attributes.get('type', '').lower()
            if input_type and input_type != 'hidden':
                return True
        
        return False
    
    def _build_signature(
        self,
        tag: str,
        role: str,
        inner_text: str,
        element_id: str,
        name: str,
        aria_label: str,
        title: str,
        placeholder: str,
        parent_tag: str,
        siblings_count: int,
        backend_node_id: Optional[int]
    ) -> str:
        """
        Build deterministic signature for element.
        
        The signature must be:
        1. Deterministic (same element → same signature)
        2. Unique enough to distinguish elements
        3. Stable across page loads
        """
        # Build signature components in deterministic order
        components = []
        
        # Core element identity
        if element_id:
            components.append(f"id:{element_id}")
        elif name:
            components.append(f"name:{name}")
        elif aria_label:
            components.append(f"aria-label:{aria_label}")
        elif title:
            components.append(f"title:{title}")
        elif placeholder:
            components.append(f"placeholder:{placeholder}")
        
        # Tag and role
        if tag:
            components.append(f"tag:{tag}")
        if role:
            components.append(f"role:{role}")
        
        # Text content (truncated for stability)
        if inner_text:
            # Truncate long text to avoid instability
            text_sig = inner_text[:50] if len(inner_text) > 50 else inner_text
            components.append(f"text:{text_sig}")
        
        # Hierarchy context
        if parent_tag:
            components.append(f"parent:{parent_tag}")
        if siblings_count > 0:
            components.append(f"siblings:{siblings_count}")
        
        # Backend node ID for uniqueness
        if backend_node_id is not None:
            components.append(f"backend:{backend_node_id}")
        
        # Create deterministic signature
        signature = "|".join(components)
        
        # Hash for compactness and consistency
        return hashlib.md5(signature.encode('utf-8')).hexdigest()[:16]
    
    def get_canonical_nodes(
        self, 
        elements: List[Dict[str, Any]], 
        frame_hash: str
    ) -> List[CanonicalNode]:
        """
        Build canonical nodes for a list of elements.
        
        Args:
            elements: List of DOM element descriptors
            frame_hash: Frame hash for context
            
        Returns:
            List of CanonicalNode objects
        """
        canonical_nodes = []
        
        # Build parent-child relationships for hierarchy context
        element_map = {i: elem for i, elem in enumerate(elements)}
        parent_map = {}
        children_map = {}
        
        # Simple parent-child detection based on XPath hierarchy
        for i, element in enumerate(elements):
            xpath = element.get('xpath', '')
            if xpath:
                # Find parent by looking for elements with shorter XPath
                parent_idx = self._find_parent_index(xpath, elements, i)
                if parent_idx is not None:
                    parent_map[i] = parent_idx
                    children_map.setdefault(parent_idx, []).append(i)
        
        # Build canonical nodes
        for i, element in enumerate(elements):
            try:
                # Get parent and siblings
                parent_idx = parent_map.get(i)
                parent_element = element_map[parent_idx] if parent_idx is not None else None
                
                sibling_indices = children_map.get(parent_idx, []) if parent_idx is not None else []
                siblings = [element_map[sib_idx] for sib_idx in sibling_indices if sib_idx != i]
                
                # Build canonical descriptor
                canonical_node = self.build_canonical_descriptor(
                    element=element,
                    parent_element=parent_element,
                    siblings=siblings
                )
                
                canonical_nodes.append(canonical_node)
                
            except Exception as e:
                logger.warning(f"Failed to build canonical descriptor for element {i}: {e}")
                continue
        
        return canonical_nodes
    
    def _find_parent_index(self, xpath: str, elements: List[Dict[str, Any]], current_index: int) -> Optional[int]:
        """Find parent element index based on XPath hierarchy."""
        if not xpath or xpath == '/':
            return None
        
        # Get parent XPath by removing last segment
        parent_xpath = '/'.join(xpath.split('/')[:-1])
        if not parent_xpath:
            return None
        
        # Find element with matching parent XPath
        for i, element in enumerate(elements):
            if i == current_index:
                continue
            element_xpath = element.get('xpath', '')
            if element_xpath == parent_xpath:
                return i
        
        return None


def get_canonical_nodes(elements: List[Dict[str, Any]], frame_hash: str) -> List[CanonicalNode]:
    """
    Convenience function to get canonical nodes for elements.
    
    Args:
        elements: List of DOM element descriptors
        frame_hash: Frame hash for context
        
    Returns:
        List of CanonicalNode objects
    """
    builder = CanonicalDescriptorBuilder()
    return builder.get_canonical_nodes(elements, frame_hash)