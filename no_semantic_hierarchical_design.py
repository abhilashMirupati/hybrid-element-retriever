"""
No-Semantic Mode with Hierarchical Context Design

Approach:
1. Find all nodes matching target text (innerText, attributes, accessibility)
2. Build parent/sibling hierarchy for ONLY matching nodes
3. Pass hierarchical context to MarkupLM for ranking
4. No structure/info loss - just better context
"""

from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
import re

@dataclass
class MatchingNode:
    """A node that matches the target text."""
    element: Dict[str, Any]
    match_type: str  # 'innerText', 'attribute', 'accessibility'
    match_confidence: float
    xpath: str

@dataclass
class HierarchicalContext:
    """Hierarchical context for a matching node."""
    target_element: MatchingNode
    parent_elements: List[Dict[str, Any]]
    sibling_elements: List[Dict[str, Any]]
    html_context: str
    depth: int

class NoSemanticHierarchicalMatcher:
    """No-semantic matcher with hierarchical context for MarkupLM."""
    
    def __init__(self):
        self.intent_parser = IntentParser()
    
    def find_matching_nodes(self, elements: List[Dict[str, Any]], target_text: str, intent: str) -> List[MatchingNode]:
        """Find all nodes that match target text in various ways."""
        matches = []
        
        for element in elements:
            # 1. InnerText matching
            if self._matches_inner_text(element, target_text):
                matches.append(MatchingNode(
                    element=element,
                    match_type='innerText',
                    match_confidence=1.0,
                    xpath=self._generate_xpath(element)
                ))
            
            # 2. Attribute matching
            attr_match = self._matches_attributes(element, target_text)
            if attr_match:
                matches.append(MatchingNode(
                    element=element,
                    match_type='attribute',
                    match_confidence=attr_match['confidence'],
                    xpath=self._generate_xpath(element)
                ))
            
            # 3. Accessibility matching
            ax_match = self._matches_accessibility(element, target_text)
            if ax_match:
                matches.append(MatchingNode(
                    element=element,
                    match_type='accessibility',
                    match_confidence=ax_match['confidence'],
                    xpath=self._generate_xpath(element)
                ))
        
        return matches
    
    def build_hierarchical_context(self, matches: List[MatchingNode], all_elements: List[Dict[str, Any]]) -> List[HierarchicalContext]:
        """Build hierarchical context for each matching node."""
        contexts = []
        
        for match in matches:
            # Find parent elements
            parents = self._find_parent_elements(match.element, all_elements)
            
            # Find sibling elements
            siblings = self._find_sibling_elements(match.element, all_elements)
            
            # Build HTML context
            html_context = self._build_html_context(match, parents, siblings)
            
            context = HierarchicalContext(
                target_element=match,
                parent_elements=parents,
                sibling_elements=siblings,
                html_context=html_context,
                depth=len(parents)
            )
            contexts.append(context)
        
        return contexts
    
    def rank_with_markup(self, contexts: List[HierarchicalContext], query: str, intent: str) -> List[Tuple[HierarchicalContext, float]]:
        """Rank hierarchical contexts using MarkupLM."""
        ranked_contexts = []
        
        for context in contexts:
            # Use MarkupLM to score the hierarchical HTML context
            markup_score = self._score_with_markup(context.html_context, query)
            
            # Apply intent-specific bonuses
            intent_bonus = self._apply_intent_bonus(context, intent)
            
            # Combine scores
            final_score = markup_score + intent_bonus
            
            ranked_contexts.append((context, final_score))
        
        # Sort by score
        ranked_contexts.sort(key=lambda x: x[1], reverse=True)
        return ranked_contexts
    
    def _matches_inner_text(self, element: Dict[str, Any], target_text: str) -> bool:
        """Check if element's innerText matches target."""
        text = element.get('text', '').strip()
        return target_text.lower() in text.lower()
    
    def _matches_attributes(self, element: Dict[str, Any], target_text: str) -> Optional[Dict[str, Any]]:
        """Check if element's attributes match target."""
        attrs = element.get('attributes', {})
        
        # Check various attributes
        attr_fields = ['id', 'class', 'aria-label', 'title', 'placeholder', 'name', 'data-testid', 'value']
        
        for field in attr_fields:
            value = attrs.get(field, '')
            if target_text.lower() in value.lower():
                return {
                    'field': field,
                    'confidence': 0.9 if field in ['id', 'data-testid'] else 0.7
                }
        
        return None
    
    def _matches_accessibility(self, element: Dict[str, Any], target_text: str) -> Optional[Dict[str, Any]]:
        """Check if element's accessibility attributes match target."""
        # This would integrate with accessibility tree
        # For now, check role and aria attributes
        attrs = element.get('attributes', {})
        role = attrs.get('role', '')
        
        if role and target_text.lower() in role.lower():
            return {'confidence': 0.8}
        
        return None
    
    def _find_parent_elements(self, element: Dict[str, Any], all_elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find parent elements for hierarchical context."""
        parents = []
        
        # Use element's hierarchy path if available
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
        
        # Find elements at same hierarchy level
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
    
    def _build_html_context(self, match: MatchingNode, parents: List[Dict[str, Any]], siblings: List[Dict[str, Any]]) -> str:
        """Build hierarchical HTML context for MarkupLM."""
        html_parts = []
        
        # Build parent context
        for parent in parents:
            tag = parent.get('tag', 'div')
            attrs = parent.get('attributes', {})
            class_attr = attrs.get('class', '')
            id_attr = attrs.get('id', '')
            
            attr_str = ""
            if class_attr:
                attr_str += f' class="{class_attr}"'
            if id_attr:
                attr_str += f' id="{id_attr}"'
            
            html_parts.append(f'<{tag}{attr_str}>')
        
        # Build sibling context
        if siblings:
            html_parts.append('<div class="sibling-context">')
            for sibling in siblings[:3]:  # Limit to 3 siblings
                tag = sibling.get('tag', 'span')
                text = sibling.get('text', '')[:50]  # Truncate long text
                html_parts.append(f'<{tag}>{text}</{tag}>')
            html_parts.append('</div>')
        
        # Build target element
        target = match.element
        tag = target.get('tag', 'div')
        attrs = target.get('attributes', {})
        text = target.get('text', '')
        
        attr_str = ""
        for key, value in attrs.items():
            if value:
                attr_str += f' {key}="{value}"'
        
        html_parts.append(f'<{tag}{attr_str}>{text}</{tag}>')
        
        # Close parent tags
        for parent in parents:
            tag = parent.get('tag', 'div')
            html_parts.append(f'</{tag}>')
        
        return ''.join(html_parts)
    
    def _score_with_markup(self, html_context: str, query: str) -> float:
        """Score HTML context using MarkupLM."""
        # This would integrate with actual MarkupLM
        # For now, return a placeholder score
        return 0.8
    
    def _apply_intent_bonus(self, context: HierarchicalContext, intent: str) -> float:
        """Apply intent-specific bonuses to context score."""
        bonus = 0.0
        
        target = context.target_element.element
        tag = target.get('tag', '').lower()
        
        if intent == 'click':
            if tag in ['a', 'button']:
                bonus += 0.2
            elif target.get('interactive', False):
                bonus += 0.1
        
        elif intent == 'enter':
            if tag in ['input', 'textarea']:
                bonus += 0.2
        
        elif intent == 'select':
            if tag in ['select', 'option']:
                bonus += 0.2
        
        return bonus
    
    def _generate_xpath(self, element: Dict[str, Any]) -> str:
        """Generate XPath for element."""
        # This would use the existing XPath generation logic
        return f"//{element.get('tag', 'div')}[contains(text(), '{element.get('text', '')[:20]}')]"
    
    def _matches_hierarchy_level(self, element: Dict[str, Any], level: str) -> bool:
        """Check if element matches hierarchy level."""
        # This would match element to hierarchy level
        return True  # Placeholder

# Usage Example
def no_semantic_query_with_hierarchy(query: str, elements: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Main query function using hierarchical no-semantic approach."""
    
    # 1. Parse intent
    intent_parser = IntentParser()
    parsed_intent = intent_parser.parse_step(query)
    
    # 2. Find matching nodes
    matcher = NoSemanticHierarchicalMatcher()
    matches = matcher.find_matching_nodes(elements, parsed_intent.target_text, parsed_intent.intent.value)
    
    if not matches:
        return {'xpath': None, 'element': None, 'confidence': 0.0}
    
    # 3. Build hierarchical context
    contexts = matcher.build_hierarchical_context(matches, elements)
    
    # 4. Rank with MarkupLM
    ranked_contexts = matcher.rank_with_markup(contexts, query, parsed_intent.intent.value)
    
    # 5. Return best match
    if ranked_contexts:
        best_context, score = ranked_contexts[0]
        return {
            'xpath': best_context.target_element.xpath,
            'element': best_context.target_element.element,
            'confidence': score,
            'html_context': best_context.html_context,
            'strategy': 'no-semantic-hierarchical'
        }
    
    return {'xpath': None, 'element': None, 'confidence': 0.0}