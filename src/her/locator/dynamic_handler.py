"""
Enhanced Dynamic Node Handler for both semantic and no-semantic modes.

This module provides comprehensive dynamic content detection, monitoring,
and element location while maintaining compatibility with both
retrieval modes.
"""

from __future__ import annotations

import logging
import time
import hashlib
from typing import List, Dict, Any, Optional, Tuple, Set, Callable
from dataclasses import dataclass
from enum import Enum

log = logging.getLogger("her.dynamic_handler")


class DynamicType(Enum):
    """Types of dynamic content."""
    AJAX = "ajax"
    SPA = "spa"
    LAZY_LOAD = "lazy_load"
    INFINITE_SCROLL = "infinite_scroll"
    MODAL = "modal"
    TOOLTIP = "tooltip"
    DROPDOWN = "dropdown"
    TAB = "tab"
    ACCORDION = "accordion"


@dataclass
class DynamicElement:
    """Dynamic element information."""
    element_id: str
    element: Dict[str, Any]
    dynamic_type: DynamicType
    is_loaded: bool = False
    load_time: Optional[float] = None
    trigger_conditions: List[str] = None
    stability_score: float = 0.0


class DynamicHandler:
    """Enhanced dynamic content handler for both retrieval modes."""
    
    def __init__(self, stability_threshold: float = 0.8):
        """Initialize dynamic handler.
        
        Args:
            stability_threshold: Threshold for element stability (0.0-1.0)
        """
        self.stability_threshold = stability_threshold
        self.dynamic_elements: Dict[str, DynamicElement] = {}
        self.element_hashes: Dict[str, str] = {}
        self.stability_monitor: Dict[str, List[float]] = {}
        self.load_callbacks: List[Callable] = []
    
    def detect_dynamic_elements(self, elements: List[Dict[str, Any]]) -> List[DynamicElement]:
        """Detect dynamic elements in the page.
        
        Args:
            elements: List of element descriptors
            
        Returns:
            List of detected dynamic elements
        """
        dynamic_elements = []
        
        for element in elements:
            dynamic_type = self._classify_dynamic_element(element)
            if dynamic_type:
                element_id = self._generate_element_id(element)
                
                dynamic_element = DynamicElement(
                    element_id=element_id,
                    element=element,
                    dynamic_type=dynamic_type,
                    trigger_conditions=self._extract_trigger_conditions(element)
                )
                
                dynamic_elements.append(dynamic_element)
                self.dynamic_elements[element_id] = dynamic_element
        
        log.info(f"Detected {len(dynamic_elements)} dynamic elements")
        return dynamic_elements
    
    def _classify_dynamic_element(self, element: Dict[str, Any]) -> Optional[DynamicType]:
        """Classify element as dynamic content type.
        
        Args:
            element: Element descriptor
            
        Returns:
            Dynamic type or None if not dynamic
        """
        tag = element.get('tag', '').lower()
        attrs = element.get('attributes', {})
        text = element.get('text', '').lower()
        
        # Check for AJAX indicators
        if any(indicator in attrs for indicator in [
            'data-ajax', 'data-async', 'data-loading', 'data-fetch'
        ]):
            return DynamicType.AJAX
        
        # Check for SPA indicators
        if any(indicator in attrs for indicator in [
            'data-spa', 'data-route', 'data-view', 'data-component'
        ]):
            return DynamicType.SPA
        
        # Check for lazy loading
        if any(indicator in attrs for indicator in [
            'data-lazy', 'data-defer', 'loading', 'data-src'
        ]):
            return DynamicType.LAZY_LOAD
        
        # Check for infinite scroll
        if any(indicator in attrs for indicator in [
            'data-infinite', 'data-scroll', 'data-pagination'
        ]):
            return DynamicType.INFINITE_SCROLL
        
        # Check for modal indicators
        if any(indicator in text for indicator in [
            'modal', 'popup', 'dialog', 'overlay'
        ]) or tag in ['dialog', 'modal']:
            return DynamicType.MODAL
        
        # Check for tooltip indicators
        if any(indicator in attrs for indicator in [
            'data-tooltip', 'data-tip', 'title', 'aria-describedby'
        ]) or 'tooltip' in text:
            return DynamicType.TOOLTIP
        
        # Check for dropdown indicators
        if any(indicator in attrs for indicator in [
            'data-dropdown', 'data-toggle', 'aria-haspopup'
        ]) or tag in ['select', 'dropdown']:
            return DynamicType.DROPDOWN
        
        # Check for tab indicators
        if any(indicator in attrs for indicator in [
            'data-tab', 'role="tab"', 'aria-controls'
        ]) or 'tab' in text:
            return DynamicType.TAB
        
        # Check for accordion indicators
        if any(indicator in attrs for indicator in [
            'data-accordion', 'data-collapse', 'aria-expanded'
        ]) or 'accordion' in text:
            return DynamicType.ACCORDION
        
        return None
    
    def _extract_trigger_conditions(self, element: Dict[str, Any]) -> List[str]:
        """Extract trigger conditions for dynamic element.
        
        Args:
            element: Element descriptor
            
        Returns:
            List of trigger conditions
        """
        conditions = []
        attrs = element.get('attributes', {})
        
        # Check for click triggers
        if attrs.get('onclick') or attrs.get('data-click'):
            conditions.append('click')
        
        # Check for hover triggers
        if attrs.get('onmouseover') or attrs.get('data-hover'):
            conditions.append('hover')
        
        # Check for focus triggers
        if attrs.get('onfocus') or attrs.get('data-focus'):
            conditions.append('focus')
        
        # Check for scroll triggers
        if attrs.get('data-scroll') or attrs.get('data-onscroll'):
            conditions.append('scroll')
        
        # Check for time-based triggers
        if attrs.get('data-delay') or attrs.get('data-timeout'):
            conditions.append('time')
        
        return conditions
    
    def _generate_element_id(self, element: Dict[str, Any]) -> str:
        """Generate unique ID for element.
        
        Args:
            element: Element descriptor
            
        Returns:
            Unique element ID
        """
        # Use xpath as base for ID
        xpath = element.get('xpath', '')
        tag = element.get('tag', '')
        text = element.get('text', '')
        
        # Create hash from element properties
        content = f"{xpath}:{tag}:{text}"
        element_id = hashlib.md5(content.encode()).hexdigest()[:12]
        
        return f"dynamic_{element_id}"
    
    def monitor_element_stability(self, element_id: str, 
                                current_elements: List[Dict[str, Any]]) -> float:
        """Monitor element stability over time.
        
        Args:
            element_id: ID of element to monitor
            current_elements: Current page elements
            
        Returns:
            Stability score (0.0-1.0)
        """
        if element_id not in self.dynamic_elements:
            return 0.0
        
        # Find current version of element
        current_element = self._find_element_by_id(element_id, current_elements)
        if not current_element:
            return 0.0
        
        # Calculate element hash
        current_hash = self._calculate_element_hash(current_element)
        
        # Store hash history
        if element_id not in self.element_hashes:
            self.element_hashes[element_id] = current_hash
            self.stability_monitor[element_id] = [1.0]  # Start with full stability
            return 1.0
        
        # Compare with previous hash
        previous_hash = self.element_hashes[element_id]
        if current_hash == previous_hash:
            stability = 1.0
        else:
            stability = 0.0
        
        # Update stability history
        self.stability_monitor[element_id].append(stability)
        
        # Keep only recent history (last 10 checks)
        if len(self.stability_monitor[element_id]) > 10:
            self.stability_monitor[element_id] = self.stability_monitor[element_id][-10:]
        
        # Calculate average stability
        avg_stability = sum(self.stability_monitor[element_id]) / len(self.stability_monitor[element_id])
        
        # Update element hash
        self.element_hashes[element_id] = current_hash
        
        return avg_stability
    
    def _find_element_by_id(self, element_id: str, 
                           elements: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Find element by ID in current elements.
        
        Args:
            element_id: Element ID to find
            elements: Current page elements
            
        Returns:
            Element descriptor or None
        """
        for element in elements:
            if self._generate_element_id(element) == element_id:
                return element
        return None
    
    def _calculate_element_hash(self, element: Dict[str, Any]) -> str:
        """Calculate hash for element stability monitoring.
        
        Args:
            element: Element descriptor
            
        Returns:
            Element hash
        """
        # Use key properties for hashing
        key_props = {
            'tag': element.get('tag', ''),
            'text': element.get('text', ''),
            'xpath': element.get('xpath', ''),
            'visible': element.get('visible', True)
        }
        
        # Include important attributes
        attrs = element.get('attributes', {})
        important_attrs = ['id', 'class', 'name', 'type', 'value']
        for attr in important_attrs:
            if attr in attrs:
                key_props[attr] = attrs[attr]
        
        # Create hash
        content = str(sorted(key_props.items()))
        return hashlib.md5(content.encode()).hexdigest()
    
    def wait_for_element_stability(self, element_id: str, 
                                 elements: List[Dict[str, Any]], 
                                 timeout: float = 5.0) -> bool:
        """Wait for element to become stable.
        
        Args:
            element_id: ID of element to wait for
            elements: Current page elements
            timeout: Maximum time to wait
            
        Returns:
            True if element became stable, False if timeout
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            stability = self.monitor_element_stability(element_id, elements)
            
            if stability >= self.stability_threshold:
                # Mark element as loaded
                if element_id in self.dynamic_elements:
                    self.dynamic_elements[element_id].is_loaded = True
                    self.dynamic_elements[element_id].load_time = time.time()
                
                log.info(f"Element {element_id} became stable (score: {stability:.2f})")
                return True
            
            time.sleep(0.1)  # Check every 100ms
        
        log.warning(f"Element {element_id} did not become stable within {timeout}s")
        return False
    
    def handle_dynamic_loading(self, elements: List[Dict[str, Any]], 
                              matcher, target: str) -> List[Dict[str, Any]]:
        """Handle dynamic content loading and matching.
        
        Args:
            elements: List of element descriptors
            matcher: Target matcher instance
            target: Target string to match
            
        Returns:
            List of matching elements with dynamic context
        """
        matches = []
        
        # Detect dynamic elements
        dynamic_elements = self.detect_dynamic_elements(elements)
        
        for dynamic_element in dynamic_elements:
            element_id = dynamic_element.element_id
            
            # Wait for stability if needed
            if not dynamic_element.is_loaded:
                if self.wait_for_element_stability(element_id, elements):
                    # Re-match after element is stable
                    element_matches = matcher.match_elements([dynamic_element.element], target)
                    
                    for match in element_matches:
                        # Add dynamic context
                        match.element['dynamic_id'] = element_id
                        match.element['dynamic_type'] = dynamic_element.dynamic_type.value
                        match.element['is_dynamic'] = True
                        match.element['stability_score'] = dynamic_element.stability_score
                        
                        matches.append(match)
        
        log.info(f"Found {len(matches)} matches in dynamic content")
        return matches
    
    def get_dynamic_summary(self) -> Dict[str, Any]:
        """Get summary of dynamic elements.
        
        Returns:
            Dictionary with dynamic element summary
        """
        summary = {
            'total_dynamic_elements': len(self.dynamic_elements),
            'loaded_elements': sum(1 for elem in self.dynamic_elements.values() if elem.is_loaded),
            'dynamic_types': {},
            'stability_scores': {}
        }
        
        # Count by type
        for element in self.dynamic_elements.values():
            dyn_type = element.dynamic_type.value
            summary['dynamic_types'][dyn_type] = summary['dynamic_types'].get(dyn_type, 0) + 1
            
            # Track stability scores
            if element.element_id in self.stability_monitor:
                scores = self.stability_monitor[element.element_id]
                summary['stability_scores'][element.element_id] = {
                    'current': scores[-1] if scores else 0.0,
                    'average': sum(scores) / len(scores) if scores else 0.0,
                    'checks': len(scores)
                }
        
        return summary
    
    def cleanup(self):
        """Clean up dynamic handler state."""
        self.dynamic_elements.clear()
        self.element_hashes.clear()
        self.stability_monitor.clear()
        self.load_callbacks.clear()
        log.info("Dynamic handler cleaned up")