"""
Enhanced No-Semantic Mode Implementation

Features:
1. True no-semantic mode (no ML models)
2. Hierarchical context building for MarkupLM ranking
3. Proper navigation handling
4. XPath validation during selection
5. Intent parsing integration
6. Search target handling
"""

from __future__ import annotations

import re
import time
import logging
from typing import List, Dict, Any, Tuple, Optional, Union
from dataclasses import dataclass
from enum import Enum

from .intent_parser import IntentParser, ParsedIntent, IntentType
from .core_no_semantic import CoreNoSemanticMatcher, ExactMatch
from .hierarchical_context import HierarchicalContextBuilder, HierarchicalContext
from .navigation_handler import NavigationHandler
from .xpath_validator import XPathValidator, XPathCandidate
from .intent_integration import IntentIntegration, IntentScoredMatch
from .critical_fixes import CriticalFixes
from .search_target_handler import SearchTargetHandler, SearchTarget

log = logging.getLogger("her.enhanced_no_semantic")

@dataclass
class MatchingNode:
    """A node that matches the target text."""
    element: Dict[str, Any]
    match_type: str  # 'innerText', 'attribute', 'accessibility', 'search_input'
    match_confidence: float
    xpath: str
    hierarchy_path: List[str]

@dataclass
class HierarchicalContext:
    """Hierarchical context for a matching node."""
    target_element: MatchingNode
    parent_elements: List[Dict[str, Any]]
    sibling_elements: List[Dict[str, Any]]
    html_context: str
    depth: int
    semantic_structure: str

# XPathCandidate is imported from xpath_validator

