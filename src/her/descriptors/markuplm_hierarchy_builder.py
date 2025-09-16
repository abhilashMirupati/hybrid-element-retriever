"""
MarkupLM Hierarchical Context Builder for HER framework.

This module builds hierarchical context for HTML elements to enhance
MarkupLM-based snippet scoring in no-semantic mode.
"""

from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

log = logging.getLogger("her.markuplm_hierarchy_builder")


@dataclass
class HierarchicalContext:
    """Hierarchical context for an element."""
    element: Dict[str, Any]
    parents: List[Dict[str, Any]]
    siblings: List[Dict[str, Any]]
    children: List[Dict[str, Any]]
    depth: int
    hierarchy_path: List[str]
    html_context: str


class MarkupLMHierarchyBuilder:
    """Builder for hierarchical context to enhance MarkupLM scoring."""
    
    def __init__(self, max_depth: int = 5, max_siblings: int = 5):
        """Initialize hierarchy builder.
        
        Args:
            max_depth: Maximum depth to traverse up the hierarchy
            max_siblings: Maximum number of siblings to include
        """
        self.max_depth = max_depth
        self.max_siblings = max_siblings
        
        log.info(f"MarkupLM Hierarchy Builder initialized (max_depth={max_depth}, max_siblings={max_siblings})")
    
    def build_context_for_candidates(self, candidates: List[Dict[str, Any]], 
                                   all_elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Build hierarchical context for candidate elements.
        
        Args:
            candidates: List of candidate elements
            all_elements: All available elements for context building
            
        Returns:
            List of candidates with hierarchical context
        """
        if not candidates or not all_elements:
            return candidates
        
        log.info(f"Building hierarchical context for {len(candidates)} candidates")
        
        enhanced_candidates = []
        
        for candidate in candidates:
            try:
                # Build hierarchical context
                context = self._build_element_context(candidate, all_elements)
                
                # Create enhanced candidate with context
                enhanced_candidate = {
                    'element': candidate,
                    'parents': context.parents,
                    'siblings': context.siblings,
                    'children': context.children,
                    'depth': context.depth,
                    'hierarchy_path': context.hierarchy_path,
                    'html_context': context.html_context,
                    'original_candidate': candidate
                }
                
                enhanced_candidates.append(enhanced_candidate)
                
            except Exception as e:
                log.warning(f"Failed to build context for candidate: {e}")
                # Add candidate without context
                enhanced_candidates.append({
                    'element': candidate,
                    'parents': [],
                    'siblings': [],
                    'children': [],
                    'depth': 0,
                    'hierarchy_path': [],
                    'html_context': self._build_basic_html(candidate),
                    'original_candidate': candidate
                })
        
        log.info(f"Enhanced {len(enhanced_candidates)} candidates with hierarchical context")
        
        return enhanced_candidates
    
    def _build_element_context(self, element: Dict[str, Any], 
                              all_elements: List[Dict[str, Any]]) -> HierarchicalContext:
        """Build hierarchical context for a single element.
        
        Args:
            element: Target element
            all_elements: All available elements
            
        Returns:
            HierarchicalContext object
        """
        # Find parents
        parents = self._find_parent_elements(element, all_elements)
        
        # Find siblings
        siblings = self._find_sibling_elements(element, all_elements, parents)
        
        # Find children
        children = self._find_child_elements(element, all_elements)
        
        # Calculate depth
        depth = len(parents)
        
        # Build hierarchy path
        hierarchy_path = self._build_hierarchy_path(element, parents)
        
        # Build HTML context
        html_context = self._build_html_context(element, parents, siblings, children)
        
        return HierarchicalContext(
            element=element,
            parents=parents,
            siblings=siblings,
            children=children,
            depth=depth,
            hierarchy_path=hierarchy_path,
            html_context=html_context
        )
    
    def _find_parent_elements(self, element: Dict[str, Any], 
                             all_elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find parent elements for the given element.
        
        Args:
            element: Target element
            all_elements: All available elements
            
        Returns:
            List of parent elements (closest to furthest)
        """
        parents = []
        
        # Try to find parents using xpath hierarchy
        element_xpath = element.get('xpath', '')
        if not element_xpath:
            return parents
        
        # Extract parent xpaths by removing the last part
        xpath_parts = element_xpath.split('/')
        if len(xpath_parts) <= 2:  # No parents if xpath is too short
            return parents
        
        # Build parent xpaths
        for i in range(1, len(xpath_parts) - 1):
            parent_xpath = '/'.join(xpath_parts[:len(xpath_parts) - i])
            if parent_xpath.startswith('//'):
                parent_xpath = parent_xpath[2:]  # Remove leading //
            
            # Find element with matching xpath
            for elem in all_elements:
                if elem == element:
                    continue
                
                elem_xpath = elem.get('xpath', '')
                if elem_xpath and parent_xpath in elem_xpath:
                    parents.append(elem)
                    break
            
            # Limit depth
            if len(parents) >= self.max_depth:
                break
        
        return parents
    
    def _find_sibling_elements(self, element: Dict[str, Any], 
                              all_elements: List[Dict[str, Any]], 
                              parents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find sibling elements for the given element.
        
        Args:
            element: Target element
            all_elements: All available elements
            parents: Parent elements
            
        Returns:
            List of sibling elements
        """
        siblings = []
        
        if not parents:
            return siblings
        
        # Find elements with same parent
        parent_xpath = parents[0].get('xpath', '') if parents else ''
        if not parent_xpath:
            return siblings
        
        # Find siblings by matching parent xpath
        for elem in all_elements:
            if elem == element:
                continue
            
            elem_xpath = elem.get('xpath', '')
            if elem_xpath and parent_xpath in elem_xpath:
                # Check if it's a direct sibling (one level difference)
                elem_depth = elem_xpath.count('/')
                element_depth = element.get('xpath', '').count('/')
                
                if elem_depth == element_depth:
                    siblings.append(elem)
                    
                    # Limit number of siblings
                    if len(siblings) >= self.max_siblings:
                        break
        
        return siblings
    
    def _find_child_elements(self, element: Dict[str, Any], 
                            all_elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find child elements for the given element.
        
        Args:
            element: Target element
            all_elements: All available elements
            
        Returns:
            List of child elements
        """
        children = []
        
        element_xpath = element.get('xpath', '')
        if not element_xpath:
            return children
        
        # Find elements that have this element as parent
        for elem in all_elements:
            if elem == element:
                continue
            
            elem_xpath = elem.get('xpath', '')
            if elem_xpath and element_xpath in elem_xpath:
                # Check if it's a direct child (one level deeper)
                elem_depth = elem_xpath.count('/')
                element_depth = element_xpath.count('/')
                
                if elem_depth == element_depth + 1:
                    children.append(elem)
                    
                    # Limit number of children
                    if len(children) >= self.max_siblings:
                        break
        
        return children
    
    def _build_hierarchy_path(self, element: Dict[str, Any], 
                             parents: List[Dict[str, Any]]) -> List[str]:
        """Build hierarchy path for the element.
        
        Args:
            element: Target element
            parents: Parent elements
            
        Returns:
            List of hierarchy path strings
        """
        path = []
        
        # Add parent tags to path
        for parent in reversed(parents):  # Reverse to get root-to-leaf order
            tag = parent.get('tag', 'div')
            attrs = parent.get('attributes', {})
            
            # Add role if available
            role = attrs.get('role', '')
            if role:
                path.append(f"{tag}[role={role}]")
            else:
                path.append(tag)
        
        # Add target element
        tag = element.get('tag', 'div')
        attrs = element.get('attributes', {})
        role = attrs.get('role', '')
        
        if role:
            path.append(f"{tag}[role={role}]")
        else:
            path.append(tag)
        
        return path
    
    def _build_html_context(self, element: Dict[str, Any], 
                           parents: List[Dict[str, Any]], 
                           siblings: List[Dict[str, Any]], 
                           children: List[Dict[str, Any]]) -> str:
        """Build HTML context for the element.
        
        Args:
            element: Target element
            parents: Parent elements
            siblings: Sibling elements
            children: Child elements
            
        Returns:
            HTML context string
        """
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
            for sibling in siblings:
                tag = sibling.get('tag', 'span')
                text = sibling.get('text', '')[:50]  # Truncate long text
                attrs = sibling.get('attributes', {})
                attr_str = self._build_attribute_string(attrs)
                html_parts.append(f'<{tag}{attr_str}>{text}</{tag}>')
            html_parts.append('</div>')
        
        # Build target element
        tag = element.get('tag', 'div')
        text = element.get('text', '')
        attrs = element.get('attributes', {})
        attr_str = self._build_attribute_string(attrs)
        
        # Include children if any
        if children:
            html_parts.append(f'<{tag}{attr_str}>')
            for child in children[:3]:  # Limit to 3 children
                child_tag = child.get('tag', 'span')
                child_text = child.get('text', '')[:30]  # Truncate
                child_attrs = child.get('attributes', {})
                child_attr_str = self._build_attribute_string(child_attrs)
                html_parts.append(f'<{child_tag}{child_attr_str}>{child_text}</{child_tag}>')
            html_parts.append(f'{text}</{tag}>')
        else:
            html_parts.append(f'<{tag}{attr_str}>{text}</{tag}>')
        
        # Close parent tags
        for parent in parents:
            tag = parent.get('tag', 'div')
            html_parts.append(f'</{tag}>')
        
        return ''.join(html_parts)
    
    def _build_basic_html(self, element: Dict[str, Any]) -> str:
        """Build basic HTML for element without context.
        
        Args:
            element: Target element
            
        Returns:
            Basic HTML string
        """
        tag = element.get('tag', 'div')
        text = element.get('text', '')
        attrs = element.get('attributes', {})
        attr_str = self._build_attribute_string(attrs)
        
        return f'<{tag}{attr_str}>{text}</{tag}>'
    
    def _build_attribute_string(self, attrs: Dict[str, Any]) -> str:
        """Build attribute string for HTML.
        
        Args:
            attrs: Element attributes
            
        Returns:
            Attribute string
        """
        if not attrs:
            return ""
        
        attr_parts = []
        
        # Include important attributes
        important_attrs = ['class', 'id', 'role', 'type', 'name', 'aria-label', 'data-testid']
        
        for attr in important_attrs:
            value = attrs.get(attr, '')
            if value:
                # Escape quotes in attribute values
                escaped_value = str(value).replace('"', '&quot;')
                attr_parts.append(f'{attr}="{escaped_value}"')
        
        return ' ' + ' '.join(attr_parts) if attr_parts else ''
    
    def get_context_summary(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """Get summary of hierarchical context for a candidate.
        
        Args:
            candidate: Candidate with hierarchical context
            
        Returns:
            Context summary dictionary
        """
        return {
            'has_parents': len(candidate.get('parents', [])) > 0,
            'parent_count': len(candidate.get('parents', [])),
            'has_siblings': len(candidate.get('siblings', [])) > 0,
            'sibling_count': len(candidate.get('siblings', [])),
            'has_children': len(candidate.get('children', [])) > 0,
            'child_count': len(candidate.get('children', [])),
            'depth': candidate.get('depth', 0),
            'hierarchy_path': candidate.get('hierarchy_path', []),
            'html_length': len(candidate.get('html_context', ''))
        }