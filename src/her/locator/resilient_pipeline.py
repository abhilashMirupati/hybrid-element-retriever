"""
Resilient Pipeline for Enhanced Error Handling

This module provides fallback strategies and error recovery for the no-semantic mode.
"""

from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from .intent_parser import IntentParser, ParsedIntent, IntentType
from .dom_target_binder import DOMTargetBinder, DOMMatch

log = logging.getLogger("her.resilient_pipeline")


class FallbackStrategy(Enum):
    """Fallback strategies for error recovery."""
    EXPLICIT_PARSING = "explicit_parsing"
    SIMPLE_TEXT_MATCHING = "simple_text_matching"
    ACCESSIBILITY_ONLY = "accessibility_only"
    SEMANTIC_FALLBACK = "semantic_fallback"


@dataclass
class FallbackResult:
    """Result of fallback strategy execution."""
    success: bool
    matches: List[DOMMatch]
    strategy_used: FallbackStrategy
    error_message: Optional[str] = None
    confidence: float = 0.0


class ResilientNoSemanticPipeline:
    """Resilient no-semantic pipeline with multiple fallback strategies."""
    
    def __init__(self, base_pipeline):
        """Initialize resilient pipeline.
        
        Args:
            base_pipeline: Base pipeline instance for fallback to semantic mode
        """
        self.base_pipeline = base_pipeline
        self.intent_parser = IntentParser()
        self.dom_target_binder = DOMTargetBinder()
        self.fallback_history = []  # Track fallback usage for learning
    
    def query_with_fallback(self, query: str, elements: List[Dict[str, Any]], 
                           top_k: int = 20, **kwargs) -> Dict[str, Any]:
        """Execute no-semantic query with multiple fallback strategies.
        
        Args:
            query: Query string
            elements: List of DOM elements
            top_k: Maximum number of results
            **kwargs: Additional arguments
            
        Returns:
            Query result with fallback information
        """
        strategies = [
            self._try_explicit_parsing,
            self._try_simple_text_matching,
            self._try_accessibility_only,
            self._try_semantic_fallback
        ]
        
        last_error = None
        
        for strategy_func in strategies:
            try:
                log.info(f"Trying strategy: {strategy_func.__name__}")
                result = strategy_func(query, elements, top_k, **kwargs)
                
                if result.success and result.matches:
                    log.info(f"Strategy {strategy_func.__name__} succeeded with {len(result.matches)} matches")
                    self._record_fallback_success(strategy_func.__name__, result.confidence)
                    return self._build_query_result(result, query, **kwargs)
                else:
                    log.warning(f"Strategy {strategy_func.__name__} failed: {result.error_message}")
                    last_error = result.error_message
                    
            except Exception as e:
                log.error(f"Strategy {strategy_func.__name__} crashed: {e}")
                last_error = str(e)
                continue
        
        # All strategies failed
        log.error(f"All fallback strategies failed. Last error: {last_error}")
        return {
            "results": [],
            "strategy": "no-semantic-failed",
            "confidence": 0.0,
            "error": last_error,
            "fallback_history": self.fallback_history
        }
    
    def _try_explicit_parsing(self, query: str, elements: List[Dict[str, Any]], 
                             top_k: int, **kwargs) -> FallbackResult:
        """Try explicit intent parsing strategy."""
        try:
            # Parse intent
            parsed_intent = self.intent_parser.parse_step(query)
            
            # Bind to DOM
            dom_matches = self.dom_target_binder.bind_target_to_dom(
                elements, parsed_intent.target_text, parsed_intent.intent.value
            )
            
            # Resolve by backend node ID
            resolved_matches = self._resolve_matches_by_backend_node_id(dom_matches)
            
            if resolved_matches:
                return FallbackResult(
                    success=True,
                    matches=resolved_matches[:top_k],
                    strategy_used=FallbackStrategy.EXPLICIT_PARSING,
                    confidence=parsed_intent.confidence
                )
            else:
                return FallbackResult(
                    success=False,
                    matches=[],
                    strategy_used=FallbackStrategy.EXPLICIT_PARSING,
                    error_message="No matches found with explicit parsing"
                )
                
        except Exception as e:
            return FallbackResult(
                success=False,
                matches=[],
                strategy_used=FallbackStrategy.EXPLICIT_PARSING,
                error_message=f"Explicit parsing failed: {e}"
            )
    
    def _try_simple_text_matching(self, query: str, elements: List[Dict[str, Any]], 
                                 top_k: int, **kwargs) -> FallbackResult:
        """Try simple text matching without intent parsing."""
        try:
            # Simple text matching without intent parsing
            matches = []
            normalized_query = query.lower().strip()
            
            for element in elements:
                if not self.dom_target_binder._is_element_visible(element):
                    continue
                
                # Check text content
                text = element.get('text', '').lower()
                if normalized_query in text:
                    backend_node_id = self.dom_target_binder._get_backend_node_id(element)
                    if backend_node_id:
                        match = DOMMatch(
                            element=element,
                            backend_node_id=backend_node_id,
                            match_type="simple_text",
                            matched_text=element.get('text', ''),
                            score=0.8,  # High score for simple matches
                            hierarchy_path=self.dom_target_binder._build_hierarchy_path(element),
                            canonical_descriptor=self.dom_target_binder._build_canonical_descriptor(element)
                        )
                        matches.append(match)
            
            if matches:
                return FallbackResult(
                    success=True,
                    matches=matches[:top_k],
                    strategy_used=FallbackStrategy.SIMPLE_TEXT_MATCHING,
                    confidence=0.8
                )
            else:
                return FallbackResult(
                    success=False,
                    matches=[],
                    strategy_used=FallbackStrategy.SIMPLE_TEXT_MATCHING,
                    error_message="No simple text matches found"
                )
                
        except Exception as e:
            return FallbackResult(
                success=False,
                matches=[],
                strategy_used=FallbackStrategy.SIMPLE_TEXT_MATCHING,
                error_message=f"Simple text matching failed: {e}"
            )
    
    def _try_accessibility_only(self, query: str, elements: List[Dict[str, Any]], 
                               top_k: int, **kwargs) -> FallbackResult:
        """Try accessibility-only matching."""
        try:
            # Extract accessibility elements
            ax_elements = []
            for element in elements:
                attrs = element.get('attributes', {})
                
                # Check for accessibility attributes
                has_ax_info = any(attr in attrs for attr in [
                    'aria-label', 'aria-labelledby', 'role', 'title', 'alt'
                ])
                
                if has_ax_info:
                    ax_element = {
                        'name': attrs.get('aria-label') or attrs.get('title') or attrs.get('alt', ''),
                        'role': attrs.get('role', ''),
                        'element': element
                    }
                    if ax_element['name'] or ax_element['role']:
                        ax_elements.append(ax_element)
            
            if not ax_elements:
                return FallbackResult(
                    success=False,
                    matches=[],
                    strategy_used=FallbackStrategy.ACCESSIBILITY_ONLY,
                    error_message="No accessibility elements found"
                )
            
            # Match against accessibility elements
            matches = []
            normalized_query = query.lower().strip()
            
            for ax_el in ax_elements:
                if (normalized_query in ax_el['name'].lower() or 
                    normalized_query in ax_el['role'].lower()):
                    
                    backend_node_id = self.dom_target_binder._get_backend_node_id(ax_el['element'])
                    if backend_node_id:
                        match = DOMMatch(
                            element=ax_el['element'],
                            backend_node_id=backend_node_id,
                            match_type="accessibility",
                            matched_text=ax_el['name'] or ax_el['role'],
                            score=0.7,  # Lower score for accessibility fallback
                            hierarchy_path=self.dom_target_binder._build_hierarchy_path(ax_el['element']),
                            canonical_descriptor=self.dom_target_binder._build_canonical_descriptor(ax_el['element'])
                        )
                        matches.append(match)
            
            if matches:
                return FallbackResult(
                    success=True,
                    matches=matches[:top_k],
                    strategy_used=FallbackStrategy.ACCESSIBILITY_ONLY,
                    confidence=0.7
                )
            else:
                return FallbackResult(
                    success=False,
                    matches=[],
                    strategy_used=FallbackStrategy.ACCESSIBILITY_ONLY,
                    error_message="No accessibility matches found"
                )
                
        except Exception as e:
            return FallbackResult(
                success=False,
                matches=[],
                strategy_used=FallbackStrategy.ACCESSIBILITY_ONLY,
                error_message=f"Accessibility matching failed: {e}"
            )
    
    def _try_semantic_fallback(self, query: str, elements: List[Dict[str, Any]], 
                              top_k: int, **kwargs) -> FallbackResult:
        """Try semantic mode as final fallback."""
        try:
            log.warning("Falling back to semantic mode")
            
            # Use base pipeline's semantic mode
            result = self.base_pipeline._query_semantic_mode(query, elements, top_k, **kwargs)
            
            if result.get('results'):
                # Convert semantic results to DOMMatch format
                matches = []
                for i, res in enumerate(result['results'][:top_k]):
                    element = res.get('meta', {})
                    if element:
                        match = DOMMatch(
                            element=element,
                            backend_node_id=f"semantic_{i}",
                            match_type="semantic_fallback",
                            matched_text=element.get('text', ''),
                            score=res.get('score', 0.5),
                            hierarchy_path="semantic",
                            canonical_descriptor="semantic_fallback"
                        )
                        matches.append(match)
                
                return FallbackResult(
                    success=True,
                    matches=matches,
                    strategy_used=FallbackStrategy.SEMANTIC_FALLBACK,
                    confidence=result.get('confidence', 0.5)
                )
            else:
                return FallbackResult(
                    success=False,
                    matches=[],
                    strategy_used=FallbackStrategy.SEMANTIC_FALLBACK,
                    error_message="Semantic mode also failed"
                )
                
        except Exception as e:
            return FallbackResult(
                success=False,
                matches=[],
                strategy_used=FallbackStrategy.SEMANTIC_FALLBACK,
                error_message=f"Semantic fallback failed: {e}"
            )
    
    def _resolve_matches_by_backend_node_id(self, dom_matches: List[DOMMatch]) -> List[DOMMatch]:
        """Resolve matches by backend node ID, removing duplicates."""
        if not dom_matches:
            return []
        
        # Group by backend node ID and keep the best match for each
        node_id_to_match = {}
        for match in dom_matches:
            node_id = match.backend_node_id
            if node_id not in node_id_to_match or match.score > node_id_to_match[node_id].score:
                node_id_to_match[node_id] = match
        
        resolved = list(node_id_to_match.values())
        resolved.sort(key=lambda m: m.score, reverse=True)
        
        return resolved
    
    def _build_query_result(self, fallback_result: FallbackResult, query: str, **kwargs) -> Dict[str, Any]:
        """Build final query result from fallback result."""
        results = []
        
        for match in fallback_result.matches:
            # Generate XPath for the element
            from ..utils.xpath_generator import generate_xpath_for_element
            xpath = generate_xpath_for_element(match.element)
            
            results.append({
                "selector": xpath,
                "score": float(match.score),
                "reasons": [f"fallback-{fallback_result.strategy_used.value}"],
                "meta": {
                    **match.element,
                    "matched_attribute": match.matched_text,
                    "matched_value": match.matched_text,
                    "mode": "no-semantic-resilient",
                    "fallback_strategy": fallback_result.strategy_used.value,
                    "backend_node_id": match.backend_node_id,
                    "canonical_descriptor": match.canonical_descriptor,
                    "hierarchy_path": match.hierarchy_path
                },
            })
        
        return {
            "results": results,
            "strategy": f"no-semantic-resilient-{fallback_result.strategy_used.value}",
            "confidence": fallback_result.confidence,
            "fallback_strategy": fallback_result.strategy_used.value,
            "fallback_history": self.fallback_history
        }
    
    def _record_fallback_success(self, strategy_name: str, confidence: float):
        """Record successful fallback for learning."""
        self.fallback_history.append({
            "strategy": strategy_name,
            "confidence": confidence,
            "timestamp": self._get_timestamp()
        })
        
        # Keep only last 100 entries
        if len(self.fallback_history) > 100:
            self.fallback_history = self.fallback_history[-100:]
    
    def _get_timestamp(self) -> float:
        """Get current timestamp."""
        import time
        return time.time()