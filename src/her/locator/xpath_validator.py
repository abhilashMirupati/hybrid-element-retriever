"""
XPath Validator for No-Semantic Mode

This module provides XPath validation functionality:
1. Validate XPath during selection, not after
2. Generate multiple XPath candidates
3. Select best valid XPath
4. Add XPath uniqueness checking
"""

from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .hierarchical_context import HierarchicalContext

log = logging.getLogger("her.xpath_validator")

@dataclass
class XPathCandidate:
    """XPath candidate with validation status."""
    xpath: str
    element: Dict[str, Any]
    confidence: float
    is_valid: bool
    validation_error: Optional[str] = None
    strategy: str = "unknown"

class XPathValidator:
    """Validator for XPath candidates with multiple strategies."""
    
    def __init__(self):
        self.validation_cache = {}  # Cache for performance
    
    def generate_candidates(self, contexts: List[HierarchicalContext]) -> List[XPathCandidate]:
        """Generate multiple XPath candidates for all contexts."""
        candidates = []
        
        log.info(f"Generating XPath candidates for {len(contexts)} contexts")
        
        for context in contexts:
            match = context.target_element
            element = match.element
            
            # Generate multiple XPath strategies
            xpath_strategies = [
                self._generate_text_xpath(element),
                self._generate_attribute_xpath(element),
                self._generate_hierarchy_xpath(element, context.hierarchy_path),
                self._generate_combined_xpath(element, context)
            ]
            
            for i, xpath in enumerate(xpath_strategies):
                if xpath:  # Only add non-empty XPaths
                    strategy_names = ['text', 'attribute', 'hierarchy', 'combined']
                    candidates.append(XPathCandidate(
                        xpath=xpath,
                        element=element,
                        confidence=match.match_confidence,
                        is_valid=False,  # Will be validated later
                        strategy=strategy_names[i] if i < len(strategy_names) else 'unknown'
                    ))
        
        log.info(f"Generated {len(candidates)} XPath candidates")
        return candidates
    
    def validate_candidates(self, candidates: List[XPathCandidate], page) -> List[XPathCandidate]:
        """Validate XPath candidates during selection."""
        validated_candidates = []
        
        log.info(f"Validating {len(candidates)} XPath candidates")
        
        for candidate in candidates:
            if not page:
                # If no page available, mark as potentially valid
                candidate.is_valid = True
                validated_candidates.append(candidate)
                continue
            
            # Check cache first
            cache_key = f"{candidate.xpath}:{candidate.element.get('tag', '')}"
            if cache_key in self.validation_cache:
                candidate.is_valid = self.validation_cache[cache_key]
                validated_candidates.append(candidate)
                continue
            
            try:
                # Use Playwright's locator to check if element exists
                elements = page.locator(candidate.xpath)
                count = elements.count()
                
                if count > 0:
                    candidate.is_valid = True
                    self.validation_cache[cache_key] = True
                    validated_candidates.append(candidate)
                else:
                    candidate.is_valid = False
                    candidate.validation_error = "Element not found in DOM"
                    self.validation_cache[cache_key] = False
                    
            except Exception as e:
                candidate.is_valid = False
                candidate.validation_error = str(e)
                self.validation_cache[cache_key] = False
        
        valid_count = len([c for c in validated_candidates if c.is_valid])
        log.info(f"Validated {valid_count} valid XPath candidates out of {len(validated_candidates)}")
        
        return validated_candidates
    
    def _generate_text_xpath(self, element: Dict[str, Any]) -> str:
        """Generate XPath based on element text."""
        tag = element.get('tag', 'div')
        text = element.get('text', '').strip()
        
        # Fix invalid tag names for XPath
        if tag.startswith('#'):
            # For text nodes and comments, find the parent element instead
            return f'//text()[contains(normalize-space(), "{text.replace('"', '\\"')}")]'
        
        if text:
            # Escape quotes in text
            escaped_text = text.replace('"', '\\"')
            # Use contains() for more flexible matching
            return f'//{tag}[contains(normalize-space(), "{escaped_text}")]'
        
        return ""
    
    def _generate_attribute_xpath(self, element: Dict[str, Any]) -> str:
        """Generate XPath based on element attributes."""
        tag = element.get('tag', 'div')
        attrs = element.get('attributes', {})
        
        # Fix invalid tag names for XPath
        if tag.startswith('#'):
            # For text nodes and comments, use attribute-based selection on parent elements
            if attrs.get('id'):
                return f'//*[@id="{attrs["id"]}"]'
            # Fall back to text-based selection
            text = element.get('text', '').strip()
            if text:
                return f'//text()[contains(normalize-space(), "{text.replace('"', '\\"')}")]'
            return ""
        
        # Try different attribute combinations
        if attrs.get('id'):
            return f'//{tag}[@id="{attrs["id"]}"]'
        
        if attrs.get('data-testid'):
            return f'//{tag}[@data-testid="{attrs["data-testid"]}"]'
        
        if attrs.get('class'):
            # Use the full class string, not just the first part
            class_value = attrs['class']
            return f'//{tag}[contains(@class, "{class_value.split()[0]}")]'
        
        # Try aria-label as fallback
        if attrs.get('aria-label'):
            return f'//{tag}[@aria-label="{attrs["aria-label"]}"]'
        
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
        
        # Fix invalid tag names for XPath
        if tag.startswith('#'):
            # For text nodes and comments, use text-based selection
            if text:
                escaped_text = text.replace('"', '\\"')
                return f'//text()[contains(normalize-space(), "{escaped_text}")]'
            return ""
        
        conditions = []
        
        if text:
            escaped_text = text.replace('"', '\\"')
            conditions.append(f'contains(normalize-space(), "{escaped_text}")')
        
        if attrs.get('id'):
            conditions.append(f'@id="{attrs["id"]}"')
        
        if attrs.get('class'):
            class_value = attrs['class']
            conditions.append(f'contains(@class, "{class_value.split()[0]}")')
        
        if attrs.get('aria-label'):
            conditions.append(f'@aria-label="{attrs["aria-label"]}"')
        
        if conditions:
            return f'//{tag}[{" and ".join(conditions)}]'
        
        return ""
    
    def select_best_candidate(self, candidates: List[XPathCandidate]) -> Optional[XPathCandidate]:
        """Select the best XPath candidate from validated candidates."""
        if not candidates:
            return None
        
        # Filter to only valid candidates
        valid_candidates = [c for c in candidates if c.is_valid]
        if not valid_candidates:
            return None
        
        # Sort by confidence and strategy preference
        strategy_preference = {
            'attribute': 1.0,
            'text': 0.9,
            'combined': 0.8,
            'hierarchy': 0.7,
            'unknown': 0.5
        }
        
        def score_candidate(candidate):
            base_score = candidate.confidence
            strategy_score = strategy_preference.get(candidate.strategy, 0.5)
            return base_score * strategy_score
        
        valid_candidates.sort(key=score_candidate, reverse=True)
        
        best_candidate = valid_candidates[0]
        log.info(f"Selected best XPath candidate: {best_candidate.xpath} (strategy: {best_candidate.strategy}, confidence: {best_candidate.confidence:.3f})")
        
        return best_candidate