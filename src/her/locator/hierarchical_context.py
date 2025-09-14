"""
Hierarchical Context Building for No-Semantic Mode

This module provides hierarchical context building functionality:
1. Build parent/sibling hierarchy for matching nodes only
2. Create rich HTML context for MarkupLM ranking
3. Handle nested matches and edge cases
4. Optimize hierarchy building performance
"""

from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .core_no_semantic import ExactMatch

log = logging.getLogger("her.hierarchical_context")

@dataclass
class HierarchicalContext:
    """Hierarchical context for a matching node."""
    target_element: ExactMatch
    parent_elements: List[Dict[str, Any]]
    sibling_elements: List[Dict[str, Any]]
    html_context: str
    depth: int
    semantic_structure: str
    hierarchy_path: List[str]

class HierarchicalContextBuilder:
    """Builder for hierarchical context with performance optimization."""
    
    def __init__(self):
        self.context_cache = {}  # Cache for performance
    
    def build_contexts(self, matches: List[ExactMatch], all_elements: List[Dict[str, Any]]) -> List[HierarchicalContext]:
        """Build hierarchical context for each matching node."""
        contexts = []
        
        log.info(f"Building hierarchical context for {len(matches)} matches")
        
        for match in matches:
            # Use cache if available
            cache_key = self._get_cache_key(match, all_elements)
            if cache_key in self.context_cache:
                contexts.append(self.context_cache[cache_key])
                continue
            
            # Build new context
            context = self._build_single_context(match, all_elements)
            contexts.append(context)
            
            # Cache the result
            self.context_cache[cache_key] = context
        
        log.info(f"Built hierarchical context for {len(contexts)} matches")
        return contexts
    
    def _build_single_context(self, match: ExactMatch, all_elements: List[Dict[str, Any]]) -> HierarchicalContext:
        """Build hierarchical context for a single match."""
        element = match.element
        
        # Find parent elements
        parents = self._find_parent_elements(element, all_elements)
        
        # Find sibling elements
        siblings = self._find_sibling_elements(element, all_elements)
        
        # Build HTML context
        html_context = self._build_html_context(match, parents, siblings)
        
        # Build semantic structure
        semantic_structure = self._build_semantic_structure(match, parents, siblings)
        
        # Get hierarchy path
        hierarchy_path = element.get('hierarchy', [])
        
        return HierarchicalContext(
            target_element=match,
            parent_elements=parents,
            sibling_elements=siblings,
            html_context=html_context,
            depth=len(parents),
            semantic_structure=semantic_structure,
            hierarchy_path=hierarchy_path
        )
    
    def _find_parent_elements(self, element: Dict[str, Any], all_elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find parent elements for hierarchical context."""
        parents = []
        hierarchy = element.get('hierarchy', [])
        
        # Find parent elements by matching hierarchy
        for level in hierarchy:
            for elem in all_elements:
                if self._matches_hierarchy_level(elem, level):
                    parents.append(elem)
                    break
        
        return parents
    
    def _find_sibling_elements(self, element: Dict[str, Any], all_elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find sibling elements for hierarchical context."""
        siblings = []
        element_hierarchy = element.get('hierarchy', [])
        
        if not element_hierarchy:
            return siblings
        
        # Find siblings (elements with same parent hierarchy)
        parent_hierarchy = element_hierarchy[:-1]  # All but last level
        
        for elem in all_elements:
            if elem == element:
                continue
            
            elem_hierarchy = elem.get('hierarchy', [])
            if len(elem_hierarchy) == len(element_hierarchy):
                # Check if same parent level
                if elem_hierarchy[:-1] == parent_hierarchy:
                    siblings.append(elem)
        
        return siblings
    
    def _build_html_context(self, match: ExactMatch, parents: List[Dict[str, Any]], siblings: List[Dict[str, Any]]) -> str:
        """Build hierarchical HTML context for MarkupLM."""
        html_parts = []
        
        # Build parent context
        for parent in parents:
            tag = parent.get('tag', 'div')
            attrs = parent.get('attributes', {})
            
            attr_str = self._build_attribute_string(attrs)
            html_parts.append(f'<{tag}{attr_str}>')
        
        # Build sibling context
        if siblings:
            html_parts.append('<div class="sibling-context">')
            for sibling in siblings[:3]:  # Limit to 3 siblings for performance
                tag = sibling.get('tag', 'span')
                text = sibling.get('text', '')[:50]  # Truncate long text
                attrs = sibling.get('attributes', {})
                attr_str = self._build_attribute_string(attrs)
                html_parts.append(f'<{tag}{attr_str}>{text}</{tag}>')
            html_parts.append('</div>')
        
        # Build target element
        target = match.element
        tag = target.get('tag', 'div')
        text = target.get('text', '')
        attrs = target.get('attributes', {})
        attr_str = self._build_attribute_string(attrs)
        
        html_parts.append(f'<{tag}{attr_str}>{text}</{tag}>')
        
        # Close parent tags
        for parent in parents:
            tag = parent.get('tag', 'div')
            html_parts.append(f'</{tag}>')
        
        return ''.join(html_parts)
    
    def _build_semantic_structure(self, match: ExactMatch, parents: List[Dict[str, Any]], siblings: List[Dict[str, Any]]) -> str:
        """Build semantic structure description."""
        structure_parts = []
        
        # Add parent context
        for parent in parents:
            tag = parent.get('tag', 'div')
            role = parent.get('attributes', {}).get('role', '')
            if role:
                structure_parts.append(f"{tag}[role={role}]")
            else:
                structure_parts.append(tag)
        
        # Add target element
        target = match.element
        tag = target.get('tag', 'div')
        match_type = match.match_type
        structure_parts.append(f"{tag}({match_type})")
        
        return " > ".join(structure_parts)
    
    def _build_attribute_string(self, attrs: Dict[str, Any]) -> str:
        """Build attribute string for HTML."""
        attr_parts = []
        
        # Include important attributes
        important_attrs = ['class', 'id', 'role', 'type', 'name', 'aria-label']
        
        for attr in important_attrs:
            value = attrs.get(attr, '')
            if value:
                attr_parts.append(f'{attr}="{value}"')
        
        return ' ' + ' '.join(attr_parts) if attr_parts else ''
    
    def _matches_hierarchy_level(self, element: Dict[str, Any], level: str) -> bool:
        """Check if element matches hierarchy level."""
        # This would match element to hierarchy level
        # For now, return True as placeholder
        return True
    
    def _get_cache_key(self, match: ExactMatch, all_elements: List[Dict[str, Any]]) -> str:
        """Generate cache key for context."""
        element_id = match.element.get('attributes', {}).get('id', '')
        hierarchy = match.element.get('hierarchy', [])
        return f"{element_id}:{':'.join(hierarchy)}"