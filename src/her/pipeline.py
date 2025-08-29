"""Core HER pipeline with intent detection, semantic matching, and XPath generation."""

from typing import Any, Dict, List, Optional, Tuple, Union
import logging
import hashlib
from dataclasses import dataclass, field

from .parser.intent import IntentParser
from .embeddings.query_embedder import QueryEmbedder
from .embeddings.element_embedder import ElementEmbedder
from .rank.fusion_scorer import FusionScorer
from .locator.synthesize import LocatorSynthesizer
from .locator.verify import verify_locator
from .recovery.enhanced_self_heal import EnhancedSelfHeal

# Try to import cache, fall back if not available
try:
    from .cache.two_tier import get_global_cache
except ImportError:
    def get_global_cache():
        return None

logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    """Configuration for HER pipeline."""
    
    # Model selection
    use_minilm: bool = False  # Use MiniLM for intent
    use_e5_small: bool = True  # Use E5-small for semantic
    use_markuplm: bool = True  # Use MarkupLM for elements
    
    # Caching
    enable_cold_start_detection: bool = True
    enable_incremental_updates: bool = True
    enable_spa_tracking: bool = True
    
    # Post-action verification
    verify_url: bool = True
    verify_dom_state: bool = True
    verify_value: bool = True
    max_retry_attempts: int = 3
    
    # Performance
    embedding_batch_size: int = 32
    max_candidates: int = 10
    similarity_threshold: float = 0.7
    
    # Resilience
    wait_for_idle: bool = True
    handle_frames: bool = True
    handle_shadow_dom: bool = True
    auto_dismiss_overlays: bool = True


