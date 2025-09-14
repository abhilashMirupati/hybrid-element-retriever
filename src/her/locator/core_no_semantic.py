"""
Core No-Semantic Mode Implementation

This module provides the core no-semantic matching functionality with:
1. Exact text/attribute matching
2. Accessibility tree fallback
3. Search target handling
4. Intent-specific heuristics
"""

from __future__ import annotations

import re
import time
import logging
from typing import List, Dict, Any, Tuple, Optional, Union
from dataclasses import dataclass
from enum import Enum

from .intent_parser import IntentParser, ParsedIntent, IntentType

log = logging.getLogger("her.core_no_semantic")

@dataclass
class ExactMatch:
    """Represents an exact match found in DOM."""
    element: Dict[str, Any]
    match_type: str  # 'innerText', 'attribute', 'accessibility', 'search_input'
    match_confidence: float
    matched_text: str
    matched_attribute: Optional[str] = None

class CoreNoSemanticMatcher:
    """Core no-semantic matcher with exact matching only."""
    
    def __init__(self):
        self.intent_parser = IntentParser()
    
    def find_exact_matches(self, elements: List[Dict[str, Any]], parsed_intent: ParsedIntent) -> List[ExactMatch]:
        """Find all exact matches using no-semantic approach."""
        matches = []
        target_text = parsed_intent.target_text
        intent = parsed_intent.intent.value
        
        log.info(f"Finding exact matches for target: '{target_text}', intent: {intent}")
        
        for element in elements:
            # 1. InnerText matching
            if self._matches_inner_text(element, target_text):
                matches.append(ExactMatch(
                    element=element,
                    match_type='innerText',
                    match_confidence=1.0,
                    matched_text=target_text
                ))
            
            # 2. Attribute matching
            attr_match = self._matches_attributes(element, target_text)
            if attr_match:
                matches.append(ExactMatch(
                    element=element,
                    match_type='attribute',
                    match_confidence=attr_match['confidence'],
                    matched_text=target_text,
                    matched_attribute=attr_match['field']
                ))
            
            # 3. Accessibility matching
            ax_match = self._matches_accessibility(element, target_text)
            if ax_match:
                matches.append(ExactMatch(
                    element=element,
                    match_type='accessibility',
                    match_confidence=ax_match['confidence'],
                    matched_text=target_text
                ))
            
            # 4. Search input matching (for search/enter intents)
            if intent in ['search', 'enter', 'type']:
                search_match = self._matches_search_input(element, target_text, parsed_intent.value)
                if search_match:
                    matches.append(ExactMatch(
                        element=element,
                        match_type='search_input',
                        match_confidence=search_match['confidence'],
                        matched_text=target_text
                    ))
        
        log.info(f"Found {len(matches)} exact matches")
        return matches
    
    def _matches_inner_text(self, element: Dict[str, Any], target_text: str) -> bool:
        """Check if element's innerText matches target exactly."""
        text = element.get('text', '').strip()
        return target_text.lower() in text.lower()
    
    def _matches_attributes(self, element: Dict[str, Any], target_text: str) -> Optional[Dict[str, Any]]:
        """Check if element's attributes match target exactly."""
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
        """Check if element's accessibility attributes match target exactly."""
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
    
    def apply_intent_heuristics(self, matches: List[ExactMatch], parsed_intent: ParsedIntent) -> List[ExactMatch]:
        """Apply intent-specific heuristics to rank matches."""
        if not matches:
            return matches
        
        intent = parsed_intent.intent.value
        
        for match in matches:
            element = match.element
            tag = element.get('tag', '').lower()
            
            # Apply intent-specific bonuses
            if intent == 'click':
                if tag in ['a', 'button']:
                    match.match_confidence += 0.2
                elif element.get('interactive', False):
                    match.match_confidence += 0.1
                elif tag in ['span', 'div'] and element.get('attributes', {}).get('role') == 'button':
                    match.match_confidence += 0.15
            
            elif intent in ['enter', 'type', 'search']:
                if tag in ['input', 'textarea']:
                    match.match_confidence += 0.2
                elif tag == 'div' and element.get('contenteditable'):
                    match.match_confidence += 0.1
            
            elif intent == 'select':
                if tag in ['select', 'option']:
                    match.match_confidence += 0.2
                elif tag in ['div', 'ul', 'li'] and 'dropdown' in element.get('attributes', {}).get('class', '').lower():
                    match.match_confidence += 0.15
            
            # Apply element type bonuses
            attrs = element.get('attributes', {})
            if attrs.get('data-testid'):
                match.match_confidence += 0.1
            if attrs.get('id'):
                match.match_confidence += 0.05
            if attrs.get('aria-label'):
                match.match_confidence += 0.05
            
            # Cap confidence at 1.0
            match.match_confidence = min(match.match_confidence, 1.0)
        
        # Sort by confidence
        matches.sort(key=lambda m: m.match_confidence, reverse=True)
        return matches