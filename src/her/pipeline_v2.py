"""Enhanced pipeline using intelligent matching instead of rules."""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from .pipeline import HERPipeline, PipelineConfig
from .matching.intelligent_matcher import IntelligentMatcher
from .locator.synthesize import LocatorSynthesizer

logger = logging.getLogger(__name__)


class HERPipelineV2(HERPipeline):
    """Enhanced pipeline with intelligent matching."""
    
    def __init__(self, config: Optional[PipelineConfig] = None):
        """Initialize enhanced pipeline.
        
        Args:
            config: Pipeline configuration
        """
        super().__init__(config)
        
        # Replace rule-based matcher with intelligent matcher
        self.intelligent_matcher = IntelligentMatcher()
    
    def _semantic_match(
        self,
        query: str,
        descriptors: List[Dict[str, Any]],
        intent: Dict[str, Any]
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Perform intelligent matching instead of rule-based.
        
        This completely replaces the rule-based _semantic_match and
        _calculate_match_score methods with intelligent, generalizable matching.
        
        Args:
            query: Natural language query
            descriptors: Element descriptors
            intent: Parsed intent
            
        Returns:
            List of (descriptor, score) tuples
        """
        # Use intelligent matcher
        candidates = self.intelligent_matcher.match(query, descriptors, intent)
        
        # If no candidates from intelligent matching, try embedding-based as fallback
        if not candidates and self.config.use_embeddings:
            try:
                # Get query embedding
                query_embedding = self.query_embedder.embed(query)
                
                # Score all elements using embeddings
                for desc in descriptors:
                    try:
                        element_embedding = self.element_embedder.embed(desc)
                        
                        # Compute similarity
                        score = self.fusion_scorer.score(
                            query_embedding=query_embedding,
                            element_embedding=element_embedding,
                            element_descriptor=desc,
                            intent=intent
                        )
                        
                        if score > self.config.similarity_threshold * 0.3:  # Lower threshold
                            candidates.append((desc, score))
                    except Exception as e:
                        logger.debug(f"Embedding scoring failed: {e}")
                
                # Sort by score
                candidates.sort(key=lambda x: x[1], reverse=True)
                
            except Exception as e:
                logger.warning(f"Embedding fallback failed: {e}")
        
        # Limit to max candidates
        return candidates[:self.config.max_candidates]
    
    def process(
        self,
        query: str,
        descriptors: List[Dict[str, Any]],
        page: Optional[Any] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process query with intelligent matching.
        
        Args:
            query: Natural language query
            descriptors: Element descriptors
            page: Optional page object
            session_id: Optional session ID
            
        Returns:
            Dictionary with xpath, confidence, element, etc.
        """
        try:
            # Step 1: Parse intent
            intent = self._detect_intent(query)
            
            # Step 2: Intelligent matching (replaces semantic match)
            candidates = self._semantic_match(query, descriptors, intent)
            
            if not candidates:
                logger.warning(f"No candidates found for query: {query}")
                return {
                    "xpath": "",
                    "confidence": 0.0,
                    "element": {},
                    "context": {"error": "No matching elements found"},
                    "fallbacks": []
                }
            
            # Step 3: Generate XPath for best candidate
            best_candidate = candidates[0][0] if isinstance(candidates[0], tuple) else candidates[0]
            confidence = candidates[0][1] if isinstance(candidates[0], tuple) else 0.8
            
            xpath, fallbacks = self._generate_xpath(best_candidate, page)
            
            # Step 4: Verify if page provided
            if page and self.config.enable_verification:
                verified = self._verify_xpath(xpath, page, best_candidate)
                if not verified and fallbacks:
                    # Try fallbacks
                    for fallback in fallbacks[:3]:
                        if self._verify_xpath(fallback, page, best_candidate):
                            xpath = fallback
                            break
            
            return {
                "xpath": xpath,
                "confidence": float(confidence),
                "element": best_candidate,
                "context": self._get_context(page, xpath) if page else {},
                "fallbacks": fallbacks[:5]  # Limit fallbacks
            }
            
        except Exception as e:
            logger.error(f"Pipeline error: {e}", exc_info=True)
            return {
                "xpath": "",
                "confidence": 0.0,
                "element": {},
                "context": {"error": str(e)},
                "fallbacks": []
            }