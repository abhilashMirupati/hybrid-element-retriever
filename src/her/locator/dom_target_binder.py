"""
DOM Target Binder for No-Semantic Mode

This module provides deterministic DOM-to-target binding by matching
innerText and accessibility attributes to target text, with backendNodeId resolution.
"""

from __future__ import annotations

import logging
import re
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum

log = logging.getLogger("her.dom_target_binder")


class MatchType(Enum):
    """Types of DOM matches."""
    INNER_TEXT = "inner_text"
    ARIA_LABEL = "aria_label"
    TITLE = "title"
    PLACEHOLDER = "placeholder"
    ID = "id"
    NAME = "name"
    VALUE = "value"
    DATA_TESTID = "data_testid"
    ALT = "alt"


@dataclass
class DOMMatch:
    """DOM match result."""
    element: Dict[str, Any]
    backend_node_id: str
    match_type: MatchType
    matched_text: str
    score: float
    hierarchy_path: str
    canonical_descriptor: str


class DOMTargetBinder:
    """Deterministic DOM-to-target binding with backendNodeId resolution."""
    
    # Priority order for matching attributes
    MATCH_ATTRIBUTES = [
        ("innerText", MatchType.INNER_TEXT),
        ("aria-label", MatchType.ARIA_LABEL),
        ("title", MatchType.TITLE),
        ("placeholder", MatchType.PLACEHOLDER),
        ("id", MatchType.ID),
        ("name", MatchType.NAME),
        ("value", MatchType.VALUE),
        ("data-testid", MatchType.DATA_TESTID),
        ("alt", MatchType.ALT),
    ]
    
    def __init__(self, case_sensitive: bool = False):
        """Initialize DOM target binder.
        
        Args:
            case_sensitive: Whether to perform case-sensitive matching
        """
        self.case_sensitive = case_sensitive
    
    def bind_target_to_dom(self, elements: List[Dict[str, Any]], 
                          target_text: str, intent: str = "click") -> List[DOMMatch]:
        """Bind target text to DOM elements with deterministic matching.
        
        Args:
            elements: List of DOM elements
            target_text: Target text to match
            intent: User intent (click, enter, search, etc.)
            
        Returns:
            List of DOM matches sorted by relevance
        """
        if not target_text or not elements:
            return []
        
        matches = []
        normalized_target = self._normalize_text(target_text)
        
        for element in elements:
            # Skip hidden or disabled elements
            if not self._is_element_visible(element):
                continue
            
            # Check if element is interactive for the given intent
            if not self._is_element_interactive(element, intent):
                continue
            
            # Get backend node ID
            backend_node_id = self._get_backend_node_id(element)
            if not backend_node_id:
                continue
            
            # Try to match against all attributes
            for attr_name, match_type in self.MATCH_ATTRIBUTES:
                attr_value = self._get_attribute_value(element, attr_name)
                if not attr_value:
                    continue
                
                # Check for exact match
                if self._is_exact_match(attr_value, normalized_target):
                    match = self._create_match(
                        element, backend_node_id, match_type, 
                        attr_value, 1.0, intent
                    )
                    matches.append(match)
                    continue
                
                # Check for partial match
                partial_score = self._calculate_partial_match(attr_value, normalized_target)
                if partial_score > 0.5:  # Threshold for partial matches
                    match = self._create_match(
                        element, backend_node_id, match_type,
                        attr_value, partial_score, intent
                    )
                    matches.append(match)
        
        # Sort by score and remove duplicates by backend_node_id
        matches = self._deduplicate_matches(matches)
        matches.sort(key=lambda m: m.score, reverse=True)
        
        log.info(f"Found {len(matches)} DOM matches for target '{target_text}'")
        return matches
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison.
        
        Args:
            text: Text to normalize
            
        Returns:
            Normalized text
        """
        if not text:
            return ""
        
        # Basic normalization
        normalized = text.strip()
        
        # Case normalization
        if not self.case_sensitive:
            normalized = normalized.lower()
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)
        
        return normalized
    
    def _is_exact_match(self, attr_value: str, target_text: str) -> bool:
        """Check for exact text match.
        
        Args:
            attr_value: Attribute value
            target_text: Target text
            
        Returns:
            True if exact match
        """
        normalized_attr = self._normalize_text(attr_value)
        return normalized_attr == target_text
    
    def _calculate_partial_match(self, attr_value: str, target_text: str) -> float:
        """Calculate partial match score.
        
        Args:
            attr_value: Attribute value
            target_text: Target text
            
        Returns:
            Partial match score (0.0-1.0)
        """
        normalized_attr = self._normalize_text(attr_value)
        normalized_target = self._normalize_text(target_text)
        
        if not normalized_attr or not normalized_target:
            return 0.0
        
        # Check if target is contained in attribute
        if normalized_target in normalized_attr:
            return len(normalized_target) / len(normalized_attr)
        
        # Check word-level match
        target_words = set(normalized_target.split())
        attr_words = set(normalized_attr.split())
        
        if target_words.issubset(attr_words) and target_words:
            return len(target_words) / len(attr_words) * 0.8
        
        return 0.0
    
    def _is_element_visible(self, element: Dict[str, Any]) -> bool:
        """Check if element is visible and interactive.
        
        Args:
            element: Element descriptor
            
        Returns:
            True if element should be considered for matching
        """
        # Check visibility flag
        if not element.get("visible", True):
            return False
        
        # Check if element is disabled
        attrs = element.get("attributes", {})
        if attrs.get("disabled") or attrs.get("aria-disabled") == "true":
            return False
        
        # Check if element is hidden
        if attrs.get("hidden") or attrs.get("aria-hidden") == "true":
            return False
        
        # Check display style
        style = attrs.get("style", "")
        if "display: none" in style or "visibility: hidden" in style:
            return False
        
        return True
    
    def _is_element_interactive(self, element: Dict[str, Any], intent: str = "click") -> bool:
        """Check if element is interactive based on intent.
        
        Args:
            element: Element descriptor
            intent: User intent
            
        Returns:
            True if element is interactive for the given intent
        """
        tag = element.get("tag", "").lower()
        attrs = element.get("attributes", {})
        
        # Check for interactive indicators
        interactive_indicators = [
            'onclick', 'onmousedown', 'onmouseup', 'onkeydown', 'onkeyup',
            'role="button"', 'role="link"', 'role="menuitem"', 'role="tab"',
            'tabindex', 'data-click', 'data-action', 'data-toggle'
        ]
        
        has_interactive_indicator = any(
            indicator in str(attrs) for indicator in interactive_indicators
        )
        
        # Check for input elements
        is_input_element = tag in ['input', 'textarea', 'select', 'button']
        
        # Check for clickable elements
        is_clickable_element = tag in ['a', 'button'] or has_interactive_indicator
        
        # Check for contenteditable elements
        is_editable = attrs.get('contenteditable') == 'true'
        
        # Intent-specific checks
        if intent == "click":
            return is_clickable_element or (tag in ['span', 'div'] and has_interactive_indicator)
        elif intent in ["enter", "type", "search"]:
            return is_input_element or is_editable
        elif intent == "select":
            return (tag in ['select', 'option'] or 
                   attrs.get('role') in ['combobox', 'listbox', 'option'] or
                   'data-value' in attrs)
        elif intent == "validate":
            return True  # Most elements can be validated
        
        return is_input_element or is_clickable_element
    
    def _get_backend_node_id(self, element: Dict[str, Any]) -> Optional[str]:
        """Get backend node ID for element.
        
        Args:
            element: Element descriptor
            
        Returns:
            Backend node ID or None
        """
        # Try to get from element metadata
        meta = element.get("meta", {})
        backend_node_id = meta.get("backend_node_id")
        
        if backend_node_id:
            return str(backend_node_id)
        
        # Generate from element properties if not available
        tag = element.get("tag", "")
        attrs = element.get("attributes", {})
        text = element.get("text", "")
        
        # Create deterministic ID from element properties
        id_parts = [tag, attrs.get("id", ""), attrs.get("name", ""), text[:50]]
        id_string = "|".join(str(part) for part in id_parts if part)
        
        return f"node_{hash(id_string) % 1000000}"
    
    def _get_attribute_value(self, element: Dict[str, Any], attr_name: str) -> Optional[str]:
        """Get attribute value from element.
        
        Args:
            element: Element descriptor
            attr_name: Attribute name
            
        Returns:
            Attribute value or None
        """
        if attr_name == "innerText":
            return element.get("text", "")
        
        attrs = element.get("attributes", {})
        return attrs.get(attr_name)
    
    def _create_match(self, element: Dict[str, Any], backend_node_id: str,
                     match_type: MatchType, matched_text: str, score: float,
                     intent: str) -> DOMMatch:
        """Create DOM match object.
        
        Args:
            element: Element descriptor
            backend_node_id: Backend node ID
            match_type: Type of match
            matched_text: Matched text
            score: Match score
            intent: User intent
            
        Returns:
            DOM match object
        """
        # Build hierarchy path
        hierarchy_path = self._build_hierarchy_path(element)
        
        # Build canonical descriptor
        canonical_descriptor = self._build_canonical_descriptor(element)
        
        return DOMMatch(
            element=element,
            backend_node_id=backend_node_id,
            match_type=match_type,
            matched_text=matched_text,
            score=score,
            hierarchy_path=hierarchy_path,
            canonical_descriptor=canonical_descriptor
        )
    
    def _build_hierarchy_path(self, element: Dict[str, Any]) -> str:
        """Build hierarchy path for element.
        
        Args:
            element: Element descriptor
            
        Returns:
            Hierarchy path string
        """
        # Get parent hierarchy from element metadata
        meta = element.get("meta", {})
        parent_hierarchy = meta.get("parent_hierarchy", [])
        
        # Build path from parent hierarchy
        path_parts = []
        for parent in parent_hierarchy:
            tag = parent.get("tag", "")
            attrs = parent.get("attributes", {})
            
            # Add tag and key attributes
            part = tag
            if attrs.get("id"):
                part += f"#{attrs['id']}"
            elif attrs.get("class"):
                classes = attrs["class"].split()[:2]  # First 2 classes
                part += f".{'.'.join(classes)}"
            
            path_parts.append(part)
        
        # Add current element
        tag = element.get("tag", "")
        attrs = element.get("attributes", {})
        current_part = tag
        if attrs.get("id"):
            current_part += f"#{attrs['id']}"
        elif attrs.get("class"):
            classes = attrs["class"].split()[:2]
            current_part += f".{'.'.join(classes)}"
        
        path_parts.append(current_part)
        
        return " > ".join(path_parts)
    
    def _build_canonical_descriptor(self, element: Dict[str, Any]) -> str:
        """Build canonical descriptor for element.
        
        Args:
            element: Element descriptor
            
        Returns:
            Canonical descriptor string
        """
        tag = element.get("tag", "")
        attrs = element.get("attributes", {})
        text = element.get("text", "")
        
        # Build descriptor parts
        parts = [tag]
        
        # Add key attributes
        key_attrs = ["id", "name", "type", "class", "role", "aria-label"]
        for attr in key_attrs:
            if attr in attrs:
                value = attrs[attr]
                if value:
                    parts.append(f"{attr}={value}")
        
        # Add text if present and not too long
        if text and len(text) < 50:
            parts.append(f"text={text}")
        
        return " ".join(parts)
    
    def _deduplicate_matches(self, matches: List[DOMMatch]) -> List[DOMMatch]:
        """Remove duplicate matches by backend_node_id.
        
        Args:
            matches: List of matches
            
        Returns:
            Deduplicated matches
        """
        seen_ids = set()
        unique_matches = []
        
        for match in matches:
            if match.backend_node_id not in seen_ids:
                seen_ids.add(match.backend_node_id)
                unique_matches.append(match)
        
        return unique_matches
    
    def get_matches_by_backend_node_id(self, matches: List[DOMMatch], 
                                     backend_node_id: str) -> List[DOMMatch]:
        """Get matches by backend node ID.
        
        Args:
            matches: List of matches
            backend_node_id: Backend node ID to filter by
            
        Returns:
            Filtered matches
        """
        return [match for match in matches if match.backend_node_id == backend_node_id]