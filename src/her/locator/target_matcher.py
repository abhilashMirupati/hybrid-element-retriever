"""
Target Matcher - DOM Exact Matching for No-Semantic Mode

This module provides exact DOM matching capabilities for the no-semantic retrieval mode.
It matches quoted targets against DOM attributes and text content without using embeddings.

Supported matching attributes:
- innerText (text content)
- aria-label
- title
- placeholder
- id
- name
- value (for form elements)
- data-testid
- data-test-id
"""

from __future__ import annotations

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

log = logging.getLogger("her.target_matcher")


@dataclass
class MatchResult:
    """Result of a target match operation."""
    element: Dict[str, Any]
    score: float
    match_type: str
    matched_attribute: str
    matched_value: str
    reasons: List[str]


class TargetMatcher:
    """DOM exact matcher for no-semantic retrieval mode."""
    
    # Priority order for matching attributes (higher index = higher priority)
    MATCH_ATTRIBUTES = [
        "innerText",      # Text content
        "aria-label",     # Accessibility label
        "title",          # Title attribute
        "placeholder",    # Placeholder text
        "id",            # Element ID
        "name",          # Form element name
        "value",         # Form element value
        "data-testid",   # Test ID
        "data-test-id",  # Alternative test ID
    ]
    
    def __init__(self, case_sensitive: bool = False):
        """Initialize target matcher.
        
        Args:
            case_sensitive: Whether to perform case-sensitive matching
        """
        self.case_sensitive = case_sensitive
    
    def extract_quoted_target(self, target: str) -> Optional[str]:
        """Extract quoted text from target string.
        
        Args:
            target: Target string like 'the "Phones" button' or 'click "Submit"'
            
        Returns:
            Extracted quoted text or None if no quotes found
        """
        if not target:
            return None
        
        # Look for quoted text in various formats
        patterns = [
            r'"([^"]+)"',  # "text"
            r"'([^']+)'",  # 'text'
            r'`([^`]+)`',  # `text`
        ]
        
        for pattern in patterns:
            match = re.search(pattern, target)
            if match:
                return match.group(1).strip()
        
        # If no quotes found, return the whole string cleaned up
        cleaned = target.strip().replace('"', '').replace("'", '').replace('`', '')
        return cleaned if cleaned else None
    
    def normalize_text(self, text: str) -> str:
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
    
    def match_element(self, element: Dict[str, Any], target: str) -> Optional[MatchResult]:
        """Match a single element against a target.
        
        Args:
            element: Element descriptor
            target: Target string to match
            
        Returns:
            MatchResult if match found, None otherwise
        """
        if not target:
            return None
        
        # Extract quoted target
        quoted_target = self.extract_quoted_target(target)
        if not quoted_target:
            return None
        
        # Normalize target for comparison
        normalized_target = self.normalize_text(quoted_target)
        if not normalized_target:
            return None
        
        # Skip hidden or disabled elements
        if not self._is_element_visible(element):
            return None
        
        # Check each attribute in priority order
        for attr in self.MATCH_ATTRIBUTES:
            value = self._get_attribute_value(element, attr)
            if not value:
                continue
            
            normalized_value = self.normalize_text(value)
            if not normalized_value:
                continue
            
            # Check for exact match
            if normalized_value == normalized_target:
                return MatchResult(
                    element=element,
                    score=1.0,
                    match_type="exact",
                    matched_attribute=attr,
                    matched_value=value,
                    reasons=[f"exact_{attr}_match"]
                )
            
            # Check for partial match (target is contained in value)
            if normalized_target in normalized_value:
                # Calculate partial match score based on length ratio
                score = len(normalized_target) / len(normalized_value)
                return MatchResult(
                    element=element,
                    score=score,
                    match_type="partial",
                    matched_attribute=attr,
                    matched_value=value,
                    reasons=[f"partial_{attr}_match"]
                )
            
            # Check for word-level match
            target_words = set(normalized_target.split())
            value_words = set(normalized_value.split())
            if target_words.issubset(value_words) and target_words:
                # Calculate word match score
                score = len(target_words) / len(value_words) * 0.8  # Slightly lower than partial
                return MatchResult(
                    element=element,
                    score=score,
                    match_type="word",
                    matched_attribute=attr,
                    matched_value=value,
                    reasons=[f"word_{attr}_match"]
                )
        
        return None
    
    def match_elements(self, elements: List[Dict[str, Any]], target: str) -> List[MatchResult]:
        """Match multiple elements against a target.
        
        Args:
            elements: List of element descriptors
            target: Target string to match
            
        Returns:
            List of MatchResults sorted by score (highest first)
        """
        if not elements or not target:
            return []
        
        matches = []
        for element in elements:
            match = self.match_element(element, target)
            if match:
                matches.append(match)
        
        # Sort by score (highest first), then by match type priority
        type_priority = {"exact": 3, "partial": 2, "word": 1}
        matches.sort(key=lambda m: (m.score, type_priority.get(m.match_type, 0)), reverse=True)
        
        return matches
    
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
        
        # Check display style (basic check)
        style = attrs.get("style", "")
        if "display: none" in style or "visibility: hidden" in style:
            return False
        
        return True
    
    def _get_attribute_value(self, element: Dict[str, Any], attr: str) -> Optional[str]:
        """Get attribute value from element.
        
        Args:
            element: Element descriptor
            attr: Attribute name
            
        Returns:
            Attribute value or None
        """
        if attr == "innerText":
            return element.get("text", "")
        
        attrs = element.get("attributes", {})
        return attrs.get(attr)
    
    def get_best_match(self, elements: List[Dict[str, Any]], target: str) -> Optional[MatchResult]:
        """Get the best matching element for a target.
        
        Args:
            elements: List of element descriptors
            target: Target string to match
            
        Returns:
            Best MatchResult or None if no matches
        """
        matches = self.match_elements(elements, target)
        return matches[0] if matches else None
    
    def get_multiple_matches(self, elements: List[Dict[str, Any]], target: str, 
                           min_score: float = 0.5) -> List[MatchResult]:
        """Get multiple matching elements above a minimum score.
        
        Args:
            elements: List of element descriptors
            target: Target string to match
            min_score: Minimum score threshold
            
        Returns:
            List of MatchResults above threshold
        """
        matches = self.match_elements(elements, target)
        return [m for m in matches if m.score >= min_score]


class AccessibilityFallbackMatcher:
    """Fallback matcher for accessibility tree when DOM has no matches."""
    
    def __init__(self, case_sensitive: bool = False):
        """Initialize accessibility fallback matcher.
        
        Args:
            case_sensitive: Whether to perform case-sensitive matching
        """
        self.case_sensitive = case_sensitive
    
    def match_accessibility_elements(self, ax_elements: List[Dict[str, Any]], 
                                   target: str) -> List[MatchResult]:
        """Match accessibility tree elements.
        
        Args:
            ax_elements: List of accessibility tree elements
            target: Target string to match
            
        Returns:
            List of MatchResults
        """
        if not ax_elements or not target:
            return []
        
        # Use the same target matcher logic but for AX elements
        matcher = TargetMatcher(case_sensitive=self.case_sensitive)
        
        # Convert AX elements to element format
        elements = []
        for ax_el in ax_elements:
            element = {
                "text": ax_el.get("name", ""),
                "attributes": {
                    "role": ax_el.get("role", ""),
                    "aria-label": ax_el.get("name", ""),
                },
                "visible": True,  # AX elements are typically visible
            }
            elements.append(element)
        
        return matcher.match_elements(elements, target)