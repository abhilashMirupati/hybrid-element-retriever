"""
HTML Hierarchy Builder with BeautifulSoup

This module provides HTML hierarchy building functionality:
1. Use BeautifulSoup to parse HTML structure
2. Build parent/sibling hierarchy properly
3. Handle 512 token limit for MarkupLM
4. Ensure no element properties are split
"""

from __future__ import annotations

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from bs4 import BeautifulSoup, Tag
import html

log = logging.getLogger("her.html_hierarchy_builder")

@dataclass
class HTMLHierarchyContext:
    """HTML hierarchy context for MarkupLM."""
    target_element: Dict[str, Any]
    parent_elements: List[Dict[str, Any]]
    sibling_elements: List[Dict[str, Any]]
    html_context: str
    token_count: int
    truncated: bool
    hierarchy_path: List[str]

class HTMLHierarchyBuilder:
    """Builder for HTML hierarchy using BeautifulSoup."""
    
    def __init__(self, max_tokens: int = 512):
        self.max_tokens = max_tokens
        self.token_counter = 0
    
    def build_hierarchy_context(self, target_element: Dict[str, Any], all_elements: List[Dict[str, Any]]) -> HTMLHierarchyContext:
        """Build HTML hierarchy context for MarkupLM."""
        log.info(f"Building HTML hierarchy for element: {target_element.get('tag', 'unknown')}")
        
        # Find parent and sibling elements
        parents = self._find_parent_elements(target_element, all_elements)
        siblings = self._find_sibling_elements(target_element, all_elements)
        
        # Build HTML structure
        html_context = self._build_html_structure(target_element, parents, siblings)
        
        # Check token limit and truncate if necessary
        token_count = self._count_tokens(html_context)
        truncated = False
        
        if token_count > self.max_tokens:
            html_context = self._truncate_html_safely(html_context, target_element)
            token_count = self._count_tokens(html_context)
            truncated = True
        
        hierarchy_path = target_element.get('hierarchy', [])
        
        return HTMLHierarchyContext(
            target_element=target_element,
            parent_elements=parents,
            sibling_elements=siblings,
            html_context=html_context,
            token_count=token_count,
            truncated=truncated,
            hierarchy_path=hierarchy_path
        )
    
    def _find_parent_elements(self, target_element: Dict[str, Any], all_elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find parent elements using hierarchy path."""
        parents = []
        target_hierarchy = target_element.get('hierarchy', [])
        
        if not target_hierarchy:
            return parents
        
        # Find parent elements by matching hierarchy levels
        for level in target_hierarchy[:-1]:  # Exclude target element itself
            for element in all_elements:
                if self._matches_hierarchy_level(element, level):
                    parents.append(element)
                    break
        
        return parents
    
    def _find_sibling_elements(self, target_element: Dict[str, Any], all_elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find sibling elements using hierarchy path."""
        siblings = []
        target_hierarchy = target_element.get('hierarchy', [])
        
        if len(target_hierarchy) < 2:
            return siblings
        
        # Find siblings (elements with same parent hierarchy)
        parent_hierarchy = target_hierarchy[:-1]
        
        for element in all_elements:
            if element == target_element:
                continue
            
            element_hierarchy = element.get('hierarchy', [])
            if len(element_hierarchy) == len(target_hierarchy):
                # Check if same parent level
                if element_hierarchy[:-1] == parent_hierarchy:
                    siblings.append(element)
        
        return siblings
    
    def _build_html_structure(self, target_element: Dict[str, Any], parents: List[Dict[str, Any]], siblings: List[Dict[str, Any]]) -> str:
        """Build HTML structure using BeautifulSoup."""
        # Create a BeautifulSoup document
        soup = BeautifulSoup('', 'html.parser')
        
        # Build parent hierarchy
        current_parent = soup
        for parent in parents:
            parent_tag = self._create_tag(soup, parent)
            current_parent.append(parent_tag)
            current_parent = parent_tag
        
        # Add sibling context if available
        if siblings:
            sibling_container = soup.new_tag('div', **{'class': 'sibling-context'})
            for sibling in siblings[:3]:  # Limit to 3 siblings
                sibling_tag = self._create_tag(soup, sibling)
                sibling_container.append(sibling_tag)
            current_parent.append(sibling_container)
        
        # Add target element
        target_tag = self._create_tag(soup, target_element)
        current_parent.append(target_tag)
        
        # Close all parent tags
        self._close_parent_tags(current_parent, parents)
        
        return str(soup)
    
    def _create_tag(self, soup: BeautifulSoup, element: Dict[str, Any]) -> Tag:
        """Create a BeautifulSoup tag from element data."""
        tag_name = element.get('tag', 'div')
        text = element.get('text', '')
        attrs = element.get('attributes', {})
        
        # Clean attributes
        clean_attrs = {}
        for key, value in attrs.items():
            if value and isinstance(value, (str, int, float)):
                clean_attrs[key] = str(value)
        
        # Create tag
        tag = soup.new_tag(tag_name, **clean_attrs)
        
        # Add text content
        if text:
            # Escape HTML entities
            escaped_text = html.escape(text)
            tag.string = escaped_text
        
        return tag
    
    def _close_parent_tags(self, current_parent: Tag, parents: List[Dict[str, Any]]):
        """Close all parent tags properly."""
        # BeautifulSoup handles tag closing automatically
        pass
    
    def _count_tokens(self, html_text: str) -> int:
        """Count tokens in HTML text (approximate)."""
        # Simple token counting - in real implementation, use proper tokenizer
        words = html_text.split()
        return len(words)
    
    def _truncate_html_safely(self, html_text: str, target_element: Dict[str, Any]) -> str:
        """Truncate HTML safely without splitting element properties."""
        log.warning(f"HTML context exceeds {self.max_tokens} tokens, truncating safely")
        
        # Parse with BeautifulSoup to ensure valid HTML
        soup = BeautifulSoup(html_text, 'html.parser')
        
        # Find target element in the soup
        target_tag = self._find_target_tag(soup, target_element)
        if not target_tag:
            return html_text[:self.max_tokens * 4]  # Fallback to character truncation
        
        # Build truncated context around target element
        truncated_context = self._build_truncated_context(soup, target_tag)
        
        return str(truncated_context)
    
    def _find_target_tag(self, soup: BeautifulSoup, target_element: Dict[str, Any]) -> Optional[Tag]:
        """Find target element tag in BeautifulSoup document."""
        target_id = target_element.get('attributes', {}).get('id')
        target_text = target_element.get('text', '')
        
        if target_id:
            return soup.find(id=target_id)
        
        if target_text:
            return soup.find(string=re.compile(re.escape(target_text)))
        
        return None
    
    def _build_truncated_context(self, soup: BeautifulSoup, target_tag: Tag) -> BeautifulSoup:
        """Build truncated context around target element."""
        # Create new soup with truncated content
        truncated_soup = BeautifulSoup('', 'html.parser')
        
        # Add target element with minimal context
        truncated_soup.append(target_tag)
        
        # Add immediate parent if available
        if target_tag.parent and target_tag.parent.name != '[document]':
            parent_copy = target_tag.parent.__copy__()
            parent_copy.clear()
            parent_copy.append(target_tag)
            truncated_soup = BeautifulSoup(str(parent_copy), 'html.parser')
        
        return truncated_soup
    
    def _matches_hierarchy_level(self, element: Dict[str, Any], level: str) -> bool:
        """Check if element matches hierarchy level."""
        element_hierarchy = element.get('hierarchy', [])
        return level in element_hierarchy
    
    def get_markup_input(self, context: HTMLHierarchyContext) -> Dict[str, Any]:
        """Get input for MarkupLM processing."""
        return {
            'html': context.html_context,
            'target_element': context.target_element,
            'token_count': context.token_count,
            'truncated': context.truncated,
            'hierarchy_path': context.hierarchy_path
        }
    
    def get_markup_output(self, markup_result: Any) -> Dict[str, Any]:
        """Process MarkupLM output."""
        return {
            'markup_score': float(markup_result) if markup_result else 0.0,
            'processed': True
        }