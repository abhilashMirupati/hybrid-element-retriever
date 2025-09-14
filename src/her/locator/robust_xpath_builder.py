"""
Robust XPath Builder for HER Framework

Builds robust relative XPath selectors with:
- Text-based selectors (preferred for stability)
- Attribute-based fallbacks
- Position-based fallbacks (avoided when possible)
- Deterministic generation across runs
"""

from __future__ import annotations

import logging
import re
from typing import Dict, List, Optional, Tuple

from ..descriptors.canonical import CanonicalNode
from ..exceptions import XPathGenerationError

logger = logging.getLogger(__name__)


class RobustXPathBuilder:
    """Builds robust XPath selectors for elements."""
    
    def __init__(self):
        # Attribute priority for XPath generation
        self.attribute_priority = [
            'id',
            'data-testid', 
            'name',
            'aria-label',
            'title',
            'placeholder',
            'value',
            'class',
            'type',
            'href'
        ]
        
        # Text-based selector patterns
        self.text_patterns = [
            'normalize-space()',  # Most stable
            'contains(normalize-space(), "{}")',  # Partial match
            'starts-with(normalize-space(), "{}")',  # Prefix match
        ]
        
        # Attributes that are stable across page loads
        self.stable_attributes = {
            'id', 'data-testid', 'name', 'aria-label', 'title'
        }
        
        # Attributes that might change
        self.unstable_attributes = {
            'class', 'style', 'data-reactid', 'data-reactroot'
        }
    
    def build_xpath(self, node: CanonicalNode) -> str:
        """
        Build robust XPath for a canonical node.
        
        Args:
            node: CanonicalNode to build XPath for
            
        Returns:
            Robust XPath selector
            
        Raises:
            XPathGenerationError: If XPath generation fails
        """
        if not node.tag:
            raise XPathGenerationError("Cannot build XPath for node without tag")
        
        # Try different strategies in order of preference
        strategies = [
            self._build_text_based_xpath,
            self._build_attribute_based_xpath,
            self._build_hybrid_xpath,
            self._build_position_based_xpath
        ]
        
        for strategy in strategies:
            try:
                xpath = strategy(node)
                if xpath and self._is_valid_xpath(xpath):
                    logger.debug(f"Generated XPath using {strategy.__name__}: {xpath}")
                    return xpath
            except Exception as e:
                logger.debug(f"Strategy {strategy.__name__} failed: {e}")
                continue
        
        # Fallback to basic tag selector
        return f"//{node.tag.lower()}"
    
    def _build_text_based_xpath(self, node: CanonicalNode) -> Optional[str]:
        """Build XPath using text content (most stable)."""
        if not node.inner_text or len(node.inner_text) > 100:
            return None
        
        # Escape quotes in text
        escaped_text = self._escape_xpath_string(node.inner_text)
        
        # Use normalize-space for stability
        tag = node.tag.lower()
        return f"//{tag}[normalize-space()='{escaped_text}']"
    
    def _build_attribute_based_xpath(self, node: CanonicalNode) -> Optional[str]:
        """Build XPath using stable attributes."""
        tag = node.tag.lower()
        
        # Try stable attributes first
        for attr in self.attribute_priority:
            if attr in self.stable_attributes:
                value = getattr(node, attr, '')
                if value and self._is_stable_value(value):
                    escaped_value = self._escape_xpath_string(value)
                    return f"//{tag}[@{attr}='{escaped_value}']"
        
        # Try other attributes
        for attr in self.attribute_priority:
            if attr not in self.unstable_attributes:
                value = getattr(node, attr, '')
                if value and self._is_stable_value(value):
                    escaped_value = self._escape_xpath_string(value)
                    return f"//{tag}[@{attr}='{escaped_value}']"
        
        return None
    
    def _build_hybrid_xpath(self, node: CanonicalNode) -> Optional[str]:
        """Build XPath combining text and attributes."""
        tag = node.tag.lower()
        conditions = []
        
        # Add text condition if available
        if node.inner_text and len(node.inner_text) <= 100:
            escaped_text = self._escape_xpath_string(node.inner_text)
            conditions.append(f"normalize-space()='{escaped_text}'")
        
        # Add attribute conditions
        for attr in self.attribute_priority:
            if attr in self.stable_attributes:
                value = getattr(node, attr, '')
                if value and self._is_stable_value(value):
                    escaped_value = self._escape_xpath_string(value)
                    conditions.append(f"@{attr}='{escaped_value}'")
                    break  # Only use one attribute for simplicity
        
        if conditions:
            condition_str = ' and '.join(conditions)
            return f"//{tag}[{condition_str}]"
        
        return None
    
    def _build_position_based_xpath(self, node: CanonicalNode) -> str:
        """Build XPath using position (last resort)."""
        tag = node.tag.lower()
        
        # Try to use parent context if available
        if node.parent_tag:
            parent_tag = node.parent_tag.lower()
            if node.siblings_count > 1:
                # Use position within parent
                return f"//{parent_tag}/{tag}[{node.siblings_count}]"
            else:
                # Only child
                return f"//{parent_tag}/{tag}"
        
        # Fallback to tag with position
        return f"//{tag}[1]"
    
    def _escape_xpath_string(self, text: str) -> str:
        """Escape string for XPath."""
        if not text:
            return ''
        
        # Escape quotes
        if "'" in text and '"' in text:
            # Both quotes present, use concat
            parts = text.split("'")
            escaped_parts = []
            for i, part in enumerate(parts):
                if i > 0:
                    escaped_parts.append("'")
                escaped_parts.append(f'"{part}"')
            return f"concat({','.join(escaped_parts)})"
        elif "'" in text:
            # Single quotes, use double quotes
            return text.replace('"', '\\"')
        else:
            # No quotes, use single quotes
            return text.replace("'", "\\'")
    
    def _is_stable_value(self, value: str) -> bool:
        """Check if attribute value is stable across page loads."""
        if not value:
            return False
        
        # Check for dynamic patterns
        dynamic_patterns = [
            r'\d{13,}',  # Timestamps
            r'[a-f0-9]{8,}',  # UUIDs/hashes
            r'react-\d+',  # React IDs
            r'data-reactid',  # React attributes
            r'__\w+__',  # Generated IDs
        ]
        
        for pattern in dynamic_patterns:
            if re.search(pattern, value):
                return False
        
        return True
    
    def _is_valid_xpath(self, xpath: str) -> bool:
        """Basic XPath validation."""
        if not xpath:
            return False
        
        # Check for basic XPath structure
        if not xpath.startswith('//'):
            return False
        
        # Check for balanced brackets
        if xpath.count('[') != xpath.count(']'):
            return False
        
        return True
    
    def build_alternative_xpaths(self, node: CanonicalNode, max_alternatives: int = 3) -> List[str]:
        """
        Build multiple alternative XPath selectors.
        
        Args:
            node: CanonicalNode to build XPaths for
            max_alternatives: Maximum number of alternatives
            
        Returns:
            List of alternative XPath selectors
        """
        alternatives = []
        
        # Try different strategies
        strategies = [
            self._build_text_based_xpath,
            self._build_attribute_based_xpath,
            self._build_hybrid_xpath,
        ]
        
        for strategy in strategies:
            try:
                xpath = strategy(node)
                if xpath and xpath not in alternatives:
                    alternatives.append(xpath)
                    if len(alternatives) >= max_alternatives:
                        break
            except Exception:
                continue
        
        # Add position-based as last resort
        if len(alternatives) < max_alternatives:
            try:
                xpath = self._build_position_based_xpath(node)
                if xpath and xpath not in alternatives:
                    alternatives.append(xpath)
            except Exception:
                pass
        
        return alternatives
    
    def validate_xpath(self, xpath: str) -> Tuple[bool, str]:
        """
        Validate XPath selector.
        
        Args:
            xpath: XPath to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not xpath:
            return False, "Empty XPath"
        
        if not xpath.startswith('//'):
            return False, "XPath must start with //"
        
        if xpath.count('[') != xpath.count(']'):
            return False, "Unbalanced brackets"
        
        if xpath.count('(') != xpath.count(')'):
            return False, "Unbalanced parentheses"
        
        # Check for common issues
        if '//' in xpath[2:]:
            return False, "Multiple // not allowed in relative XPath"
        
        return True, "Valid XPath"


def build_robust_xpath(node: CanonicalNode) -> str:
    """
    Convenience function to build robust XPath for a canonical node.
    
    Args:
        node: CanonicalNode to build XPath for
        
    Returns:
        Robust XPath selector
    """
    builder = RobustXPathBuilder()
    return builder.build_xpath(node)


def build_alternative_xpaths(node: CanonicalNode, max_alternatives: int = 3) -> List[str]:
    """
    Convenience function to build alternative XPath selectors.
    
    Args:
        node: CanonicalNode to build XPaths for
        max_alternatives: Maximum number of alternatives
        
    Returns:
        List of alternative XPath selectors
    """
    builder = RobustXPathBuilder()
    return builder.build_alternative_xpaths(node, max_alternatives)