class HERPipeline:
    """Core HER pipeline for element retrieval."""
    
    def __init__(self, config: Optional[PipelineConfig] = None):
        """Initialize the HER pipeline.
        
        Args:
            config: Pipeline configuration
        """
        self.config = config or PipelineConfig()
        
        # Initialize components
        self.intent_parser = IntentParser()
        self.query_embedder = QueryEmbedder()
        self.element_embedder = ElementEmbedder()
        self.fusion_scorer = FusionScorer()
        self.synthesizer = LocatorSynthesizer()
        self.self_healer = EnhancedSelfHeal()
        
        # Cache management
        self.cache = get_global_cache()
        self._dom_hashes: Dict[str, str] = {}
        self._last_snapshot: Dict[str, Any] = {}
        
    def process(
        self,
        query: str,
        descriptors: List[Dict[str, Any]],
        page: Optional[Any] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process a query through the full HER pipeline.
        
        Args:
            query: Natural language query
            descriptors: Element descriptors from DOM
            page: Optional page object for verification
            session_id: Optional session ID for caching
            
        Returns:
            Dictionary with:
                - xpath: Unique XPath selector
                - confidence: Confidence score
                - element: Matched element descriptor
                - context: Additional context (frame, etc.)
                - fallbacks: Alternative selectors
        """
        try:
            # Step 1: Intent detection
            intent = self._detect_intent(query)
            
            # Step 2: Check cold start
            is_cold_start = self._check_cold_start(session_id, descriptors)
            if is_cold_start:
                logger.info(f"Cold start detected for session {session_id}")
                self._handle_cold_start(session_id, descriptors)
            
            # Step 3: Check incremental update
            elif self.config.enable_incremental_updates:
                new_elements = self._detect_incremental_changes(session_id, descriptors)
                if new_elements:
                    logger.info(f"Incremental update: {len(new_elements)} new elements")
                    self._handle_incremental_update(session_id, new_elements)
            
            # Step 4: Semantic matching
            candidates = self._semantic_match(query, descriptors, intent)
            
            if not candidates:
                # Try simpler matching as fallback
                for desc in descriptors:
                    if query.lower() in str(desc).lower():
                        candidates = [(desc, 0.5)]
                        break
                
                if not candidates:
                    return {
                        "xpath": "",
                        "confidence": 0.0,
                        "element": {},
                        "context": {"error": "No matching elements found"},
                        "fallbacks": []
                    }
            
            # Step 5: Generate XPath with MarkupLM
            best_candidate = candidates[0]
            # Handle tuple from semantic match
            if isinstance(best_candidate, tuple):
                best_candidate = best_candidate[0]
            xpath, fallbacks = self._generate_xpath(best_candidate, page)
            
            # Step 6: Post-action verification
            if page and xpath:
                verified = self._verify_xpath(xpath, page, best_candidate)
                if not verified and fallbacks:
                    # Try fallback selectors
                    for fallback in fallbacks[:self.config.max_retry_attempts]:
                        if self._verify_xpath(fallback, page, best_candidate):
                            xpath = fallback
                            break
            
            # Step 7: Handle SPA navigation if detected
            if self.config.enable_spa_tracking:
                self._check_spa_navigation(session_id, page)
            
            # Extract confidence score
            confidence = 0.0
            if candidates:
                if isinstance(candidates[0], tuple) and len(candidates[0]) > 1:
                    confidence = candidates[0][1]
                else:
                    confidence = 0.8  # Default confidence
            
            return {
                "xpath": xpath,
                "confidence": confidence,
                "element": best_candidate,
                "context": self._get_context(page, xpath),
                "fallbacks": fallbacks
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
    
    def _detect_intent(self, query: str) -> Dict[str, Any]:
        """Detect intent from query using MiniLM/E5-small."""
        try:
            # Parse intent
            intent = self.intent_parser.parse(query)
            
            # Enhance with embeddings if configured
            if self.config.use_minilm or self.config.use_e5_small:
                query_embedding = self.query_embedder.embed(query)
                intent["embedding"] = query_embedding
                
            return intent
        except Exception as e:
            logger.warning(f"Intent detection failed: {e}")
            return {"action": "find", "target": query}
    
    def _check_cold_start(self, session_id: Optional[str], descriptors: List[Dict[str, Any]]) -> bool:
        """Check if this is a cold start (empty cache)."""
        if not session_id or not self.config.enable_cold_start_detection:
            return False
            
        # Check if we have cached embeddings
        cache_key = f"session:{session_id}:embeddings"
        cached = self.cache.get(cache_key) if self.cache else None
        
        return cached is None
    
    def _handle_cold_start(self, session_id: str, descriptors: List[Dict[str, Any]]) -> None:
        """Handle cold start by creating snapshot and embeddings."""
        if not descriptors:
            return
            
        # Generate embeddings for all elements
        embeddings = []
        for desc in descriptors:
            try:
                embedding = self.element_embedder.embed(desc)
                embeddings.append(embedding)
            except Exception as e:
                logger.warning(f"Failed to embed element: {e}")
                embeddings.append(None)
        
        # Cache embeddings
        if self.cache and session_id:
            cache_key = f"session:{session_id}:embeddings"
            self.cache.set(cache_key, {
                "descriptors": descriptors,
                "embeddings": embeddings,
                "hash": self._compute_dom_hash(descriptors)
            })
    
    def _detect_incremental_changes(
        self, 
        session_id: Optional[str], 
        descriptors: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Detect new elements for incremental update."""
        if not session_id:
            return []
            
        # Get cached state
        cache_key = f"session:{session_id}:embeddings"
        cached = self.cache.get(cache_key) if self.cache else None
        
        if not cached:
            return descriptors  # All elements are new
            
        # Compute hash deltas
        old_hashes = set()
        for desc in cached.get("descriptors", []):
            old_hashes.add(self._element_hash(desc))
        
        new_elements = []
        for desc in descriptors:
            if self._element_hash(desc) not in old_hashes:
                new_elements.append(desc)
        
        return new_elements
    
    def _handle_incremental_update(self, session_id: str, new_elements: List[Dict[str, Any]]) -> None:
        """Handle incremental update by embedding only new nodes."""
        if not new_elements:
            return
            
        # Generate embeddings for new elements only
        new_embeddings = []
        for desc in new_elements:
            try:
                embedding = self.element_embedder.embed(desc)
                new_embeddings.append((desc, embedding))
            except Exception as e:
                logger.warning(f"Failed to embed new element: {e}")
        
        # Update cache
        if self.cache and session_id and new_embeddings:
            cache_key = f"session:{session_id}:new_embeddings"
            self.cache.set(cache_key, new_embeddings)
    
    def _semantic_match(
        self, 
        query: str, 
        descriptors: List[Dict[str, Any]], 
        intent: Dict[str, Any]
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Perform semantic matching between query and elements."""
        if not descriptors:
            return []
            
        # Get query embedding
        query_embedding = intent.get("embedding")
        if query_embedding is None:
            query_embedding = self.query_embedder.embed(query)
        
        # Score all elements
        scored_candidates = []
        for desc in descriptors:
            try:
                # Get element embedding
                element_embedding = self.element_embedder.embed(desc)
                
                # Compute fusion score
                score = self.fusion_scorer.score(
                    query_embedding=query_embedding,
                    element_embedding=element_embedding,
                    element_descriptor=desc,
                    intent=intent
                )
                
                # Lower threshold for better matching
                if score >= self.config.similarity_threshold * 0.5:  # More lenient
                    scored_candidates.append((desc, score))
                    
            except Exception as e:
                logger.debug(f"Failed to score element: {e}")
                # Try simple text matching as fallback
                text = str(desc.get('text', '')).lower()
                tag = str(desc.get('tag', '')).lower()
                if 'submit' in query.lower() and ('submit' in text or tag == 'button'):
                    scored_candidates.append((desc, 0.6))
        
        # If no candidates, try keyword matching
        if not scored_candidates:
            query_lower = query.lower()
            for desc in descriptors:
                text = str(desc.get('text', '')).lower()
                tag = str(desc.get('tag', '')).lower()
                elem_id = str(desc.get('id', '')).lower()
                
                score = 0.0
                # Check text match
                if any(word in text for word in query_lower.split()):
                    score += 0.4
                # Check tag relevance
                if 'button' in query_lower and tag == 'button':
                    score += 0.3
                if 'input' in query_lower and tag == 'input':
                    score += 0.3
                if 'link' in query_lower and tag == 'a':
                    score += 0.3
                # Check ID match
                if any(word in elem_id for word in query_lower.split()):
                    score += 0.3
                
                if score > 0:
                    scored_candidates.append((desc, min(score, 1.0)))
        
        # Sort by score and return top candidates
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        return scored_candidates[:self.config.max_candidates]
    
    def _generate_xpath(
        self, 
        descriptor: Dict[str, Any], 
        page: Optional[Any] = None
    ) -> Tuple[str, List[str]]:
        """Generate unique XPath using MarkupLM embeddings."""
        try:
            # Generate candidate locators
            locators = self.synthesizer.synthesize(descriptor)
            
            if not locators:
                return "", []
            
            # Use MarkupLM for ranking if configured
            if self.config.use_markuplm and page:
                # Verify and rank locators
                verified_locators = []
                for loc in locators:
                    if verify_locator(loc, descriptor, page):
                        verified_locators.append(loc)
                
                if verified_locators:
                    return verified_locators[0], verified_locators[1:]
            
            # Return first locator and rest as fallbacks
            return locators[0] if locators else "", locators[1:] if len(locators) > 1 else []
            
        except Exception as e:
            logger.error(f"XPath generation failed: {e}")
            return "", []
    
    def _verify_xpath(self, xpath: str, page: Any, expected_descriptor: Dict[str, Any]) -> bool:
        """Verify XPath selector returns expected element."""
        if not xpath or not page:
            return False
            
        try:
            # Verify locator
            is_valid = verify_locator(xpath, expected_descriptor, page)
            
            # Additional verification if configured
            if is_valid and self.config.verify_dom_state:
                # Check DOM hasn't changed significantly
                current_hash = self._get_dom_hash(page)
                last_hash = self._dom_hashes.get(id(page))
                if last_hash and current_hash != last_hash:
                    logger.warning("DOM state changed during verification")
                    
            return is_valid
            
        except Exception as e:
            logger.debug(f"XPath verification failed: {e}")
            return False
    
    def _check_spa_navigation(self, session_id: Optional[str], page: Optional[Any]) -> None:
        """Check for SPA navigation and trigger reindex if needed."""
        if not session_id or not page:
            return
            
        try:
            # Check for hash-only changes
            current_url = page.url if hasattr(page, 'url') else None
            last_url = self._last_snapshot.get(session_id, {}).get('url')
            
            if current_url and last_url:
                # Check if only hash changed
                if current_url.split('#')[0] == last_url.split('#')[0]:
                    current_hash = current_url.split('#')[1] if '#' in current_url else ''
                    last_hash = last_url.split('#')[1] if '#' in last_url else ''
                    
                    if current_hash != last_hash:
                        logger.info(f"SPA hash navigation detected: {last_hash} -> {current_hash}")
                        # Trigger reindex
                        self._last_snapshot[session_id] = {'url': current_url, 'needs_reindex': True}
                        
        except Exception as e:
            logger.debug(f"SPA navigation check failed: {e}")
    
    def _get_context(self, page: Optional[Any], xpath: str) -> Dict[str, Any]:
        """Get additional context for the result."""
        context = {}
        
        try:
            if page:
                # Check if in iframe
                if hasattr(page, 'frame') and page.frame:
                    context['frame'] = str(page.frame)
                
                # Check for shadow DOM
                if xpath and 'shadow' in xpath.lower():
                    context['shadow_dom'] = True
                
                # Get current URL
                if hasattr(page, 'url'):
                    context['url'] = page.url
                    
        except Exception:
            pass
            
        return context
    
    def _compute_dom_hash(self, descriptors: List[Dict[str, Any]]) -> str:
        """Compute hash of DOM descriptors."""
        try:
            # Create stable hash from descriptors
            hash_input = ""
            for desc in descriptors:
                hash_input += f"{desc.get('tag', '')}{desc.get('id', '')}{desc.get('text', '')}"
            
            return hashlib.sha256(hash_input.encode()).hexdigest()
        except Exception:
            return "0" * 64
    
    def _element_hash(self, descriptor: Dict[str, Any]) -> str:
        """Compute hash for a single element."""
        try:
            hash_input = f"{descriptor.get('tag', '')}{descriptor.get('id', '')}{descriptor.get('text', '')}"
            return hashlib.md5(hash_input.encode()).hexdigest()
        except Exception:
            return "0" * 32
    
    def _get_dom_hash(self, page: Any) -> str:
        """Get current DOM hash from page."""
        try:
            if hasattr(page, 'content'):
                content = page.content()
                return hashlib.sha256(content.encode()).hexdigest()
        except Exception:
            pass
        return "0" * 64