"""
Intent-Aware MarkupLM Reranker for HER Framework

Enhances MarkupLM reranking with intent-aware heuristics:
- click → boost button/link elements
- type → boost input/textarea elements  
- validate → boost static text/span/div elements

Combines semantic similarity with UI automation heuristics.
"""

from __future__ import annotations

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple

from ..descriptors.canonical import CanonicalNode
from ..intent.enhanced_parser import ParsedIntent

logger = logging.getLogger(__name__)


class IntentAwareReranker:
    """Reranks elements using MarkupLM + intent-aware heuristics."""
    
    def __init__(self):
        # Intent-based element type preferences
        self.intent_preferences = {
            'click': {
                'preferred_tags': {'button', 'a', 'input', 'select', 'option', 'label'},
                'preferred_roles': {'button', 'link', 'menuitem', 'tab', 'option'},
                'boost_score': 0.3
            },
            'type': {
                'preferred_tags': {'input', 'textarea', 'select'},
                'preferred_roles': {'textbox', 'combobox', 'searchbox'},
                'boost_score': 0.4
            },
            'validate': {
                'preferred_tags': {'span', 'div', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'},
                'preferred_roles': {'text', 'heading', 'status', 'alert'},
                'boost_score': 0.2
            }
        }
        
        # Element interactivity scoring
        self.interactive_boost = 0.2
        self.visibility_boost = 0.1
        self.accessibility_boost = 0.15
    
    def rerank_candidates(
        self,
        candidates: List[CanonicalNode],
        intent: ParsedIntent,
        markup_scores: List[float],
        target_text: str
    ) -> List[Tuple[float, CanonicalNode, List[str]]]:
        """
        Rerank candidates using MarkupLM scores + intent-aware heuristics.
        
        Args:
            candidates: List of candidate canonical nodes
            intent: Parsed user intent
            markup_scores: MarkupLM similarity scores
            target_text: Target text for matching
            
        Returns:
            List of (final_score, node, reasons) tuples sorted by score
        """
        if not candidates or not markup_scores:
            return []
        
        if len(candidates) != len(markup_scores):
            logger.warning(f"Mismatch between candidates ({len(candidates)}) and scores ({len(markup_scores)})")
            return []
        
        # Apply intent-aware heuristics
        reranked = []
        for i, (node, base_score) in enumerate(zip(candidates, markup_scores)):
            final_score, reasons = self._calculate_intent_aware_score(
                node, intent, base_score, target_text
            )
            reranked.append((final_score, node, reasons))
        
        # Sort by final score (descending)
        reranked.sort(key=lambda x: x[0], reverse=True)
        
        logger.info(f"Reranked {len(reranked)} candidates using intent-aware heuristics")
        return reranked
    
    def _calculate_intent_aware_score(
        self,
        node: CanonicalNode,
        intent: ParsedIntent,
        base_score: float,
        target_text: str
    ) -> Tuple[float, List[str]]:
        """Calculate final score with intent-aware heuristics."""
        reasons = [f"markup_cosine={base_score:.3f}"]
        final_score = base_score
        
        # Intent-based element type matching
        intent_boost = self._calculate_intent_boost(node, intent)
        if intent_boost > 0:
            final_score += intent_boost
            reasons.append(f"intent_boost=+{intent_boost:.3f}")
        
        # Text matching boost
        text_boost = self._calculate_text_matching_boost(node, target_text)
        if text_boost > 0:
            final_score += text_boost
            reasons.append(f"text_match=+{text_boost:.3f}")
        
        # Interactivity boost
        if node.is_interactive:
            final_score += self.interactive_boost
            reasons.append(f"interactive=+{self.interactive_boost:.3f}")
        
        # Accessibility boost
        if node.aria_label or node.title:
            final_score += self.accessibility_boost
            reasons.append(f"accessible=+{self.accessibility_boost:.3f}")
        
        # Visibility boost (if we have visibility info)
        if hasattr(node, 'visible') and node.visible:
            final_score += self.visibility_boost
            reasons.append(f"visible=+{self.visibility_boost:.3f}")
        
        # Penalty for very long text (likely not clickable)
        if len(node.inner_text) > 200:
            penalty = -0.1
            final_score += penalty
            reasons.append(f"long_text={penalty:.3f}")
        
        # Ensure score is within reasonable bounds
        final_score = max(0.0, min(1.0, final_score))
        
        return final_score, reasons
    
    def _calculate_intent_boost(self, node: CanonicalNode, intent: ParsedIntent) -> float:
        """Calculate boost based on intent and element type."""
        action = intent.action.lower()
        
        if action not in self.intent_preferences:
            return 0.0
        
        preferences = self.intent_preferences[action]
        boost = 0.0
        
        # Check tag preference
        if node.tag.lower() in preferences['preferred_tags']:
            boost += preferences['boost_score']
        
        # Check role preference
        if node.role and node.role.lower() in preferences['preferred_roles']:
            boost += preferences['boost_score'] * 0.8
        
        # Special cases for specific intents
        if action == 'click':
            # Extra boost for clickable elements
            if node.is_interactive:
                boost += 0.1
            
            # Penalty for non-interactive elements
            if not node.is_interactive and node.tag.lower() not in {'span', 'div', 'p'}:
                boost -= 0.2
        
        elif action == 'type':
            # Extra boost for input elements
            if node.tag.lower() in {'input', 'textarea'}:
                boost += 0.2
            
            # Penalty for non-input elements
            if node.tag.lower() not in {'input', 'textarea', 'select'}:
                boost -= 0.3
        
        elif action == 'validate':
            # Boost for text-containing elements
            if node.inner_text and len(node.inner_text) > 0:
                boost += 0.1
            
            # Penalty for interactive elements (validation usually targets text)
            if node.is_interactive and node.tag.lower() not in {'span', 'div', 'p'}:
                boost -= 0.1
        
        return boost
    
    def _calculate_text_matching_boost(self, node: CanonicalNode, target_text: str) -> float:
        """Calculate boost based on text matching quality."""
        if not target_text or not node.inner_text:
            return 0.0
        
        target_lower = target_text.lower()
        text_lower = node.inner_text.lower()
        
        # Exact match
        if target_lower == text_lower:
            return 0.5
        
        # Contains match
        if target_lower in text_lower:
            return 0.3
        
        # Word boundary match
        target_words = set(target_lower.split())
        text_words = set(text_lower.split())
        word_overlap = len(target_words.intersection(text_words))
        
        if word_overlap > 0:
            return 0.1 + (word_overlap / len(target_words)) * 0.2
        
        # Check attributes for matches
        attribute_boost = 0.0
        for attr in ['aria_label', 'title', 'placeholder']:
            attr_value = getattr(node, attr, '')
            if attr_value and target_lower in attr_value.lower():
                attribute_boost += 0.1
        
        return attribute_boost
    
    def get_reranking_explanation(
        self,
        candidates: List[CanonicalNode],
        intent: ParsedIntent,
        markup_scores: List[float],
        target_text: str
    ) -> Dict[str, any]:
        """Get detailed explanation of reranking process."""
        reranked = self.rerank_candidates(candidates, intent, markup_scores, target_text)
        
        explanation = {
            'intent': {
                'action': intent.action,
                'target': intent.target,
                'value': intent.value,
                'confidence': intent.confidence
            },
            'candidates_count': len(candidates),
            'reranking_strategy': 'markuplm_intent_aware',
            'top_candidates': []
        }
        
        # Add top 3 candidates with explanations
        for i, (score, node, reasons) in enumerate(reranked[:3]):
            candidate_info = {
                'rank': i + 1,
                'score': score,
                'tag': node.tag,
                'role': node.role,
                'text': node.inner_text[:50] + '...' if len(node.inner_text) > 50 else node.inner_text,
                'is_interactive': node.is_interactive,
                'reasons': reasons
            }
            explanation['top_candidates'].append(candidate_info)
        
        return explanation


def rerank_with_intent_awareness(
    candidates: List[CanonicalNode],
    intent: ParsedIntent,
    markup_scores: List[float],
    target_text: str
) -> List[Tuple[float, CanonicalNode, List[str]]]:
    """
    Convenience function to rerank candidates with intent awareness.
    
    Args:
        candidates: List of candidate canonical nodes
        intent: Parsed user intent
        markup_scores: MarkupLM similarity scores
        target_text: Target text for matching
        
    Returns:
        List of (final_score, node, reasons) tuples sorted by score
    """
    reranker = IntentAwareReranker()
    return reranker.rerank_candidates(candidates, intent, markup_scores, target_text)