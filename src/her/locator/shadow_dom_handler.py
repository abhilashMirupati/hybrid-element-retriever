"""
Enhanced Shadow DOM Handler for both semantic and no-semantic modes.

This module provides comprehensive shadow DOM detection, traversal,
and element location while maintaining compatibility with both
retrieval modes.
"""

from __future__ import annotations

import logging
import re
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum

log = logging.getLogger("her.shadow_dom_handler")


class ShadowDOMType(Enum):
    """Types of shadow DOM encountered."""
    OPEN = "open"
    CLOSED = "closed"
    DELEGATE_FOCUS = "delegate_focus"
    SLOT = "slot"


@dataclass
class ShadowRoot:
    """Shadow root information."""
    root_id: str
    host_element: Dict[str, Any]
    shadow_type: ShadowDOMType
    is_attached: bool = True
    slot_elements: List[Dict[str, Any]] = None
    style_elements: List[Dict[str, Any]] = None


class ShadowDOMHandler:
    """Enhanced shadow DOM handler for both retrieval modes."""
    
    def __init__(self):
        """Initialize shadow DOM handler."""
        self.shadow_roots: Dict[str, ShadowRoot] = {}
        self.slot_mappings: Dict[str, List[str]] = {}
        self.current_shadow_root: Optional[str] = None
    
    def detect_shadow_roots(self, elements: List[Dict[str, Any]]) -> List[ShadowRoot]:
        """Detect shadow DOM roots in elements.
        
        Args:
            elements: List of element descriptors
            
        Returns:
            List of detected shadow roots
        """
        shadow_roots = []
        
        for element in elements:
            if self._is_shadow_host(element):
                shadow_root = self._create_shadow_root(element)
                if shadow_root:
                    shadow_roots.append(shadow_root)
                    self.shadow_roots[shadow_root.root_id] = shadow_root
        
        log.info(f"Detected {len(shadow_roots)} shadow DOM roots")
        return shadow_roots
    
    def _is_shadow_host(self, element: Dict[str, Any]) -> bool:
        """Check if element is a shadow DOM host.
        
        Args:
            element: Element descriptor
            
        Returns:
            True if element is a shadow host
        """
        tag = element.get('tag', '').lower()
        attrs = element.get('attributes', {})
        
        # Check for shadow DOM indicators
        shadow_indicators = [
            'shadowroot', 'shadow-root', 'data-shadow',
            'shadowdom', 'shadow-dom', 'web-component'
        ]
        
        # Check attributes
        if any(indicator in attrs for indicator in shadow_indicators):
            return True
        
        # Check for custom element patterns
        if tag and '-' in tag:  # Custom elements often have hyphens
            return True
        
        # Check for shadow DOM specific attributes
        if any(attr.startswith('shadow') for attr in attrs.keys()):
            return True
        
        return False
    
    def _create_shadow_root(self, host_element: Dict[str, Any]) -> Optional[ShadowRoot]:
        """Create shadow root from host element.
        
        Args:
            host_element: Host element descriptor
            
        Returns:
            Shadow root or None
        """
        root_id = f"shadow_{len(self.shadow_roots)}"
        attrs = host_element.get('attributes', {})
        
        # Determine shadow type
        shadow_type = ShadowDOMType.OPEN
        if attrs.get('shadowroot') == 'closed':
            shadow_type = ShadowDOMType.CLOSED
        elif attrs.get('delegatefocus'):
            shadow_type = ShadowDOMType.DELEGATE_FOCUS
        
        shadow_root = ShadowRoot(
            root_id=root_id,
            host_element=host_element,
            shadow_type=shadow_type,
            slot_elements=[],
            style_elements=[]
        )
        
        return shadow_root
    
    def traverse_shadow_dom(self, shadow_root_id: str, 
                          elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Traverse shadow DOM and extract elements.
        
        Args:
            shadow_root_id: ID of shadow root to traverse
            elements: List of all elements
            
        Returns:
            List of elements within shadow DOM
        """
        if shadow_root_id not in self.shadow_roots:
            return []
        
        shadow_root = self.shadow_roots[shadow_root_id]
        host_element = shadow_root.host_element
        
        # Find elements that belong to this shadow root
        shadow_elements = []
        
        for element in elements:
            if self._belongs_to_shadow_root(element, shadow_root):
                shadow_elements.append(element)
        
        # Process slots
        slot_elements = self._process_slots(shadow_elements, shadow_root)
        shadow_elements.extend(slot_elements)
        
        log.info(f"Traversed shadow DOM {shadow_root_id}: {len(shadow_elements)} elements")
        return shadow_elements
    
    def _belongs_to_shadow_root(self, element: Dict[str, Any], 
                               shadow_root: ShadowRoot) -> bool:
        """Check if element belongs to shadow root.
        
        Args:
            element: Element descriptor
            shadow_root: Shadow root context
            
        Returns:
            True if element belongs to shadow root
        """
        # Check if element is a child of shadow host
        element_xpath = element.get('xpath', '')
        host_xpath = shadow_root.host_element.get('xpath', '')
        
        if host_xpath and element_xpath.startswith(host_xpath):
            return True
        
        # Check for shadow DOM specific attributes
        attrs = element.get('attributes', {})
        if any(attr.startswith('shadow') for attr in attrs.keys()):
            return True
        
        # Check for slot elements
        if element.get('tag', '').lower() == 'slot':
            return True
        
        return False
    
    def _process_slots(self, elements: List[Dict[str, Any]], 
                      shadow_root: ShadowRoot) -> List[Dict[str, Any]]:
        """Process slot elements in shadow DOM.
        
        Args:
            elements: List of elements
            shadow_root: Shadow root context
            
        Returns:
            List of slot elements
        """
        slot_elements = []
        
        for element in elements:
            if element.get('tag', '').lower() == 'slot':
                slot_elements.append(element)
                shadow_root.slot_elements.append(element)
        
        return slot_elements
    
    def resolve_shadow_selector(self, element: Dict[str, Any], 
                               shadow_root_id: str) -> str:
        """Resolve selector for element within shadow DOM.
        
        Args:
            element: Element descriptor
            shadow_root_id: ID of shadow root
            
        Returns:
            Resolved selector with shadow DOM context
        """
        if shadow_root_id not in self.shadow_roots:
            return element.get('xpath', '')
        
        shadow_root = self.shadow_roots[shadow_root_id]
        host_element = shadow_root.host_element
        
        element_selector = element.get('xpath', '')
        host_selector = host_element.get('xpath', '')
        
        # Create shadow DOM selector
        if element_selector.startswith('//'):
            # XPath selector
            return f"{host_selector}{element_selector}"
        else:
            # CSS selector with shadow DOM syntax
            return f"{host_selector} >>> {element_selector}"
    
    def find_elements_in_shadow_dom(self, elements: List[Dict[str, Any]], 
                                   target: str, matcher) -> List[Dict[str, Any]]:
        """Find elements within shadow DOM using target matcher.
        
        Args:
            elements: List of element descriptors
            target: Target string to match
            matcher: Target matcher instance
            
        Returns:
            List of matching elements with shadow DOM context
        """
        matches = []
        
        # Detect shadow roots
        shadow_roots = self.detect_shadow_roots(elements)
        
        for shadow_root in shadow_roots:
            # Traverse shadow DOM
            shadow_elements = self.traverse_shadow_dom(shadow_root.root_id, elements)
            
            if not shadow_elements:
                continue
            
            # Match elements within shadow DOM
            shadow_matches = matcher.match_elements(shadow_elements, target)
            
            # Add shadow DOM context to matches
            for match in shadow_matches:
                element = match.element
                element['shadow_root_id'] = shadow_root.root_id
                element['shadow_host'] = shadow_root.host_element
                element['is_shadow_element'] = True
                
                # Resolve shadow selector
                shadow_selector = self.resolve_shadow_selector(element, shadow_root.root_id)
                element['shadow_selector'] = shadow_selector
                
                matches.append(match)
        
        log.info(f"Found {len(matches)} matches in shadow DOM")
        return matches
    
    def handle_dynamic_shadow_dom(self, elements: List[Dict[str, Any]]) -> List[ShadowRoot]:
        """Handle dynamically created shadow DOM.
        
        Args:
            elements: List of element descriptors
            
        Returns:
            List of dynamic shadow roots
        """
        dynamic_roots = []
        
        for element in elements:
            attrs = element.get('attributes', {})
            
            # Check for dynamic shadow DOM indicators
            if any(indicator in attrs for indicator in [
                'data-dynamic-shadow', 'data-lazy-shadow', 'data-async-shadow'
            ]):
                shadow_root = self._create_shadow_root(element)
                if shadow_root:
                    dynamic_roots.append(shadow_root)
                    self.shadow_roots[shadow_root.root_id] = shadow_root
        
        log.info(f"Detected {len(dynamic_roots)} dynamic shadow DOM roots")
        return dynamic_roots
    
    def get_shadow_hierarchy(self) -> Dict[str, List[str]]:
        """Get shadow DOM hierarchy structure.
        
        Returns:
            Dictionary mapping host elements to shadow roots
        """
        hierarchy = {}
        
        for root_id, shadow_root in self.shadow_roots.items():
            host_xpath = shadow_root.host_element.get('xpath', '')
            if host_xpath not in hierarchy:
                hierarchy[host_xpath] = []
            hierarchy[host_xpath].append(root_id)
        
        return hierarchy
    
    def cleanup(self):
        """Clean up shadow DOM handler state."""
        self.shadow_roots.clear()
        self.slot_mappings.clear()
        self.current_shadow_root = None
        log.info("Shadow DOM handler cleaned up")