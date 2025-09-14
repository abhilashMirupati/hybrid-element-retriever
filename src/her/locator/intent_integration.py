"""
Intent Integration for No-Semantic Mode

This module provides intent parsing integration functionality:
1. Integrate parsed intent with MarkupLM context
2. Use target text for better element matching
3. Apply intent-specific bonuses
4. Handle search/enter intents properly
"""

from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .intent_parser import ParsedIntent, IntentType
from .core_no_semantic import ExactMatch

log = logging.getLogger("her.intent_integration")

@dataclass
class IntentScoredMatch:
    """Match with intent-specific scoring applied."""
    match: ExactMatch
    intent_score: float
    final_score: float
    scoring_reasons: List[str]

class IntentIntegration:
    """Integrates intent parsing with element matching and ranking."""
    
    def __init__(self):
        self.intent_weights = {
            'click': {'button': 0.3, 'link': 0.2, 'interactive': 0.1},
            'enter': {'input': 0.3, 'textarea': 0.2, 'contenteditable': 0.1},
            'search': {'input': 0.3, 'search': 0.2, 'text': 0.1},
            'select': {'select': 0.3, 'option': 0.2, 'dropdown': 0.1},
            'navigate': {'link': 0.3, 'button': 0.1}
        }
    
    def apply_intent_scoring(self, matches: List[ExactMatch], parsed_intent: ParsedIntent) -> List[IntentScoredMatch]:
        """Apply intent-specific scoring to matches."""
        if not matches:
            return []
        
        intent = parsed_intent.intent.value
        target_text = parsed_intent.target_text
        value = parsed_intent.value
        
        log.info(f"Applying intent scoring for intent: {intent}, target: '{target_text}', value: '{value}'")
        
        scored_matches = []
        
        for match in matches:
            # Calculate intent-specific score
            intent_score = self._calculate_intent_score(match, parsed_intent)
            
            # Calculate final score (weighted combination)
            final_score = (match.match_confidence * 0.7) + (intent_score * 0.3)
            
            # Generate scoring reasons
            scoring_reasons = self._generate_scoring_reasons(match, parsed_intent, intent_score)
            
            scored_match = IntentScoredMatch(
                match=match,
                intent_score=intent_score,
                final_score=final_score,
                scoring_reasons=scoring_reasons
            )
            
            scored_matches.append(scored_match)
        
        # Sort by final score
        scored_matches.sort(key=lambda m: m.final_score, reverse=True)
        
        log.info(f"Applied intent scoring to {len(scored_matches)} matches")
        return scored_matches
    
    def _calculate_intent_score(self, match: ExactMatch, parsed_intent: ParsedIntent) -> float:
        """Calculate intent-specific score for a match."""
        intent = parsed_intent.intent.value
        element = match.element
        tag = element.get('tag', '').lower()
        attrs = element.get('attributes', {})
        
        base_score = 0.0
        
        # Get intent-specific weights
        weights = self.intent_weights.get(intent, {})
        
        # Apply tag-based scoring
        if tag in weights:
            base_score += weights[tag]
        
        # Apply attribute-based scoring
        if intent == 'click':
            if attrs.get('role') == 'button':
                base_score += 0.2
            if attrs.get('onclick'):
                base_score += 0.1
            if attrs.get('data-testid'):
                base_score += 0.1
        
        elif intent in ['enter', 'type', 'search']:
            input_type = attrs.get('type', '').lower()
            if input_type in ['text', 'search', 'email', 'password']:
                base_score += 0.2
            if attrs.get('placeholder'):
                base_score += 0.1
            if attrs.get('name') in ['search', 'query', 'q']:
                base_score += 0.1
        
        elif intent == 'select':
            if tag == 'select':
                base_score += 0.3
            elif tag == 'option':
                base_score += 0.2
            elif 'dropdown' in attrs.get('class', '').lower():
                base_score += 0.1
        
        elif intent == 'navigate':
            if tag == 'a' and attrs.get('href'):
                base_score += 0.3
            if 'nav' in attrs.get('class', '').lower():
                base_score += 0.1
        
        # Apply text-based scoring
        text = element.get('text', '').lower()
        target_text = parsed_intent.target_text.lower()
        
        if target_text in text:
            base_score += 0.2
        
        # Apply value-based scoring for search/enter intents
        if intent in ['enter', 'type', 'search'] and parsed_intent.value:
            value = parsed_intent.value.lower()
            if value in text:
                base_score += 0.1
        
        # Cap score at 1.0
        return min(base_score, 1.0)
    
    def _generate_scoring_reasons(self, match: ExactMatch, parsed_intent: ParsedIntent, intent_score: float) -> List[str]:
        """Generate human-readable scoring reasons."""
        reasons = []
        
        intent = parsed_intent.intent.value
        element = match.element
        tag = element.get('tag', '').lower()
        attrs = element.get('attributes', {})
        
        # Intent-specific reasons
        if intent == 'click':
            if tag in ['button', 'a']:
                reasons.append(f"intent-click-{tag}")
            if attrs.get('role') == 'button':
                reasons.append("intent-click-role-button")
            if attrs.get('data-testid'):
                reasons.append("intent-click-testid")
        
        elif intent in ['enter', 'type', 'search']:
            if tag in ['input', 'textarea']:
                reasons.append(f"intent-{intent}-{tag}")
            if attrs.get('type') in ['text', 'search']:
                reasons.append(f"intent-{intent}-type-{attrs['type']}")
            if attrs.get('placeholder'):
                reasons.append("intent-enter-placeholder")
        
        elif intent == 'select':
            if tag in ['select', 'option']:
                reasons.append(f"intent-select-{tag}")
            if 'dropdown' in attrs.get('class', '').lower():
                reasons.append("intent-select-dropdown")
        
        elif intent == 'navigate':
            if tag == 'a' and attrs.get('href'):
                reasons.append("intent-navigate-link")
            if 'nav' in attrs.get('class', '').lower():
                reasons.append("intent-navigate-nav")
        
        # Text matching reasons
        text = element.get('text', '').lower()
        target_text = parsed_intent.target_text.lower()
        
        if target_text in text:
            reasons.append("text-match")
        
        # Value matching reasons
        if parsed_intent.value and parsed_intent.value.lower() in text:
            reasons.append("value-match")
        
        # Confidence reasons
        if match.match_confidence >= 0.9:
            reasons.append("high-confidence")
        elif match.match_confidence >= 0.7:
            reasons.append("medium-confidence")
        else:
            reasons.append("low-confidence")
        
        return reasons
    
    def enhance_context_with_intent(self, context: HierarchicalContext, parsed_intent: ParsedIntent) -> HierarchicalContext:
        """Enhance hierarchical context with intent information."""
        # Add intent information to context
        enhanced_html = f'<!-- Intent: {parsed_intent.intent.value}, Target: {parsed_intent.target_text} -->\n'
        enhanced_html += context.html_context
        
        # Create enhanced context
        enhanced_context = HierarchicalContext(
            target_element=context.target_element,
            parent_elements=context.parent_elements,
            sibling_elements=context.sibling_elements,
            html_context=enhanced_html,
            depth=context.depth,
            semantic_structure=context.semantic_structure,
            hierarchy_path=context.hierarchy_path
        )
        
        return enhanced_context