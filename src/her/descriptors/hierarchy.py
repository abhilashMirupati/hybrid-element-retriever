"""
Hierarchical context builder for element descriptors.

This module provides functionality to build HTML hierarchy context
for element descriptors, including parent-child relationships,
sibling information, and hierarchy paths.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class HierarchyContextBuilder:
    """Builds hierarchical context for element descriptors."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def build_hierarchy_context(self, dom_tree: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Build hierarchical context for all elements in the DOM tree.
        
        Args:
            dom_tree: List of DOM node dictionaries
            
        Returns:
            List of elements with added hierarchical context
        """
        # Build node index for quick lookup
        node_index = self._build_node_index(dom_tree)
        
        # Build parent-child relationships
        parent_child_map = self._build_parent_child_map(dom_tree, node_index)
        
        # Add context to each element
        enhanced_elements = []
        for element in dom_tree:
            context = self._build_element_context(element, node_index, parent_child_map)
            # Preserve all existing fields, especially meta
            enhanced_element = element.copy()
            enhanced_element['context'] = context
            enhanced_elements.append(enhanced_element)
        
        self.logger.debug(f"Built hierarchy context for {len(enhanced_elements)} elements")
        return enhanced_elements
    
    def _build_node_index(self, dom_tree: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Build index of nodes by backendNodeId for quick lookup."""
        node_index = {}
        for node in dom_tree:
            backend_id = node.get('backendNodeId')
            if backend_id is not None:
                node_index[str(backend_id)] = node
        return node_index
    
    def _build_parent_child_map(self, dom_tree: List[Dict[str, Any]], node_index: Dict[str, Dict[str, Any]]) -> Dict[str, List[str]]:
        """Build parent-child relationship mapping."""
        parent_child_map = {}
        
        for node in dom_tree:
            parent_id = node.get('parentId')
            backend_id = node.get('backendNodeId')
            
            if parent_id is not None and backend_id is not None:
                parent_id_str = str(parent_id)
                backend_id_str = str(backend_id)
                
                if parent_id_str not in parent_child_map:
                    parent_child_map[parent_id_str] = []
                parent_child_map[parent_id_str].append(backend_id_str)
        
        return parent_child_map
    
    def _build_element_context(self, element: Dict[str, Any], node_index: Dict[str, Dict[str, Any]], parent_child_map: Dict[str, List[str]]) -> Dict[str, Any]:
        """Build hierarchical context for a single element."""
        backend_id = element.get('backendNodeId')
        if backend_id is None:
            return self._empty_context()
        
        backend_id_str = str(backend_id)
        
        # Get parent information
        parent_info = self._get_parent_info(element, node_index)
        
        # Get sibling information
        siblings_info = self._get_siblings_info(element, node_index, parent_child_map)
        
        # Get ancestors information
        ancestors_info = self._get_ancestors_info(element, node_index)
        
        # Build hierarchy path
        hierarchy_path = self._build_hierarchy_path(element, ancestors_info)
        
        return {
            'parent': parent_info,
            'siblings': siblings_info,
            'ancestors': ancestors_info,
            'hierarchy_path': hierarchy_path,
            'depth': len(ancestors_info),
            'has_children': backend_id_str in parent_child_map,
            'children_count': len(parent_child_map.get(backend_id_str, []))
        }
    
    def _get_parent_info(self, element: Dict[str, Any], node_index: Dict[str, Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Get parent element information."""
        parent_id = element.get('parentId')
        if parent_id is None:
            return None
        
        parent_node = node_index.get(str(parent_id))
        if parent_node is None:
            return None
        
        return {
            'tag': parent_node.get('tagName', parent_node.get('tag', '')),
            'id': parent_node.get('id', ''),
            'class': parent_node.get('className', ''),
            'role': parent_node.get('role', ''),
            'backendNodeId': parent_id
        }
    
    def _get_siblings_info(self, element: Dict[str, Any], node_index: Dict[str, Dict[str, Any]], parent_child_map: Dict[str, List[str]]) -> List[Dict[str, Any]]:
        """Get sibling elements information."""
        parent_id = element.get('parentId')
        if parent_id is None:
            return []
        
        siblings = parent_child_map.get(str(parent_id), [])
        siblings_info = []
        
        for sibling_id in siblings:
            if sibling_id == str(element.get('backendNodeId')):
                continue  # Skip self
            
            sibling_node = node_index.get(sibling_id)
            if sibling_node:
                siblings_info.append({
                    'tag': sibling_node.get('tagName', sibling_node.get('tag', '')),
                    'id': sibling_node.get('id', ''),
                    'class': sibling_node.get('className', ''),
                    'role': sibling_node.get('role', ''),
                    'backendNodeId': sibling_id
                })
        
        return siblings_info
    
    def _get_ancestors_info(self, element: Dict[str, Any], node_index: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get ancestor elements information (up to root)."""
        ancestors = []
        current_id = element.get('parentId')
        max_depth = 10  # Prevent infinite loops
        
        while current_id is not None and len(ancestors) < max_depth:
            ancestor_node = node_index.get(str(current_id))
            if ancestor_node is None:
                break
            
            ancestors.append({
                'tag': ancestor_node.get('tagName', ancestor_node.get('tag', '')),
                'id': ancestor_node.get('id', ''),
                'class': ancestor_node.get('className', ''),
                'role': ancestor_node.get('role', ''),
                'backendNodeId': current_id
            })
            
            current_id = ancestor_node.get('parentId')
        
        return ancestors
    
    def _build_hierarchy_path(self, element: Dict[str, Any], ancestors_info: List[Dict[str, Any]]) -> str:
        """Build human-readable hierarchy path."""
        path_parts = []
        
        # Add ancestors (from root to parent)
        for ancestor in reversed(ancestors_info):
            tag = ancestor.get('tag', '').upper()
            element_id = ancestor.get('id', '')
            element_class = ancestor.get('class', '')
            
            if element_id:
                path_parts.append(f"{tag}#{element_id}")
            elif element_class:
                # Take first class for brevity
                first_class = element_class.split()[0] if element_class else ''
                path_parts.append(f"{tag}.{first_class}")
            else:
                path_parts.append(tag)
        
        # Add current element
        current_tag = element.get('tagName', element.get('tag', '')).upper()
        current_id = element.get('id', '')
        current_class = element.get('className', '')
        
        if current_id:
            path_parts.append(f"{current_tag}#{current_id}")
        elif current_class:
            first_class = current_class.split()[0] if current_class else ''
            path_parts.append(f"{current_tag}.{first_class}")
        else:
            path_parts.append(current_tag)
        
        return " > ".join(path_parts)
    
    def _empty_context(self) -> Dict[str, Any]:
        """Return empty context for elements without hierarchy info."""
        return {
            'parent': None,
            'siblings': [],
            'ancestors': [],
            'hierarchy_path': 'UNKNOWN',
            'depth': 0,
            'has_children': False,
            'children_count': 0
        }
    
    def add_context_to_elements(self, elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Add hierarchical context to a list of elements.
        
        Args:
            elements: List of element descriptors
            
        Returns:
            List of elements with added context
        """
        if not elements:
            return elements
        
        return self.build_hierarchy_context(elements)