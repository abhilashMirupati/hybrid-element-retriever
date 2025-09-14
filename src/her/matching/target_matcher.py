"""
Target Text Matcher for HER Framework

Matches target text against canonical nodes using:
- innerText matching
- Attribute matching (id, aria-label, title, placeholder)
- Fuzzy matching for partial matches

Handles:
- 0 matches → ElementNotFoundError
- 1 match → return directly
- >1 match → forward to reranker
"""

from __future__ import annotations

import logging
import re
from typing import List, Optional, Tuple

from ..descriptors.canonical import CanonicalNode
from ..exceptions import ElementNotFoundError

logger = logging.getLogger(__name__)


class TargetTextMatcher:
    """Matches target text against canonical nodes."""
    
    def __init__(self):
        # Text normalization patterns
        self.normalize_patterns = [
            (r'\s+', ' '),  # Multiple whitespace to single space
            (r'[^\w\s]', ''),  # Remove punctuation for fuzzy matching
        ]
        
        # Attribute priority for matching
        self.attribute_priority = [
            'aria-label',
            'title', 
            'placeholder',
            'id',
            'name',
            'value',
            'data-testid',
            'data-label'
        ]
    
    def match_target(
        self, 
        target_text: str, 
        canonical_nodes: List[CanonicalNode]
    ) -> List[CanonicalNode]:
        """
        Match target text against canonical nodes.
        
        Args:
            target_text: Target text to match (e.g., "Login", "Username")
            canonical_nodes: List of canonical nodes to search
            
        Returns:
            List of matching canonical nodes
            
        Raises:
            ElementNotFoundError: If no matches found
        """
        if not target_text or not canonical_nodes:
            raise ElementNotFoundError(f"No target text or nodes provided")
        
        # Normalize target text
        normalized_target = self._normalize_text(target_text)
        
        # Find matches
        matches = self._find_matches(normalized_target, canonical_nodes)
        
        if not matches:
            raise ElementNotFoundError(f"No elements found matching target: '{target_text}'")
        
        # Sort by match quality
        matches.sort(key=lambda node: self._calculate_match_score(normalized_target, node), reverse=True)
        
        logger.info(f"Found {len(matches)} matches for target: '{target_text}'")
        return matches
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for matching."""
        if not text:
            return ''
        
        normalized = text.strip()
        
        # Apply normalization patterns
        for pattern, replacement in self.normalize_patterns:
            normalized = re.sub(pattern, replacement, normalized)
        
        return normalized.lower()
    
    def _find_matches(self, normalized_target: str, canonical_nodes: List[CanonicalNode]) -> List[CanonicalNode]:
        """Find all nodes that match the target text."""
        matches = []
        
        for node in canonical_nodes:
            if self._node_matches(normalized_target, node):
                matches.append(node)
        
        return matches
    
    def _node_matches(self, normalized_target: str, node: CanonicalNode) -> bool:
        """Check if a node matches the target text."""
        # Check inner text
        if self._text_matches(normalized_target, node.inner_text):
            return True
        
        # Check attributes
        for attr_name in self.attribute_priority:
            attr_value = getattr(node, attr_name, '')
            if attr_value and self._text_matches(normalized_target, attr_value):
                return True
        
        return False
    
    def _text_matches(self, target: str, text: str) -> bool:
        """Check if target text matches the given text."""
        if not text:
            return False
        
        normalized_text = self._normalize_text(text)
        
        # Exact match
        if target == normalized_text:
            return True
        
        # Contains match
        if target in normalized_text:
            return True
        
        # Word boundary match
        if self._word_boundary_match(target, normalized_text):
            return True
        
        # Fuzzy match for partial words
        if self._fuzzy_match(target, normalized_text):
            return True
        
        return False
    
    def _word_boundary_match(self, target: str, text: str) -> bool:
        """Check for word boundary matches."""
        target_words = target.split()
        text_words = text.split()
        
        # Check if all target words are in text
        return all(word in text_words for word in target_words)
    
    def _fuzzy_match(self, target: str, text: str) -> bool:
        """Check for fuzzy matches (partial word matches)."""
        target_words = target.split()
        text_words = text.split()
        
        # Check if any target word is a substring of any text word
        for target_word in target_words:
            if any(target_word in text_word for text_word in text_words):
                return True
        
        return False
    
    def _calculate_match_score(self, target: str, node: CanonicalNode) -> float:
        """Calculate match quality score for ranking."""
        score = 0.0
        
        # Check inner text match
        if node.inner_text:
            text_score = self._calculate_text_score(target, node.inner_text)
            score += text_score * 1.0  # Highest weight for inner text
        
        # Check attribute matches
        for attr_name in self.attribute_priority:
            attr_value = getattr(node, attr_name, '')
            if attr_value:
                attr_score = self._calculate_text_score(target, attr_value)
                # Weight by attribute priority
                weight = 1.0 - (self.attribute_priority.index(attr_name) * 0.1)
                score += attr_score * weight
        
        # Bonus for interactive elements
        if node.is_interactive:
            score += 0.1
        
        return score
    
    def _calculate_text_score(self, target: str, text: str) -> float:
        """Calculate text matching score."""
        if not text:
            return 0.0
        
        normalized_text = self._normalize_text(text)
        
        # Exact match
        if target == normalized_text:
            return 1.0
        
        # Contains match
        if target in normalized_text:
            return 0.8
        
        # Word boundary match
        if self._word_boundary_match(target, normalized_text):
            return 0.6
        
        # Fuzzy match
        if self._fuzzy_match(target, normalized_text):
            return 0.4
        
        return 0.0
    
    def get_match_explanation(self, target: str, node: CanonicalNode) -> str:
        """Get explanation of why a node matches the target."""
        explanations = []
        
        # Check inner text
        if node.inner_text and self._text_matches(self._normalize_text(target), node.inner_text):
            explanations.append(f"inner_text: '{node.inner_text}'")
        
        # Check attributes
        for attr_name in self.attribute_priority:
            attr_value = getattr(node, attr_name, '')
            if attr_value and self._text_matches(self._normalize_text(target), attr_value):
                explanations.append(f"{attr_name}: '{attr_value}'")
        
        return " | ".join(explanations) if explanations else "no clear match"


class ElementNotFoundError(Exception):
    """Raised when no elements match the target text."""
    
    def __init__(self, message: str, target_text: str = "", suggestions: List[str] = None):
        super().__init__(message)
        self.target_text = target_text
        self.suggestions = suggestions or []
    
    def __str__(self) -> str:
        msg = super().__str__()
        if self.suggestions:
            msg += f"\nSuggestions: {', '.join(self.suggestions[:5])}"
        return msg


def match_target_text(target_text: str, canonical_nodes: List[CanonicalNode]) -> List[CanonicalNode]:
    """
    Convenience function to match target text against canonical nodes.
    
    Args:
        target_text: Target text to match
        canonical_nodes: List of canonical nodes to search
        
    Returns:
        List of matching canonical nodes
        
    Raises:
        ElementNotFoundError: If no matches found
    """
    matcher = TargetTextMatcher()
    return matcher.match_target(target_text, canonical_nodes)