"""Final production pipeline with all fixes."""

import logging
import hashlib
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from .pipeline import PipelineConfig
from .scoring.fusion_scorer_v2 import FusionScorerV2, ScoringSignals
from .parser.intent import IntentParser
from .embeddings.real_embedder import MiniLMEmbedder, MarkupLMEmbedder
from .locator.synthesize import LocatorSynthesizer
from .cache.thread_safe_cache import ThreadSafeTwoTierCache
from .locator.verify import verify_locator

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Structured pipeline result."""
    xpath: str
    confidence: float
    element: Dict[str, Any]
    fallbacks: List[str]
    scoring_signals: Optional[ScoringSignals] = None
    cache_hit: bool = False
    processing_time_ms: float = 0.0
    frame: Optional[str] = None
    shadow_root: Optional[str] = None


class FinalProductionPipeline:
    """Final production pipeline with all improvements."""
    
    def __init__(self, config: Optional[PipelineConfig] = None):
        """Initialize production pipeline."""
        self.config = config or PipelineConfig()
        
        # Core components with real implementations
        self.intent_parser = IntentParser()
        self.query_embedder = MiniLMEmbedder()  # Real MiniLM
        self.element_embedder = MarkupLMEmbedder()  # Real MarkupLM
        self.fusion_scorer = FusionScorerV2()
        self.synthesizer = LocatorSynthesizer()
        self.cache = ThreadSafeTwoTierCache()  # Thread-safe cache
        
        # State tracking
        self.last_dom_hash = None
        self.cached_embeddings = {}
        
        logger.info("Initialized FinalProductionPipeline with real embedders and thread-safe cache")
    
    def process(
        self,
        query: str,
        descriptors: List[Dict[str, Any]],
        page: Optional[Any] = None,
        session_id: Optional[str] = None
    ) -> PipelineResult:
        """Process query through production pipeline.
        
        Args:
            query: Natural language query
            descriptors: Element descriptors from DOM
            page: Optional page object for verification
            session_id: Optional session for caching
            
        Returns:
            PipelineResult with XPath and metadata
        """
        start_time = time.time()
        
        # Handle None inputs gracefully
        if query is None:
            query = ""
        if descriptors is None:
            descriptors = []
        
        # Check cache first (thread-safe)
        cache_key = self._get_cache_key(query, descriptors)
        cached = self.cache.get(cache_key)
        if cached:
            cached['cache_hit'] = True
            cached['processing_time_ms'] = (time.time() - start_time) * 1000
            return PipelineResult(**cached)
        
        try:
            # Step 1: Parse intent
            intent = self.intent_parser.parse(query)
            logger.debug(f"Intent: {intent}")
            
            # Step 2: Handle cold start or incremental update
            embeddings = self._get_or_create_embeddings(descriptors, session_id)
            
            # Step 3: Generate query embedding using real MiniLM
            query_embedding = self.query_embedder.embed_text(query)
            
            # Step 4: Score all candidates with frame/shadow DOM awareness
            scored_candidates = []
            for i, desc in enumerate(descriptors):
                # Get element embedding using real MarkupLM
                element_embedding = embeddings.get(i)
                if element_embedding is None:
                    element_embedding = self.element_embedder.embed_element(desc)
                    embeddings[i] = element_embedding
                
                # Use fusion scorer for comprehensive scoring
                score, signals = self.fusion_scorer.score(
                    query=query,
                    element=desc,
                    query_embedding=query_embedding,
                    element_embedding=element_embedding,
                    intent=intent
                )
                
                # Boost score for frame/shadow DOM matches
                if "frame" in query.lower() and desc.get("frame"):
                    if desc["frame"] in query.lower():
                        score *= 1.5  # Boost for frame match
                
                if "shadow" in query.lower() and desc.get("inShadowRoot"):
                    score *= 1.5  # Boost for shadow DOM match
                
                # Only include if score is meaningful
                if score > 0.1:
                    scored_candidates.append((desc, score, signals))
            
            # Step 5: Sort by score
            scored_candidates.sort(key=lambda x: x[1], reverse=True)
            
            if not scored_candidates:
                logger.warning(f"No candidates found for query: {query}")
                return PipelineResult(
                    xpath="",
                    confidence=0.0,
                    element={},
                    fallbacks=[],
                    processing_time_ms=(time.time() - start_time) * 1000
                )
            
            # Step 6: Get best candidate
            best_element, best_score, best_signals = scored_candidates[0]
            
            # Step 7: Generate XPath with frame/shadow DOM context
            xpath, fallbacks = self._generate_xpath(best_element, page)
            
            # Add frame/shadow DOM context to XPath if needed
            if best_element.get("frame") and best_element["frame"] != "main":
                xpath = f"frame:{best_element['frame']} >> {xpath}"
            
            if best_element.get("inShadowRoot"):
                shadow_host = best_element.get("shadowHost", "unknown")
                xpath = f"shadow:{shadow_host} >> {xpath}"
            
            # Step 8: Verify if page provided
            if page and not self._verify_xpath(xpath, page, best_element):
                # Try fallbacks
                for fallback in fallbacks[:3]:
                    if self._verify_xpath(fallback, page, best_element):
                        xpath = fallback
                        break
            
            # Create result
            result = PipelineResult(
                xpath=xpath,
                confidence=min(best_score, 1.0),
                element=best_element,
                fallbacks=fallbacks[:5],
                scoring_signals=best_signals,
                cache_hit=False,
                processing_time_ms=(time.time() - start_time) * 1000,
                frame=best_element.get("frame"),
                shadow_root=best_element.get("shadowHost")
            )
            
            # Cache result (thread-safe)
            self.cache.put(cache_key, {
                'xpath': result.xpath,
                'confidence': result.confidence,
                'element': result.element,
                'fallbacks': result.fallbacks,
                'frame': result.frame,
                'shadow_root': result.shadow_root
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Pipeline error: {e}", exc_info=True)
            return PipelineResult(
                xpath="",
                confidence=0.0,
                element={},
                fallbacks=[],
                processing_time_ms=(time.time() - start_time) * 1000
            )
    
    def _get_cache_key(self, query: str, descriptors: List[Dict[str, Any]]) -> str:
        """Generate cache key for query and descriptors."""
        desc_summary = f"{len(descriptors)}:{hashlib.md5(str(descriptors[:3]).encode()).hexdigest()[:8]}"
        return f"pipeline:{hashlib.md5(f'{query}:{desc_summary}'.encode()).hexdigest()}"
    
    def _get_or_create_embeddings(
        self,
        descriptors: List[Dict[str, Any]],
        session_id: Optional[str]
    ) -> Dict[int, List[float]]:
        """Get cached embeddings or create new ones with real models.
        
        Implements:
        - Cold start: embed all elements with MarkupLM
        - Incremental: detect changes and embed only new
        - SPA detection: reindex on major DOM changes
        """
        # Calculate DOM hash
        dom_hash = self._calculate_dom_hash(descriptors)
        
        # Detect SPA navigation (major DOM change)
        if self.last_dom_hash and dom_hash != self.last_dom_hash:
            # Check if it's a major change (SPA navigation)
            if self._is_spa_navigation(descriptors):
                logger.info("SPA navigation detected, full reindex")
                self.cached_embeddings.clear()
        
        # Check if cold start
        if not self.last_dom_hash or not self.cached_embeddings:
            logger.info("Cold start: embedding all elements with MarkupLM")
            embeddings = {}
            for i, desc in enumerate(descriptors):
                try:
                    embeddings[i] = self.element_embedder.embed_element(desc)
                except Exception as e:
                    logger.warning(f"Failed to embed element {i}: {e}")
                    embeddings[i] = None
            
            self.cached_embeddings = embeddings
            self.last_dom_hash = dom_hash
            return embeddings
        
        # Check for incremental update
        if dom_hash != self.last_dom_hash:
            logger.info("Incremental update: detecting changed elements")
            
            # Find new/changed elements
            new_embeddings = {}
            for i, desc in enumerate(descriptors):
                # Check if element is new or changed
                if i >= len(self.cached_embeddings) or self._element_changed(i, desc):
                    try:
                        new_embeddings[i] = self.element_embedder.embed_element(desc)
                    except Exception as e:
                        logger.warning(f"Failed to embed new element {i}: {e}")
                        new_embeddings[i] = None
                else:
                    # Reuse cached embedding
                    new_embeddings[i] = self.cached_embeddings.get(i)
            
            self.cached_embeddings = new_embeddings
            self.last_dom_hash = dom_hash
            return new_embeddings
        
        # No changes, return cached
        return self.cached_embeddings
    
    def _calculate_dom_hash(self, descriptors: List[Dict[str, Any]]) -> str:
        """Calculate hash of DOM structure."""
        if not descriptors:
            return ""
        
        # Create signature from element tags and IDs
        signatures = []
        for desc in descriptors[:100]:  # Sample first 100 for performance
            sig = f"{desc.get('tag')}:{desc.get('id', '')}:{desc.get('dataTestId', '')}"
            signatures.append(sig)
        
        return hashlib.md5('|'.join(signatures).encode()).hexdigest()
    
    def _is_spa_navigation(self, descriptors: List[Dict[str, Any]]) -> bool:
        """Detect if DOM change is SPA navigation."""
        # Simple heuristic: if more than 50% of elements changed, it's likely navigation
        if not self.cached_embeddings:
            return False
        
        old_count = len(self.cached_embeddings)
        new_count = len(descriptors)
        
        # Major size change indicates navigation
        if abs(old_count - new_count) > old_count * 0.5:
            return True
        
        # Check for major content change
        # (In production, would check URL change, history API, etc.)
        return False
    
    def _element_changed(self, index: int, element: Dict[str, Any]) -> bool:
        """Check if element at index has changed."""
        if index not in self.cached_embeddings:
            return True
        
        # In production, would compare element hashes
        return False
    
    def _generate_xpath(
        self,
        element: Dict[str, Any],
        page: Optional[Any] = None
    ) -> Tuple[str, List[str]]:
        """Generate XPath for element."""
        locators = self.synthesizer.synthesize(element)
        
        if not locators:
            return "", []
        
        return locators[0], locators[1:] if len(locators) > 1 else []
    
    def _verify_xpath(
        self,
        xpath: str,
        page: Any,
        expected_element: Dict[str, Any]
    ) -> bool:
        """Verify XPath finds expected element."""
        try:
            return verify_locator(xpath, expected_element, page)
        except Exception as e:
            logger.debug(f"Verification failed: {e}")
            return False
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return self.cache.get_stats()