class EnhancedNoSemanticMatcher:
    """Enhanced no-semantic matcher with hierarchical context."""
    
    def __init__(self):
        self.intent_parser = IntentParser()
        self.core_matcher = CoreNoSemanticMatcher()
        self.context_builder = HierarchicalContextBuilder()
        self.navigation_handler = NavigationHandler()
        self.xpath_validator = XPathValidator()
        self.intent_integration = IntentIntegration()
        self.critical_fixes = CriticalFixes()
        self.search_target_handler = SearchTargetHandler()
        self.markup_ranker = None  # Will be set if MarkupLM is available
    
    def query(self, query: str, elements: List[Dict[str, Any]], page=None) -> Dict[str, Any]:
        """Main query method for enhanced no-semantic mode."""
        start_time = time.time()
        
        try:
            # Step 1: Parse intent
            parsed_intent = self.intent_parser.parse_step(query)
            log.info(f"Parsed intent: {parsed_intent.intent.value}, target: '{parsed_intent.target_text}', value: '{parsed_intent.value}'")
            
            # Step 2: Apply critical fixes
            elements = self.critical_fixes.apply_all_fixes(elements, parsed_intent)
            
            # Step 3: Handle navigation queries
            if self.navigation_handler.is_navigation_query(parsed_intent):
                nav_result = self.navigation_handler.handle_navigation(parsed_intent, page)
                return self.navigation_handler.create_navigation_result(nav_result)
            
            # Step 4: Handle search targets
            search_target = self.search_target_handler.extract_search_target(parsed_intent)
            if search_target:
                search_inputs = self.search_target_handler.find_search_inputs(elements, search_target)
                if search_inputs:
                    # Use search inputs as primary elements
                    elements = [self.search_target_handler.enhance_search_input(elem, search_target) for elem in search_inputs]
            
            # Step 5: Find exact matches using core matcher
            exact_matches = self.core_matcher.find_exact_matches(elements, parsed_intent)
            log.info(f"Found {len(exact_matches)} exact matches")
            
            if not exact_matches:
                return self._create_no_match_result(query, start_time)
            
            # Step 6: Apply intent-specific heuristics
            heuristically_scored_matches = self.core_matcher.apply_intent_heuristics(exact_matches, parsed_intent)
            
            # Step 7: Apply intent integration scoring
            intent_scored_matches = self.intent_integration.apply_intent_scoring(heuristically_scored_matches, parsed_intent)
            
            # Step 8: Build hierarchical context for top matches
            top_matches = intent_scored_matches[:5]  # Limit to top 5 for performance
            contexts = self.context_builder.build_contexts([m.match for m in top_matches], elements)
            log.info(f"Built hierarchical context for {len(contexts)} matches")
            
            # Step 9: Generate and validate XPath candidates
            xpath_candidates = self.xpath_validator.generate_candidates(contexts)
            validated_candidates = self.xpath_validator.validate_candidates(xpath_candidates, page)
            log.info(f"Validated {len([c for c in validated_candidates if c.is_valid])} valid XPath candidates")
            
            # Step 10: Select best candidate
            best_candidate = self.xpath_validator.select_best_candidate(validated_candidates)
            
            if best_candidate:
                return self._create_success_result(best_candidate, query, start_time)
            else:
                return self._create_no_valid_result(query, start_time)
                
        except Exception as e:
            log.error(f"Enhanced no-semantic query failed: {e}")
            return self._create_error_result(query, str(e), start_time)
    
    def _is_navigation_query(self, parsed_intent: ParsedIntent) -> bool:
        """Check if query is a navigation request."""
        navigation_keywords = ['navigate', 'go to', 'visit', 'open', 'load']
        query_lower = parsed_intent.original_step.lower()
        
        for keyword in navigation_keywords:
            if keyword in query_lower:
                return True
        
        # Check if target text looks like a URL
        target = parsed_intent.target_text
        if target and ('http' in target or 'www.' in target or target.endswith('.com')):
            return True
        
        return False
    
    def _handle_navigation(self, parsed_intent: ParsedIntent, page) -> Dict[str, Any]:
        """Handle navigation queries using page.goto()."""
        if not page:
            return {
                'xpath': None,
                'element': None,
                'confidence': 0.0,
                'strategy': 'navigation-failed',
                'error': 'No page object available for navigation'
            }
        
        # Extract URL from target text or original step
        url = self._extract_url(parsed_intent)
        if not url:
            return {
                'xpath': None,
                'element': None,
                'confidence': 0.0,
                'strategy': 'navigation-failed',
                'error': 'Could not extract URL from query'
            }
        
        try:
            # Use page.goto() for navigation
            response = page.goto(url, wait_until='domcontentloaded', timeout=30000)
            
            if response and response.status < 400:
                return {
                    'xpath': None,
                    'element': None,
                    'confidence': 1.0,
                    'strategy': 'navigation-success',
                    'url': url,
                    'status': response.status
                }
            else:
                return {
                    'xpath': None,
                    'element': None,
                    'confidence': 0.0,
                    'strategy': 'navigation-failed',
                    'error': f'Navigation failed with status: {response.status if response else "No response"}'
                }
        except Exception as e:
            return {
                'xpath': None,
                'element': None,
                'confidence': 0.0,
                'strategy': 'navigation-failed',
                'error': f'Navigation error: {str(e)}'
            }
    
    def _extract_url(self, parsed_intent: ParsedIntent) -> Optional[str]:
        """Extract URL from parsed intent."""
        # Try target text first
        target = parsed_intent.target_text
        if target and ('http' in target or 'www.' in target):
            if not target.startswith('http'):
                target = 'https://' + target
            return target
        
        # Try original step
        step = parsed_intent.original_step
        url_pattern = r'https?://[^\s"\']+|www\.[^\s"\']+'
        match = re.search(url_pattern, step)
        if match:
            url = match.group(0)
            if not url.startswith('http'):
                url = 'https://' + url
            return url
        
        # Try to construct URL from target text (e.g., "Verizon" -> "https://verizon.com")
        if target:
            # Simple domain mapping
            domain_mapping = {
                'verizon': 'https://verizon.com',
                'google': 'https://google.com',
                'amazon': 'https://amazon.com',
                'facebook': 'https://facebook.com',
                'twitter': 'https://twitter.com',
                'linkedin': 'https://linkedin.com',
                'github': 'https://github.com',
                'stackoverflow': 'https://stackoverflow.com'
            }
            
            target_lower = target.lower()
            if target_lower in domain_mapping:
                return domain_mapping[target_lower]
            
            # Try to construct URL from target
            if target_lower.replace(' ', '').isalnum():
                return f'https://{target_lower.replace(" ", "").lower()}.com'
        
        return None
    
    def _find_matching_nodes(self, elements: List[Dict[str, Any]], parsed_intent: ParsedIntent) -> List[MatchingNode]:
        """Find all nodes that match target text using exact matching."""
        matches = []
        target_text = parsed_intent.target_text
        intent = parsed_intent.intent.value
        
        for element in elements:
            # 1. InnerText matching
            if self._matches_inner_text(element, target_text):
                matches.append(MatchingNode(
                    element=element,
                    match_type='innerText',
                    match_confidence=1.0,
                    xpath=self._generate_xpath(element),
                    hierarchy_path=element.get('hierarchy', [])
                ))
            
            # 2. Attribute matching
            attr_match = self._matches_attributes(element, target_text)
            if attr_match:
                matches.append(MatchingNode(
                    element=element,
                    match_type='attribute',
                    match_confidence=attr_match['confidence'],
                    xpath=self._generate_xpath(element),
                    hierarchy_path=element.get('hierarchy', [])
                ))
            
            # 3. Accessibility matching
            ax_match = self._matches_accessibility(element, target_text)
            if ax_match:
                matches.append(MatchingNode(
                    element=element,
                    match_type='accessibility',
                    match_confidence=ax_match['confidence'],
                    xpath=self._generate_xpath(element),
                    hierarchy_path=element.get('hierarchy', [])
                ))
            
            # 4. Search input matching (for search/enter intents)
            if intent in ['search', 'enter', 'type']:
                search_match = self._matches_search_input(element, target_text, parsed_intent.value)
                if search_match:
                    matches.append(MatchingNode(
                        element=element,
                        match_type='search_input',
                        match_confidence=search_match['confidence'],
                        xpath=self._generate_xpath(element),
                        hierarchy_path=element.get('hierarchy', [])
                    ))
        
        return matches
    
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
            if value and target_text.lower() in value.lower():
                confidence = 0.9 if field in ['id', 'data-testid'] else 0.7
                return {'field': field, 'confidence': confidence}
        
        return None
    
    def _matches_accessibility(self, element: Dict[str, Any], target_text: str) -> Optional[Dict[str, Any]]:
        """Check if element's accessibility attributes match target."""
        attrs = element.get('attributes', {})
        role = attrs.get('role', '')
        
        if role and target_text.lower() in role.lower():
            return {'confidence': 0.8}
        
        return None
    
    def _matches_search_input(self, element: Dict[str, Any], target_text: str, value: Optional[str]) -> Optional[Dict[str, Any]]:
        """Check if element is a search input that matches target."""
        tag = element.get('tag', '').lower()
        attrs = element.get('attributes', {})
        
        # Check if it's an input field
        if tag != 'input':
            return None
        
        input_type = attrs.get('type', '').lower()
        
        # Check if it's a search-related input
        search_indicators = ['search', 'query', 'find', 'look']
        
        # Check placeholder
        placeholder = attrs.get('placeholder', '').lower()
        if any(indicator in placeholder for indicator in search_indicators):
            return {'confidence': 0.9, 'reason': 'search_placeholder'}
        
        # Check name attribute
        name = attrs.get('name', '').lower()
        if any(indicator in name for indicator in search_indicators):
            return {'confidence': 0.8, 'reason': 'search_name'}
        
        # Check id attribute
        element_id = attrs.get('id', '').lower()
        if any(indicator in element_id for indicator in search_indicators):
            return {'confidence': 0.8, 'reason': 'search_id'}
        
        # Check if it's a text input (generic search)
        if input_type in ['text', 'search'] and not attrs.get('readonly'):
            return {'confidence': 0.6, 'reason': 'text_input'}
        
        return None
    
    def _build_hierarchical_context(self, matches: List[MatchingNode], all_elements: List[Dict[str, Any]]) -> List[HierarchicalContext]:
        """Build hierarchical context for each matching node."""
        contexts = []
        
        for match in matches:
            # Find parent elements
            parents = self._find_parent_elements(match.element, all_elements)
            
            # Find sibling elements
            siblings = self._find_sibling_elements(match.element, all_elements)
            
            # Build HTML context
            html_context = self._build_html_context(match, parents, siblings)
            
            # Build semantic structure
            semantic_structure = self._build_semantic_structure(match, parents, siblings)
            
            context = HierarchicalContext(
                target_element=match,
                parent_elements=parents,
                sibling_elements=siblings,
                html_context=html_context,
                depth=len(parents),
                semantic_structure=semantic_structure
            )
            contexts.append(context)
        
        return contexts
    
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
    
    def _build_html_context(self, match: MatchingNode, parents: List[Dict[str, Any]], siblings: List[Dict[str, Any]]) -> str:
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
            for sibling in siblings[:3]:  # Limit to 3 siblings
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
    
    def _build_semantic_structure(self, match: MatchingNode, parents: List[Dict[str, Any]], siblings: List[Dict[str, Any]]) -> str:
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
    
    def _generate_xpath_candidates(self, contexts: List[HierarchicalContext]) -> List[XPathCandidate]:
        """Generate XPath candidates for all contexts."""
        candidates = []
        
        for context in contexts:
            match = context.target_element
            element = match.element
            
            # Generate multiple XPath strategies
            xpath_strategies = [
                self._generate_text_xpath(element),
                self._generate_attribute_xpath(element),
                self._generate_hierarchy_xpath(element, match.hierarchy_path),
                self._generate_combined_xpath(element, context)
            ]
            
            for xpath in xpath_strategies:
                if xpath:  # Only add non-empty XPaths
                    candidates.append(XPathCandidate(
                        xpath=xpath,
                        element=element,
                        confidence=match.match_confidence,
                        is_valid=False  # Will be validated later
                    ))
        
        return candidates
    
    def _generate_text_xpath(self, element: Dict[str, Any]) -> str:
        """Generate XPath based on element text."""
        tag = element.get('tag', 'div')
        text = element.get('text', '').strip()
        
        if text:
            # Escape quotes in text
            escaped_text = text.replace('"', '\\"')
            return f'//{tag}[normalize-space()="{escaped_text}"]'
        
        return ""
    
    def _generate_attribute_xpath(self, element: Dict[str, Any]) -> str:
        """Generate XPath based on element attributes."""
        tag = element.get('tag', 'div')
        attrs = element.get('attributes', {})
        
        # Try different attribute combinations
        if attrs.get('id'):
            return f'//{tag}[@id="{attrs["id"]}"]'
        
        if attrs.get('data-testid'):
            return f'//{tag}[@data-testid="{attrs["data-testid"]}"]'
        
        if attrs.get('class'):
            class_name = attrs['class'].split()[0]  # Use first class
            return f'//{tag}[@class="{class_name}"]'
        
        return ""
    
    def _generate_hierarchy_xpath(self, element: Dict[str, Any], hierarchy: List[str]) -> str:
        """Generate XPath based on hierarchy path."""
        if not hierarchy:
            return ""
        
        # Build XPath from hierarchy
        xpath_parts = []
        for level in hierarchy[-3:]:  # Use last 3 levels
            if ':' in level:
                tag, position = level.split(':')
                xpath_parts.append(f'{tag}[{position}]')
            else:
                xpath_parts.append(level)
        
        return '//' + '/'.join(xpath_parts)
    
    def _generate_combined_xpath(self, element: Dict[str, Any], context: HierarchicalContext) -> str:
        """Generate XPath combining multiple strategies."""
        tag = element.get('tag', 'div')
        text = element.get('text', '').strip()
        attrs = element.get('attributes', {})
        
        conditions = []
        
        if text:
            escaped_text = text.replace('"', '\\"')
            conditions.append(f'normalize-space()="{escaped_text}"')
        
        if attrs.get('class'):
            conditions.append(f'@class="{attrs["class"]}"')
        
        if conditions:
            return f'//{tag}[{" and ".join(conditions)}]'
        
        return ""
    
    def _validate_xpath_candidates(self, candidates: List[XPathCandidate], page) -> List[XPathCandidate]:
        """Validate XPath candidates during selection."""
        validated_candidates = []
        
        for candidate in candidates:
            if not page:
                # If no page available, mark as potentially valid
                candidate.is_valid = True
                validated_candidates.append(candidate)
                continue
            
            try:
                # Use Playwright's locator to check if element exists
                elements = page.locator(candidate.xpath)
                count = elements.count()
                
                if count > 0:
                    candidate.is_valid = True
                    validated_candidates.append(candidate)
                else:
                    candidate.is_valid = False
                    candidate.validation_error = "Element not found in DOM"
                    
            except Exception as e:
                candidate.is_valid = False
                candidate.validation_error = str(e)
        
        return validated_candidates
    
    def _rank_candidates(self, candidates: List[XPathCandidate], query: str, parsed_intent: ParsedIntent) -> List[XPathCandidate]:
        """Rank XPath candidates using heuristics and optional MarkupLM."""
        if not candidates:
            return []
        
        # Filter to only valid candidates
        valid_candidates = [c for c in candidates if c.is_valid]
        if not valid_candidates:
            return []
        
        # Apply intent-specific heuristics
        ranked_candidates = []
        
        for candidate in valid_candidates:
            score = candidate.confidence
            
            # Apply intent-specific bonuses
            intent_bonus = self._apply_intent_bonus(candidate, parsed_intent)
            score += intent_bonus
            
            # Apply element type bonuses
            type_bonus = self._apply_element_type_bonus(candidate, parsed_intent)
            score += type_bonus
            
            # Apply hierarchy bonus
            hierarchy_bonus = self._apply_hierarchy_bonus(candidate)
            score += hierarchy_bonus
            
            # Update confidence
            candidate.confidence = min(score, 1.0)  # Cap at 1.0
            ranked_candidates.append(candidate)
        
        # Sort by confidence
        ranked_candidates.sort(key=lambda c: c.confidence, reverse=True)
        
        return ranked_candidates
    
    def _apply_intent_bonus(self, candidate: XPathCandidate, parsed_intent: ParsedIntent) -> float:
        """Apply intent-specific bonuses to candidate score."""
        bonus = 0.0
        intent = parsed_intent.intent.value
        element = candidate.element
        tag = element.get('tag', '').lower()
        
        if intent == 'click':
            if tag in ['a', 'button']:
                bonus += 0.2
            elif element.get('interactive', False):
                bonus += 0.1
        
        elif intent in ['enter', 'type', 'search']:
            if tag in ['input', 'textarea']:
                bonus += 0.2
            elif tag == 'div' and element.get('contenteditable'):
                bonus += 0.1
        
        elif intent == 'select':
            if tag in ['select', 'option']:
                bonus += 0.2
        
        return bonus
    
    def _apply_element_type_bonus(self, candidate: XPathCandidate, parsed_intent: ParsedIntent) -> float:
        """Apply element type bonuses to candidate score."""
        bonus = 0.0
        element = candidate.element
        attrs = element.get('attributes', {})
        
        # Bonus for specific attributes
        if attrs.get('data-testid'):
            bonus += 0.1
        
        if attrs.get('id'):
            bonus += 0.05
        
        # Bonus for accessibility
        if attrs.get('aria-label'):
            bonus += 0.05
        
        return bonus
    
    def _apply_hierarchy_bonus(self, candidate: XPathCandidate) -> float:
        """Apply hierarchy-based bonuses to candidate score."""
        bonus = 0.0
        element = candidate.element
        hierarchy = element.get('hierarchy', [])
        
        # Bonus for elements closer to root
        if len(hierarchy) <= 3:
            bonus += 0.05
        
        # Bonus for elements in common UI patterns
        hierarchy_str = ' > '.join(hierarchy).lower()
        if any(pattern in hierarchy_str for pattern in ['nav', 'menu', 'button', 'form']):
            bonus += 0.05
        
        return bonus
    
    def _generate_xpath(self, element: Dict[str, Any]) -> str:
        """Generate basic XPath for element."""
        tag = element.get('tag', 'div')
        text = element.get('text', '').strip()
        
        if text:
            escaped_text = text.replace('"', '\\"')
            return f'//{tag}[normalize-space()="{escaped_text}"]'
        
        return f'//{tag}'
    
    def _matches_hierarchy_level(self, element: Dict[str, Any], level: str) -> bool:
        """Check if element matches hierarchy level."""
        # This would match element to hierarchy level
        # For now, return True as placeholder
        return True
    
    def _create_success_result(self, candidate: XPathCandidate, query: str, start_time: float) -> Dict[str, Any]:
        """Create success result."""
        execution_time = (time.time() - start_time) * 1000
        
        return {
            'xpath': candidate.xpath,
            'selector': candidate.xpath,
            'element': candidate.element,
            'confidence': candidate.confidence,
            'strategy': 'enhanced-no-semantic',
            'execution_time_ms': execution_time,
            'elements_found': 1
        }
    
    def _create_no_match_result(self, query: str, start_time: float) -> Dict[str, Any]:
        """Create no match result."""
        execution_time = (time.time() - start_time) * 1000
        
        return {
            'xpath': None,
            'selector': None,
            'element': None,
            'confidence': 0.0,
            'strategy': 'enhanced-no-semantic',
            'execution_time_ms': execution_time,
            'elements_found': 0,
            'error': 'No matching elements found'
        }
    
    def _create_no_valid_result(self, query: str, start_time: float) -> Dict[str, Any]:
        """Create no valid result."""
        execution_time = (time.time() - start_time) * 1000
        
        return {
            'xpath': None,
            'selector': None,
            'element': None,
            'confidence': 0.0,
            'strategy': 'enhanced-no-semantic',
            'execution_time_ms': execution_time,
            'elements_found': 0,
            'error': 'No valid XPath candidates found'
        }
    
    def _create_error_result(self, query: str, error: str, start_time: float) -> Dict[str, Any]:
        """Create error result."""
        execution_time = (time.time() - start_time) * 1000
        
        return {
            'xpath': None,
            'selector': None,
            'element': None,
            'confidence': 0.0,
            'strategy': 'enhanced-no-semantic',
            'execution_time_ms': execution_time,
            'elements_found': 0,
            'error': error
        }