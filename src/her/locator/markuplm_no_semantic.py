"""
MarkupLM-enhanced No-Semantic Mode for HER framework.

This module integrates MarkupLM model for enhanced snippet scoring
in no-semantic mode with hierarchical context.
"""

from __future__ import annotations

import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from .intent_parser import IntentParser, ParsedIntent, IntentType
from .target_matcher import TargetMatcher, MatchResult
from ..embeddings.markuplm_snippet_scorer import MarkupLMSnippetScorer, SnippetScore
from ..descriptors.markuplm_hierarchy_builder import MarkupLMHierarchyBuilder
from ..utils.xpath_generator import generate_xpath_for_element
from ..core.config_service import get_config_service

log = logging.getLogger("her.markuplm_no_semantic")


@dataclass
class MarkupLMMatchResult:
    """Result of MarkupLM-enhanced matching."""
    element: Dict[str, Any]
    score: float
    xpath: str
    confidence: float
    strategy: str
    reasons: List[str]
    html_context: str
    hierarchy_path: List[str]


class MarkupLMNoSemanticMatcher:
    """MarkupLM-enhanced no-semantic matcher with hierarchical context."""
    
    def __init__(self, model_name: Optional[str] = None):
        """Initialize MarkupLM no-semantic matcher.
        
        Args:
            model_name: Name of the MarkupLM model to use (if None, uses config)
        """
        self.intent_parser = IntentParser()
        self.target_matcher = TargetMatcher(case_sensitive=False)
        self.hierarchy_builder = MarkupLMHierarchyBuilder()
        
        # Get configuration
        config_service = get_config_service()
        
        # Use provided model name or get from config
        if model_name is None:
            model_name = config_service.get_markuplm_model_name()
        
        # Initialize MarkupLM scorer
        try:
            self.markup_scorer = MarkupLMSnippetScorer(
                model_name=model_name,
                device=config_service.get_markuplm_device(),
                batch_size=config_service.get_markuplm_batch_size()
            )
            self.markup_available = True
            log.info(f"MarkupLM scorer initialized with model: {model_name}")
        except Exception as e:
            log.warning(f"MarkupLM scorer initialization failed: {e}")
            self.markup_scorer = None
            self.markup_available = False
        
        log.info(f"MarkupLM No-Semantic Matcher initialized (MarkupLM available: {self.markup_available})")
    
    def query(self, query: str, elements: List[Dict[str, Any]], page=None) -> Dict[str, Any]:
        """Main query method for MarkupLM-enhanced no-semantic mode.
        
        Args:
            query: User query string
            elements: List of available elements
            page: Optional page object for validation
            
        Returns:
            Query result dictionary
        """
        start_time = time.time()
        
        try:
            log.info(f"MarkupLM No-Semantic query: '{query}' with {len(elements)} elements")
            
            # Step 1: Parse intent
            parsed_intent = self.intent_parser.parse_step(query)
            log.info(f"Parsed intent: {parsed_intent.intent.value}, target: '{parsed_intent.target_text}'")
            
            # Step 2: Find initial candidates using exact matching
            initial_candidates = self._find_initial_candidates(elements, parsed_intent)
            log.info(f"Found {len(initial_candidates)} initial candidates")
            
            if not initial_candidates:
                return self._create_no_match_result(query, start_time)
            
            # Step 3: Build hierarchical context for candidates
            enhanced_candidates = self.hierarchy_builder.build_context_for_candidates(
                initial_candidates, elements
            )
            log.info(f"Enhanced {len(enhanced_candidates)} candidates with hierarchical context")
            
            # Step 4: Score candidates using MarkupLM (if available)
            if self.markup_available and self.markup_scorer:
                scored_candidates = self._score_with_markuplm(enhanced_candidates, query, parsed_intent)
                log.info(f"Scored {len(scored_candidates)} candidates with MarkupLM")
            else:
                # Fallback to basic scoring
                scored_candidates = self._score_without_markuplm(enhanced_candidates, query, parsed_intent)
                log.info(f"Scored {len(scored_candidates)} candidates without MarkupLM")
            
            # Step 5: Select best candidate
            best_candidate = self._select_best_candidate(scored_candidates, query, parsed_intent)
            
            if best_candidate:
                return self._create_success_result(best_candidate, query, start_time)
            else:
                return self._create_no_valid_result(query, start_time)
                
        except Exception as e:
            log.error(f"MarkupLM no-semantic query failed: {e}")
            return self._create_error_result(query, str(e), start_time)
    
    def _find_initial_candidates(self, elements: List[Dict[str, Any]], 
                                parsed_intent: ParsedIntent) -> List[Dict[str, Any]]:
        """Find initial candidates using exact matching.
        
        Args:
            elements: List of available elements
            parsed_intent: Parsed user intent
            
        Returns:
            List of initial candidate elements
        """
        candidates = []
        target_text = parsed_intent.target_text
        
        if not target_text:
            return candidates
        
        # Use target matcher to find exact matches
        for element in elements:
            match_result = self.target_matcher.match_element(element, target_text)
            if match_result and match_result.score >= 0.5:  # Minimum score threshold
                candidates.append(element)
        
        # If no exact matches, try partial matches
        if not candidates:
            for element in elements:
                match_result = self.target_matcher.match_element(element, target_text)
                if match_result and match_result.score >= 0.3:  # Lower threshold for partial matches
                    candidates.append(element)
        
        # If still no matches, try word-level matches
        if not candidates:
            for element in elements:
                match_result = self.target_matcher.match_element(element, target_text)
                if match_result and match_result.score >= 0.1:  # Very low threshold for word matches
                    candidates.append(element)
        
        return candidates
    
    def _score_with_markuplm(self, enhanced_candidates: List[Dict[str, Any]], 
                            query: str, parsed_intent: ParsedIntent) -> List[MarkupLMMatchResult]:
        """Score candidates using MarkupLM.
        
        Args:
            enhanced_candidates: Candidates with hierarchical context
            query: User query string
            parsed_intent: Parsed user intent
            
        Returns:
            List of scored match results
        """
        if not self.markup_scorer or not enhanced_candidates:
            return []
        
        try:
            # Score snippets using MarkupLM
            snippet_scores = self.markup_scorer.score_snippets(enhanced_candidates, query)
            
            # Convert to MarkupLMMatchResult objects
            results = []
            for snippet_score in snippet_scores:
                # Find the corresponding enhanced candidate
                enhanced_candidate = None
                for candidate in enhanced_candidates:
                    if candidate.get('element') == snippet_score.element:
                        enhanced_candidate = candidate
                        break
                
                if enhanced_candidate:
                    result = MarkupLMMatchResult(
                        element=snippet_score.element,
                        score=snippet_score.score,
                        xpath=snippet_score.xpath,
                        confidence=snippet_score.confidence,
                        strategy="markuplm-enhanced",
                        reasons=snippet_score.reasons,
                        html_context=enhanced_candidate.get('html_context', ''),
                        hierarchy_path=enhanced_candidate.get('hierarchy_path', [])
                    )
                    results.append(result)
            
            return results
            
        except Exception as e:
            log.error(f"MarkupLM scoring failed: {e}")
            return self._score_without_markuplm(enhanced_candidates, query, parsed_intent)
    
    def _score_without_markuplm(self, enhanced_candidates: List[Dict[str, Any]], 
                               query: str, parsed_intent: ParsedIntent) -> List[MarkupLMMatchResult]:
        """Score candidates without MarkupLM (fallback).
        
        Args:
            enhanced_candidates: Candidates with hierarchical context
            query: User query string
            parsed_intent: Parsed user intent
            
        Returns:
            List of scored match results
        """
        results = []
        
        for candidate in enhanced_candidates:
            element = candidate.get('element', candidate)
            
            # Basic scoring based on exact matching
            match_result = self.target_matcher.match_element(element, parsed_intent.target_text)
            if not match_result:
                continue
            
            # Generate XPath
            xpath = generate_xpath_for_element(element)
            
            # Calculate confidence based on match score and context
            base_confidence = match_result.score
            
            # Add context bonuses
            context_bonus = 0.0
            if candidate.get('parents'):
                context_bonus += 0.1
            if candidate.get('siblings'):
                context_bonus += 0.05
            if candidate.get('hierarchy_path'):
                context_bonus += 0.05
            
            final_confidence = min(base_confidence + context_bonus, 1.0)
            
            # Generate reasons
            reasons = [f"exact_match_{match_result.match_type}"]
            if candidate.get('parents'):
                reasons.append("has_parent_context")
            if candidate.get('siblings'):
                reasons.append("has_sibling_context")
            
            result = MarkupLMMatchResult(
                element=element,
                score=base_confidence,
                xpath=xpath,
                confidence=final_confidence,
                strategy="exact-match-fallback",
                reasons=reasons,
                html_context=candidate.get('html_context', ''),
                hierarchy_path=candidate.get('hierarchy_path', [])
            )
            results.append(result)
        
        # Sort by confidence
        results.sort(key=lambda x: x.confidence, reverse=True)
        
        return results
    
    def _select_best_candidate(self, scored_candidates: List[MarkupLMMatchResult], 
                              query: str, parsed_intent: ParsedIntent) -> Optional[MarkupLMMatchResult]:
        """Select the best candidate from scored results.
        
        Args:
            scored_candidates: List of scored candidates
            query: User query string
            parsed_intent: Parsed user intent
            
        Returns:
            Best candidate or None
        """
        if not scored_candidates:
            return None
        
        # Apply additional heuristics
        best_candidate = None
        best_score = -1.0
        
        for candidate in scored_candidates:
            score = candidate.confidence
            
            # Apply intent-specific bonuses
            intent_bonus = self._apply_intent_bonus(candidate, parsed_intent)
            score += intent_bonus
            
            # Apply element type bonuses
            type_bonus = self._apply_element_type_bonus(candidate, parsed_intent)
            score += type_bonus
            
            # Apply hierarchy bonuses
            hierarchy_bonus = self._apply_hierarchy_bonus(candidate)
            score += hierarchy_bonus
            
            # Cap score at 1.0
            score = min(score, 1.0)
            
            if score > best_score:
                best_score = score
                best_candidate = candidate
        
        return best_candidate
    
    def _apply_intent_bonus(self, candidate: MarkupLMMatchResult, 
                           parsed_intent: ParsedIntent) -> float:
        """Apply intent-specific bonuses to candidate score.
        
        Args:
            candidate: Candidate match result
            parsed_intent: Parsed user intent
            
        Returns:
            Bonus score
        """
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
    
    def _apply_element_type_bonus(self, candidate: MarkupLMMatchResult, 
                                 parsed_intent: ParsedIntent) -> float:
        """Apply element type bonuses to candidate score.
        
        Args:
            candidate: Candidate match result
            parsed_intent: Parsed user intent
            
        Returns:
            Bonus score
        """
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
    
    def _apply_hierarchy_bonus(self, candidate: MarkupLMMatchResult) -> float:
        """Apply hierarchy-based bonuses to candidate score.
        
        Args:
            candidate: Candidate match result
            
        Returns:
            Bonus score
        """
        bonus = 0.0
        
        # Bonus for elements with hierarchical context
        if candidate.hierarchy_path:
            bonus += 0.05
        
        # Bonus for elements closer to root
        if len(candidate.hierarchy_path) <= 3:
            bonus += 0.05
        
        # Bonus for elements in common UI patterns
        hierarchy_str = ' > '.join(candidate.hierarchy_path).lower()
        if any(pattern in hierarchy_str for pattern in ['nav', 'menu', 'button', 'form']):
            bonus += 0.05
        
        return bonus
    
    def _create_success_result(self, candidate: MarkupLMMatchResult, 
                              query: str, start_time: float) -> Dict[str, Any]:
        """Create success result.
        
        Args:
            candidate: Best candidate
            query: User query
            start_time: Query start time
            
        Returns:
            Success result dictionary
        """
        execution_time = (time.time() - start_time) * 1000
        
        return {
            'xpath': candidate.xpath,
            'selector': candidate.xpath,
            'element': candidate.element,
            'confidence': candidate.confidence,
            'strategy': candidate.strategy,
            'execution_time_ms': execution_time,
            'elements_found': 1,
            'reasons': candidate.reasons,
            'html_context': candidate.html_context,
            'hierarchy_path': candidate.hierarchy_path
        }
    
    def _create_no_match_result(self, query: str, start_time: float) -> Dict[str, Any]:
        """Create no match result.
        
        Args:
            query: User query
            start_time: Query start time
            
        Returns:
            No match result dictionary
        """
        execution_time = (time.time() - start_time) * 1000
        
        return {
            'xpath': None,
            'selector': None,
            'element': None,
            'confidence': 0.0,
            'strategy': 'markuplm-no-semantic',
            'execution_time_ms': execution_time,
            'elements_found': 0,
            'error': 'No matching elements found'
        }
    
    def _create_no_valid_result(self, query: str, start_time: float) -> Dict[str, Any]:
        """Create no valid result.
        
        Args:
            query: User query
            start_time: Query start time
            
        Returns:
            No valid result dictionary
        """
        execution_time = (time.time() - start_time) * 1000
        
        return {
            'xpath': None,
            'selector': None,
            'element': None,
            'confidence': 0.0,
            'strategy': 'markuplm-no-semantic',
            'execution_time_ms': execution_time,
            'elements_found': 0,
            'error': 'No valid candidates found'
        }
    
    def _create_error_result(self, query: str, error: str, start_time: float) -> Dict[str, Any]:
        """Create error result.
        
        Args:
            query: User query
            error: Error message
            start_time: Query start time
            
        Returns:
            Error result dictionary
        """
        execution_time = (time.time() - start_time) * 1000
        
        return {
            'xpath': None,
            'selector': None,
            'element': None,
            'confidence': 0.0,
            'strategy': 'markuplm-no-semantic',
            'execution_time_ms': execution_time,
            'elements_found': 0,
            'error': error
        }
    
    def is_markup_available(self) -> bool:
        """Check if MarkupLM is available.
        
        Returns:
            True if MarkupLM is available
        """
        return self.markup_available and self.markup_scorer is not None