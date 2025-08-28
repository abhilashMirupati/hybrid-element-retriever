"""Main CLI API with full integration of all HER components."""

from __future__ import annotations
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import asdict
from playwright.sync_api import sync_playwright, Page, Browser

# Core components
from .parser.intent import IntentParser
from .session.manager import SessionManager
from .bridge.cdp_bridge import capture_complete_snapshot
from .descriptors.merge import merge_dom_ax
from .embeddings.query_embedder import QueryEmbedder
from .embeddings.element_embedder import ElementEmbedder
from .rank.fusion_scorer import FusionScorer
from .locator.synthesize import LocatorSynthesizer
from .locator.verify import verify_locator
from .executor.actions import ActionError, click, fill, check, wait_for_idle
from .recovery.enhanced_self_heal import EnhancedSelfHeal
from .cache.two_tier import get_global_cache
from .utils import truncate_text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class QueryResult:
    """Result from element query."""
    
    def __init__(self, elements: List[Dict[str, Any]]):
        self.elements = elements
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "ok": len(self.elements) > 0,
            "count": len(self.elements),
            "elements": self.elements[:10]  # Limit to top 10
        }


class ActionResult:
    """Result from action execution."""
    
    def __init__(self, success: bool, locator: str = "", error: str = "", details: Dict = None):
        self.success = success
        self.locator = locator
        self.error = error
        self.details = details or {}
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "status": "success" if self.success else "failed",
            "locator": self.locator,
            "error": self.error,
            "details": self.details
        }


