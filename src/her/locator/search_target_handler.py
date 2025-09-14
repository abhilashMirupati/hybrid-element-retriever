"""
Search Target Handler for No-Semantic Mode

This module provides search target handling functionality:
1. Detect search/enter intents
2. Extract value from test step (e.g., "Enter 'John' in search")
3. Find input fields by type/placeholder/name
4. Handle input fields without innerText
"""

from __future__ import annotations

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from .intent_parser import ParsedIntent, IntentType

log = logging.getLogger("her.search_target_handler")

@dataclass
class SearchTarget:
    """Represents a search target with extracted information."""
    target_text: str
    value: Optional[str]
    input_type: str  # 'search', 'text', 'email', 'password', etc.
    confidence: float
    extraction_method: str

class SearchTargetHandler:
    """Handles search targets and input field detection."""
    
    def __init__(self):
        self.search_indicators = ['search', 'query', 'find', 'look', 'enter', 'type']
        self.input_types = ['text', 'search', 'email', 'password', 'tel', 'url']
    
    def extract_search_target(self, parsed_intent: ParsedIntent) -> Optional[SearchTarget]:
        """Extract search target information from parsed intent."""
        intent = parsed_intent.intent.value
        target_text = parsed_intent.target_text
        value = parsed_intent.value
        
        # Check if this is a search/enter intent
        if intent not in ['search', 'enter', 'type']:
            return None
        
        log.info(f"Extracting search target for intent: {intent}, target: '{target_text}', value: '{value}'")
        
        # Determine input type based on context
        input_type = self._determine_input_type(target_text, value, parsed_intent.original_step)
        
        # Calculate confidence based on extraction method
        confidence = self._calculate_extraction_confidence(target_text, value, input_type)
        
        # Determine extraction method
        extraction_method = self._determine_extraction_method(target_text, value)
        
        search_target = SearchTarget(
            target_text=target_text,
            value=value,
            input_type=input_type,
            confidence=confidence,
            extraction_method=extraction_method
        )
        
        log.info(f"Extracted search target: {search_target}")
        return search_target
    
    def find_search_inputs(self, elements: List[Dict[str, Any]], search_target: SearchTarget) -> List[Dict[str, Any]]:
        """Find input fields that match the search target."""
        search_inputs = []
        
        log.info(f"Finding search inputs for target: {search_target.target_text}")
        
        for element in elements:
            if self._is_search_input(element, search_target):
                search_inputs.append(element)
        
        log.info(f"Found {len(search_inputs)} search inputs")
        return search_inputs
    
    def _determine_input_type(self, target_text: str, value: Optional[str], original_step: str) -> str:
        """Determine the most likely input type based on context."""
        step_lower = original_step.lower()
        
        # Check for specific input types
        if 'email' in step_lower or '@' in (value or ''):
            return 'email'
        elif 'password' in step_lower or 'pass' in step_lower:
            return 'password'
        elif 'phone' in step_lower or 'tel' in step_lower:
            return 'tel'
        elif 'url' in step_lower or 'website' in step_lower:
            return 'url'
        elif 'search' in step_lower or 'query' in step_lower or 'enter' in step_lower:
            return 'search'
        else:
            return 'text'
    
    def _calculate_extraction_confidence(self, target_text: str, value: Optional[str], input_type: str) -> float:
        """Calculate confidence in the extraction."""
        confidence = 0.5  # Base confidence
        
        # Boost confidence if we have a value
        if value:
            confidence += 0.3
        
        # Boost confidence if target text is clear
        if target_text and len(target_text) > 2:
            confidence += 0.2
        
        # Boost confidence if input type is specific
        if input_type in ['email', 'password', 'tel']:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _determine_extraction_method(self, target_text: str, value: Optional[str]) -> str:
        """Determine how the search target was extracted."""
        if value and target_text:
            return 'value_and_target'
        elif value:
            return 'value_only'
        elif target_text:
            return 'target_only'
        else:
            return 'none'
    
    def _is_search_input(self, element: Dict[str, Any], search_target: SearchTarget) -> bool:
        """Check if element is a search input that matches the target."""
        tag = element.get('tag', '').lower()
        attrs = element.get('attributes', {})
        
        # Must be an input element
        if tag != 'input':
            return False
        
        input_type = attrs.get('type', '').lower()
        
        # Check if input type matches
        if input_type not in self.input_types:
            return False
        
        # Check if it's readonly or disabled
        if attrs.get('readonly') or attrs.get('disabled'):
            return False
        
        # Check for search indicators
        search_score = 0
        
        # Check placeholder
        placeholder = attrs.get('placeholder', '').lower()
        if any(indicator in placeholder for indicator in self.search_indicators):
            search_score += 0.4
        
        # Check name attribute
        name = attrs.get('name', '').lower()
        if any(indicator in name for indicator in self.search_indicators):
            search_score += 0.3
        
        # Check id attribute
        element_id = attrs.get('id', '').lower()
        if any(indicator in element_id for indicator in self.search_indicators):
            search_score += 0.3
        
        # Check class attribute
        class_name = attrs.get('class', '').lower()
        if any(indicator in class_name for indicator in self.search_indicators):
            search_score += 0.2
        
        # Check aria-label
        aria_label = attrs.get('aria-label', '').lower()
        if any(indicator in aria_label for indicator in self.search_indicators):
            search_score += 0.2
        
        # Check if it's a generic text input
        if input_type in ['text', 'search'] and search_score == 0:
            search_score = 0.1
        
        # Must have some search indicators or be a text/search input
        return search_score > 0.1
    
    def enhance_search_input(self, element: Dict[str, Any], search_target: SearchTarget) -> Dict[str, Any]:
        """Enhance search input element with target information."""
        enhanced = element.copy()
        
        # Add search target information
        enhanced['search_target'] = {
            'target_text': search_target.target_text,
            'value': search_target.value,
            'input_type': search_target.input_type,
            'confidence': search_target.confidence,
            'extraction_method': search_target.extraction_method
        }
        
        # Add search-specific attributes
        enhanced['is_search_input'] = True
        enhanced['search_priority'] = self._calculate_search_priority(element, search_target)
        
        return enhanced
    
    def _calculate_search_priority(self, element: Dict[str, Any], search_target: SearchTarget) -> float:
        """Calculate priority for search input selection."""
        priority = 0.5  # Base priority
        
        attrs = element.get('attributes', {})
        
        # Boost priority for exact type match
        if attrs.get('type', '').lower() == search_target.input_type:
            priority += 0.3
        
        # Boost priority for search-specific attributes
        if attrs.get('data-testid'):
            priority += 0.2
        
        if attrs.get('id'):
            priority += 0.1
        
        if attrs.get('aria-label'):
            priority += 0.1
        
        # Boost priority for visible elements
        if not attrs.get('hidden') and not attrs.get('style', '').__contains__('display: none'):
            priority += 0.1
        
        return min(priority, 1.0)