class HybridClient:
    """Main client for HER with full component integration."""
    
    def __init__(
        self,
        headless: bool = True,
        auto_index: bool = True,
        enable_self_heal: bool = True,
        enable_cache: bool = True,
        log_level: str = "INFO"
    ):
        """Initialize HER client with all components.
        
        Args:
            headless: Run browser in headless mode
            auto_index: Automatically index pages
            enable_self_heal: Enable self-healing locators
            enable_cache: Enable embedding cache
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        """
        # Set logging level
        logging.getLogger("her").setLevel(getattr(logging, log_level.upper()))
        
        # Core configuration
        self.headless = headless
        self.auto_index = auto_index
        self.enable_self_heal = enable_self_heal
        self.enable_cache = enable_cache
        
        # Initialize components
        self.intent_parser = IntentParser()
        self.session_manager = SessionManager(
            auto_index=auto_index,
            reindex_on_change=True,
            reindex_on_failure=True
        )
        self.query_embedder = QueryEmbedder()
        self.element_embedder = ElementEmbedder()
        self.fusion_scorer = FusionScorer()
        self.locator_synthesizer = LocatorSynthesizer()
        self.self_healer = EnhancedSelfHeal() if enable_self_heal else None
        
        # Browser management
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.session_id: Optional[str] = None
        
        logger.info(f"HybridClient initialized (headless={headless}, auto_index={auto_index})")
    
    def _ensure_browser(self) -> Page:
        """Ensure browser and page are initialized."""
        if not self.playwright:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=self.headless)
            logger.debug("Browser launched")
        
        if not self.page:
            self.page = self.browser.new_page()
            self.session_id = f"session_{id(self.page)}"
            
            # Create session with auto-indexing
            self.session_manager.create_session(
                self.session_id,
                self.page,
                auto_index=self.auto_index
            )
            logger.debug(f"Page created with session {self.session_id}")
        
        return self.page
    
    def query(self, phrase: str, url: Optional[str] = None) -> Dict:
        """Query for elements matching a natural language phrase.
        
        Args:
            phrase: Natural language description of elements
            url: Optional URL to navigate to first
            
        Returns:
            Dictionary with query results
        """
        try:
            logger.info(f"Query: '{phrase}' at {url or 'current page'}")
            
            # Ensure browser is ready
            page = self._ensure_browser()
            
            # Navigate if URL provided
            if url:
                page.goto(url)
                wait_for_idle(page)
                logger.debug(f"Navigated to {url}")
            
            # Get session
            session = self.session_manager.get_session(self.session_id)
            if not session:
                raise RuntimeError("Session not found")
            
            # Check if we need to index/reindex
            if self.session_manager.should_reindex(self.session_id, page):
                self.session_manager._index_page(self.session_id, page)
            
            # Get query embedding
            query_embedding = self.query_embedder.embed(phrase)
            logger.debug(f"Query embedded: shape={query_embedding.shape}")
            
            # Score all indexed elements
            candidates = []
            for desc in session.indexed_descriptors:
                # Calculate semantic similarity
                element_embedding = self.element_embedder.embed(desc)
                semantic_score = float(np.dot(query_embedding, element_embedding))
                
                # Get promotion score from database
                promotion_score = 0.0
                if desc.get("xpath"):
                    # Check promotion database for this XPath
                    promotion_score = self._get_promotion_score(desc["xpath"])
                
                # Calculate fusion score
                fusion_score = self.fusion_scorer.score(
                    semantic=semantic_score,
                    heuristic=self._calculate_heuristic_score(desc, phrase),
                    promotion=promotion_score
                )
                
                # Generate locators
                locators = self.locator_synthesizer.synthesize(desc)
                
                # Add candidate
                candidates.append({
                    "descriptor": desc,
                    "score": fusion_score,
                    "semantic": semantic_score,
                    "locators": locators,
                    "selector": locators[0]["selector"] if locators else "",
                    "strategy": locators[0]["strategy"] if locators else "xpath"
                })
            
            # Sort by score
            candidates.sort(key=lambda x: x["score"], reverse=True)
            logger.debug(f"Found {len(candidates)} candidates")
            
            # Format results
            elements = []
            for candidate in candidates[:10]:  # Top 10
                # Verify locator works
                verification = verify_locator(
                    page,
                    candidate["selector"],
                    strategy=candidate["strategy"],
                    require_unique=True
                )
                
                if verification and verification.ok:
                    elements.append({
                        "selector": candidate["selector"],
                        "strategy": candidate["strategy"],
                        "score": candidate["score"],
                        "element": {
                            "tag": candidate["descriptor"].get("tag", ""),
                            "text": truncate_text(candidate["descriptor"].get("text", ""), 100),
                            "id": candidate["descriptor"].get("id", ""),
                            "classes": candidate["descriptor"].get("classes", []),
                            "role": candidate["descriptor"].get("role", "")
                        }
                    })
            
            logger.info(f"Query returned {len(elements)} verified elements")
            
            return QueryResult(elements).to_dict()
            
        except Exception as e:
            logger.error(f"Query failed: {e}", exc_info=True)
            return {
                "ok": False,
                "count": 0,
                "elements": [],
                "error": str(e)
            }
    
    def act(self, step: str, url: Optional[str] = None) -> Dict:
        """Execute a natural language action.
        
        Args:
            step: Natural language action description
            url: Optional URL to navigate to first
            
        Returns:
            Dictionary with action result
        """
        try:
            logger.info(f"Act: '{step}' at {url or 'current page'}")
            
            # Parse intent
            intent = self.intent_parser.parse(step)
            logger.debug(f"Parsed intent: action={intent.action}, target={intent.target_phrase}")
            
            # Query for target element
            query_result = self.query(intent.target_phrase, url)
            
            if not query_result.get("ok") or not query_result.get("elements"):
                raise ActionError(f"No elements found for: {intent.target_phrase}")
            
            # Get best element
            best_element = query_result["elements"][0]
            locator = best_element["selector"]
            strategy = best_element["strategy"]
            
            logger.debug(f"Using locator: {locator} (strategy={strategy})")
            
            # Ensure browser
            page = self._ensure_browser()
            
            # Execute action with self-healing
            success = False
            error_msg = ""
            
            try:
                # Find element
                if strategy == "css":
                    element = page.query_selector(locator)
                elif strategy == "xpath":
                    element = page.query_selector(f"xpath={locator}")
                else:
                    element = page.locator(locator).first
                
                if not element:
                    raise ActionError(f"Element not found: {locator}")
                
                # Execute action based on type
                if intent.action == "click":
                    click(element)
                elif intent.action in ["type", "fill"]:
                    fill(element, intent.args or "")
                elif intent.action == "check":
                    check(element, True)
                elif intent.action == "select":
                    element.select_option(intent.args or "")
                else:
                    # Default to click
                    click(element)
                
                success = True
                logger.info(f"Action executed successfully: {intent.action}")
                
                # Promote successful locator
                if success:
                    self._promote_locator(locator)
                
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"Action failed: {e}")
                
                # Try self-healing if enabled
                if self.enable_self_heal and self.self_healer:
                    logger.info("Attempting self-heal...")
                    healed_result = self.self_healer.heal_and_execute(
                        page=page,
                        primary_locator=locator,
                        action=intent.action,
                        args=intent.args
                    )
                    
                    if healed_result["success"]:
                        success = True
                        locator = healed_result["used_locator"]
                        error_msg = ""
                        logger.info(f"Self-heal successful with: {locator}")
            
            return ActionResult(
                success=success,
                locator=locator,
                error=error_msg,
                details={
                    "action": intent.action,
                    "target": intent.target_phrase,
                    "confidence": best_element["score"]
                }
            ).to_dict()
            
        except Exception as e:
            logger.error(f"Act failed: {e}", exc_info=True)
            return ActionResult(
                success=False,
                error=str(e)
            ).to_dict()
    
    def close(self):
        """Close browser and clean up resources."""
        try:
            if self.page:
                self.page.close()
                self.page = None
            
            if self.browser:
                self.browser.close()
                self.browser = None
            
            if self.playwright:
                self.playwright.stop()
                self.playwright = None
            
            # Clean up session
            if self.session_id:
                self.session_manager.destroy_session(self.session_id)
                self.session_id = None
            
            logger.info("Client closed")
            
        except Exception as e:
            logger.error(f"Error closing client: {e}")
    
    def _calculate_heuristic_score(self, descriptor: Dict, phrase: str) -> float:
        """Calculate heuristic score for element matching."""
        score = 0.0
        phrase_lower = phrase.lower()
        
        # Text matching
        if "text" in descriptor:
            text_lower = descriptor["text"].lower()
            if phrase_lower in text_lower:
                score += 0.5
            elif any(word in text_lower for word in phrase_lower.split()):
                score += 0.3
        
        # ID matching
        if "id" in descriptor and descriptor["id"]:
            if phrase_lower in descriptor["id"].lower():
                score += 0.3
        
        # Class matching
        if "classes" in descriptor:
            for cls in descriptor["classes"]:
                if phrase_lower in cls.lower():
                    score += 0.2
                    break
        
        # Role matching
        if "role" in descriptor and descriptor["role"]:
            if phrase_lower in descriptor["role"].lower():
                score += 0.3
        
        # Label matching
        if "label" in descriptor and descriptor["label"]:
            if phrase_lower in descriptor["label"].lower():
                score += 0.4
        
        return min(1.0, score)
    
    def _get_promotion_score(self, locator: str) -> float:
        """Get promotion score from database."""
        try:
            from .recovery.promotion import get_promotion_score
            return get_promotion_score(locator)
        except Exception:
            return 0.0
    
    def _promote_locator(self, locator: str):
        """Promote successful locator."""
        try:
            from .recovery.promotion import promote_locator
            promote_locator(locator)
        except Exception as e:
            logger.debug(f"Failed to promote locator: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Import numpy for embeddings
try:
    import numpy as np
except ImportError:
    logger.warning("NumPy not available, some features may not work")
    np = None


def _strict_json(obj: Any) -> str:
    """Convert object to strict JSON without None values."""
    def remove_none(d):
        if isinstance(d, dict):
            return {k: remove_none(v) for k, v in d.items() if v is not None}
        elif isinstance(d, list):
            return [remove_none(item) for item in d]
        else:
            return d
    
    cleaned = remove_none(obj)
    return json.dumps(cleaned, ensure_ascii=False, separators=(",", ":"))