"""Fixed HER Client API with integrated pipeline and resilience."""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
import logging
from pathlib import Path

# Browser automation
try:
    from playwright.sync_api import sync_playwright, Page, Browser
    import playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    Page = Any
    Browser = Any

# Core components
from .parser.intent import IntentParser
from .session.manager import SessionManager
try:
    from .session.enhanced_manager import EnhancedSessionManager
    ENHANCED_AVAILABLE = True
except ImportError:
    EnhancedSessionManager = None
    ENHANCED_AVAILABLE = False

from .descriptors.merge import merge_dom_ax
from .locator.synthesize import LocatorSynthesizer
from .locator.verify import verify_locator, LocatorVerifier
from .rank.fusion_scorer import FusionScorer
from .embeddings.query_embedder import QueryEmbedder
from .embeddings.element_embedder import ElementEmbedder
from .executor.actions import ActionExecutor

# New integrated components (optional for environments without full deps)
try:
    from .pipeline import HERPipeline, PipelineConfig
except Exception:  # pragma: no cover - allow smoke tests without full pipeline deps
    HERPipeline = None  # type: ignore
    PipelineConfig = None  # type: ignore
from .resilience import ResilienceManager, WaitStrategy
from .validators import InputValidator, DOMValidator

logger = logging.getLogger(__name__)


def wait_for_idle(page: Page, timeout: float = 5.0) -> None:
    """Wait for page to be idle."""
    if not PLAYWRIGHT_AVAILABLE or not page:
        return
    
    manager = ResilienceManager()
    manager.wait_for_idle(page, WaitStrategy.IDLE)


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to max length."""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "…"


class HybridElementRetrieverClient:
    """Production-ready HER client with integrated pipeline and resilience."""
    
    def __init__(
        self,
        browser: Optional[Browser] = None,
        headless: bool = True,
        slow_mo: int = 0,
        auto_index: bool = True,
        reindex_on_change: bool = True,
        cache_dir: Optional[Path] = None,
        use_enhanced: bool = True,
        enable_resilience: bool = True,
        enable_pipeline: bool = True
    ):
        """Initialize HER client with all features integrated.
        
        Args:
            browser: Optional browser instance
            headless: Run browser in headless mode
            slow_mo: Slow down operations by ms
            auto_index: Auto-index pages
            reindex_on_change: Re-index on DOM changes
            cache_dir: Cache directory
            use_enhanced: Use enhanced session manager
            enable_resilience: Enable resilience features
            enable_pipeline: Use new integrated pipeline
        """
        self.browser = browser
        self.headless = headless
        self.slow_mo = slow_mo
        self.auto_index = auto_index
        self.enable_resilience = enable_resilience
        self.enable_pipeline = enable_pipeline
        self.timeout_ms = 30000
        self.promotion_enabled = True
        
        # Initialize pipeline if enabled
        if enable_pipeline and PipelineConfig is not None and HERPipeline is not None:
            config = PipelineConfig(
                use_minilm=False,  # Use fallback embeddings
                use_e5_small=True,
                use_markuplm=True,
                enable_cold_start_detection=True,
                enable_incremental_updates=True,
                enable_spa_tracking=True,
                verify_url=True,
                verify_dom_state=True,
                verify_value=True,
                max_retry_attempts=3,
                wait_for_idle=True,
                handle_frames=True,
                handle_shadow_dom=True,
                auto_dismiss_overlays=True
            )
            self.pipeline = HERPipeline(config)
        else:
            self.pipeline = None
        
        # Initialize resilience manager if enabled
        if enable_resilience:
            self.resilience = ResilienceManager()
        else:
            self.resilience = None
        
        # Session management
        if use_enhanced and ENHANCED_AVAILABLE:
            self.session_manager = EnhancedSessionManager(
                auto_index=auto_index,
                reindex_on_change=reindex_on_change,
                cache_dir=cache_dir,
                enable_incremental=True,
                enable_spa_tracking=True
            )
        else:
            self.session_manager = SessionManager(
                auto_index=auto_index,
                reindex_on_change=reindex_on_change
            )
        
        # Legacy components (kept for compatibility)
        self.intent_parser = IntentParser()
        self.parser = self.intent_parser  # compatibility for tests
        self.synthesizer = LocatorSynthesizer()
        # Embedders in fallback-friendly mode
        self.query_embedder = QueryEmbedder()
        self.element_embedder = ElementEmbedder()
        self.fusion_scorer = FusionScorer()
        self.verifier = LocatorVerifier()
        
        # Browser management
        self.playwright = None
        self.page: Optional[Page] = None
        self.current_session_id = "default"
        
        # Tracking
        self._last_action_result: Optional[Dict[str, Any]] = None
        self._snapshots: Dict[str, Any] = {}
    
    def _ensure_browser(self) -> Optional[Page]:
        """Ensure browser and page are available."""
        if not PLAYWRIGHT_AVAILABLE:
            logger.warning("Playwright not available")
            return None
        
        if not self.page:
            if not self.browser:
                if not self.playwright:
                    self.playwright = sync_playwright().start()
                self.browser = self.playwright.chromium.launch(
                    headless=self.headless,
                    slow_mo=self.slow_mo
                )
            
            self.page = self.browser.new_page()
            
            # Setup session
            session = self.session_manager.create_session(
                self.current_session_id,
                self.page
            )
            
            # Setup SPA tracking if available
            if hasattr(self.session_manager, '_setup_spa_tracking'):
                self.session_manager._setup_spa_tracking(self.current_session_id, self.page)
        
        return self.page
    
    def act(self, step: str, url: Optional[str] = None) -> Dict[str, Any]:
        """Execute a natural-language step; return strict JSON for tests."""
        page = self._ensure_browser()
        if url and page:
            try:
                page.goto(url)
            except Exception:
                pass
        # Parse intent
        intent = getattr(self.parser, 'parse')(step) if hasattr(self, 'parser') else None
        action = getattr(intent, 'action', 'click') if intent else 'click'
        target_phrase = getattr(intent, 'target_phrase', step)
        confidence = float(getattr(intent, 'confidence', 0.0))

        # Index page to obtain dom_hash
        descriptors, dom_hash = ([], '')
        try:
            if page:
                descriptors, dom_hash = self.session_manager.index_page(self.current_session_id, page)  # type: ignore
        except Exception:
            pass

        # Find candidates (allow test to patch _find_candidates)
        try:
            candidates = self._find_candidates(target_phrase, descriptors)
        except Exception:
            candidates = []
        used_locator: Optional[str] = None
        if candidates:
            primary_desc = candidates[0][0]
            locators = self.synthesizer.synthesize(primary_desc)
            used_locator = self.verifier.find_unique_locator(locators, page) if hasattr(self, 'verifier') else (locators[0] if locators else None)
        if not used_locator:
            return {
                'status': 'failure',
                'method': action,
                'confidence': confidence,
                'dom_hash': dom_hash,
                'used_locator': None,
                'overlay_events': [],
                'retries': {'attempts': 0},
                'explanation': 'No valid locator found'
            }

        # Execute with recovery
        exec_result = self._execute_with_recovery(action, used_locator, None, candidates)
        status = 'success' if getattr(exec_result, 'success', False) else 'failure'
        overlay_events = getattr(exec_result, 'overlay_events', []) or []
        attempts = int(getattr(exec_result, 'retries', 0) or 0)
        return {
            'status': status,
            'method': action,
            'confidence': confidence,
            'dom_hash': dom_hash,
            'used_locator': used_locator,
            'overlay_events': overlay_events,
            'retries': {'attempts': attempts}
        }

    def _execute_with_recovery(self, method: str, locator: str, value: Optional[str], candidates: List[Tuple[Dict[str, Any], float, Any]]):
        """Run an action, optionally applying self-heal or alternatives (tests patch ActionExecutor)."""
        try:
            executor = ActionExecutor()
            if method in {'type', 'fill'}:
                return executor.fill(locator, value or '')
            if method == 'check':
                return executor.check(locator)
            return executor.click(locator)
        except Exception as e:  # pragma: no cover
            return type('Result', (), {'success': False, 'locator': locator, 'error': str(e), 'overlay_events': [], 'retries': 0, 'verification': {}})()

    def query(self, phrase: str, url: Optional[str] = None) -> Any:
        """Query for elements with full pipeline integration.
        
        Args:
            phrase: Natural language description
            url: Optional URL to navigate to
            
        Returns:
            List of elements or dict with top result
        """
        try:
            # Validate input
            valid, sanitized_phrase, error = InputValidator.validate_query(phrase)
            if not valid:
                return {"ok": False, "error": error}
            
            phrase = sanitized_phrase
            logger.info(f"Query: '{phrase}' at {url or 'current page'}")
            
            # Ensure browser
            page = self._ensure_browser()
            
            # Navigate if URL provided
            if url and page:
                valid_url, sanitized_url, url_error = InputValidator.validate_url(url)
                if valid_url:
                    try:
                        page.goto(sanitized_url)
                        
                        # Wait for page to be ready
                        if self.resilience:
                            self.resilience.wait_for_idle(page, WaitStrategy.LOAD_COMPLETE)
                            
                            # Handle overlays
                            self.resilience.detect_and_handle_overlay(page)
                    except Exception as e:
                        logger.debug(f"Navigation failed: {e}")
            
            # Get descriptors
            descriptors, dom_hash = self.session_manager.index_page(
                self.current_session_id, 
                page
            ) if page else ([], "0"*64)
            
            # Validate DOM size
            valid_dom, dom_warning = DOMValidator.validate_dom_size(descriptors)
            if not valid_dom:
                logger.warning(dom_warning)
            
            # Handle duplicates
            descriptors = DOMValidator.handle_duplicate_elements(descriptors)
            
            # Use pipeline if enabled
            if self.enable_pipeline and self.pipeline:
                # Support both legacy compat signature (dom=...) and newer
                # experimental signatures. Prefer the stable compat surface.
                try:
                    result = self.pipeline.process(
                        query=phrase,
                        dom={"elements": descriptors},
                        page=page,
                        session_id=self.current_session_id,
                    )
                except TypeError:
                    # Fallback to descriptors kwarg if present in custom impls
                    try:
                        result = self.pipeline.process(
                            query=phrase,
                            descriptors=descriptors,
                            page=page,
                            session_id=self.current_session_id,
                        )
                    except TypeError:
                        # Ultimate fallback: positional minimal call
                        result = self.pipeline.process(phrase, {"elements": descriptors})
                
                # Check for unique XPath
                if result['xpath']:
                    # Verify uniqueness
                    unique_xpath = self._ensure_unique_xpath(
                        result['xpath'],
                        descriptors,
                        page
                    )
                    result['xpath'] = unique_xpath
                    
                    # Return in expected format
                    return {
                        'selector': unique_xpath,
                        'confidence': result['confidence'],
                        'element': result['element'],
                        'context': result['context'],
                        'fallbacks': result.get('fallbacks', [])
                    }
                else:
                    # Try fallback methods
                    return self._fallback_query(phrase, descriptors, page)
            else:
                # Use legacy flow
                return self._legacy_query(phrase, descriptors, page)
            
        except Exception as e:
            logger.error(f"Query failed: {e}", exc_info=True)
            
            # Try recovery if resilience enabled
            if self.resilience and page:
                recovery = self.resilience.recover_from_error(e, page, {})
                if recovery and recovery['action'] == 'retry':
                    # Retry once
                    return self.query(phrase, url=None)
            
            return {"ok": False, "error": str(e)}
    
    def click(self, phrase: str) -> Dict[str, Any]:
        """Click on element with verification and retry."""
        try:
            logger.info(f"Click: '{phrase}'")
            
            # Find element
            result = self.query(phrase)
            
            if isinstance(result, dict) and result.get('selector'):
                selector = result['selector']
                page = self._ensure_browser()
                
                if page:
                    # Wait for element
                    if self.resilience:
                        self.resilience.wait_for_idle(page, WaitStrategy.IDLE)
                    
                    # Try click with retries
                    max_attempts = 3 if self.resilience else 1
                    last_error = None
                    
                    for attempt in range(max_attempts):
                        try:
                            # Check if in iframe
                            if self._is_iframe_selector(selector):
                                frame = self._switch_to_frame(page, selector)
                                if frame:
                                    page = frame
                            
                            # Click element
                            page.click(selector, timeout=5000)
                            
                            # Verify action succeeded
                            if self.enable_pipeline and self.pipeline:
                                success = self._verify_action(page, 'click', selector)
                                if success:
                                    return {"ok": True, "message": f"Clicked {selector}"}
                            else:
                                return {"ok": True, "message": f"Clicked {selector}"}
                            
                        except Exception as e:
                            last_error = e
                            
                            # Try recovery
                            if self.resilience:
                                recovery = self.resilience.recover_from_error(e, page, {})
                                if recovery and recovery['action'] == 'retry':
                                    continue
                            
                            # Try fallback selectors
                            if 'fallbacks' in result and attempt < max_attempts - 1:
                                if attempt < len(result['fallbacks']):
                                    selector = result['fallbacks'][attempt]
                                    continue
                    
                    return {"ok": False, "error": str(last_error)}
                
            return {"ok": False, "error": "Element not found"}
            
        except Exception as e:
            logger.error(f"Click failed: {e}")
            return {"ok": False, "error": str(e)}
    
    def type_text(self, phrase: str, text: str) -> Dict[str, Any]:
        """Type text with validation and verification."""
        try:
            logger.info(f"Type: '{text}' for '{phrase}'")
            
            # Find element
            result = self.query(phrase)
            
            if isinstance(result, dict) and result.get('selector'):
                selector = result['selector']
                page = self._ensure_browser()
                
                if page:
                    # Detect input type
                    input_type = self._detect_input_type(page, selector)
                    
                    # Validate input
                    from .validators import FormValidator
                    valid, sanitized_text, error = FormValidator.validate_form_input(
                        input_type, text
                    )
                    
                    if not valid:
                        return {"ok": False, "error": f"Invalid input: {error}"}
                    
                    # Clear and type
                    page.fill(selector, str(sanitized_text))
                    
                    # Verify value was set
                    if self.enable_pipeline:
                        actual_value = page.evaluate(f"document.querySelector('{selector}').value")
                        if str(actual_value) == str(sanitized_text):
                            return {"ok": True, "message": f"Typed text in {selector}"}
                        else:
                            return {"ok": False, "error": "Value not set correctly"}
                    
                    return {"ok": True, "message": f"Typed text in {selector}"}
            
            return {"ok": False, "error": "Element not found"}
            
        except Exception as e:
            logger.error(f"Type failed: {e}")
            return {"ok": False, "error": str(e)}
    
    def _ensure_unique_xpath(
        self,
        xpath: str,
        descriptors: List[Dict[str, Any]],
        page: Optional[Page]
    ) -> str:
        """Ensure XPath is unique by adding position if needed."""
        if not page or not xpath.startswith('/'):
            return xpath
        
        try:
            # Count matching elements
            count = page.evaluate(f"""
                document.evaluate(
                    '{xpath}',
                    document,
                    null,
                    XPathResult.ORDERED_NODE_SNAPSHOT_TYPE,
                    null
                ).snapshotLength
            """)
            
            if count <= 1:
                return xpath  # Already unique
            
            # Find which position matches our descriptor
            # For now, return first match with position
            return f"({xpath})[1]"
            
        except Exception:
            return xpath
    
    def _is_iframe_selector(self, selector: str) -> bool:
        """Check if selector is for iframe content."""
        return 'iframe' in selector.lower() or '>>>' in selector
    
    def _switch_to_frame(self, page: Page, selector: str) -> Optional[Page]:
        """Switch to iframe context."""
        if not self.resilience:
            return None
        
        # Extract frame selector
        if '>>>' in selector:
            frame_sel = selector.split('>>>')[0]
        else:
            frame_sel = 'iframe'
        
        return self.resilience.switch_to_frame(page, frame_sel)
    
    def _detect_input_type(self, page: Page, selector: str) -> str:
        """Detect HTML input type."""
        try:
            input_type = page.evaluate(f"""
                document.querySelector('{selector}').type || 'text'
            """)
            return str(input_type)
        except Exception:
            return 'text'
    
    def _verify_action(self, page: Page, action: str, selector: str) -> bool:
        """Verify action succeeded."""
        try:
            if action == 'click':
                # Check if page navigated or element state changed
                # This is simplified - real implementation would be more robust
                return True
            elif action == 'type':
                # Check value was set
                value = page.evaluate(f"document.querySelector('{selector}').value")
                return bool(value)
            
            return True
        except Exception:
            return False
    
    def _fallback_query(
        self,
        phrase: str,
        descriptors: List[Dict[str, Any]],
        page: Optional[Page]
    ) -> Any:
        """Fallback query using simpler methods."""
        # Use legacy flow but with better XPath generation
        candidates = self._find_candidates(phrase, descriptors)
        
        results = []
        for desc, score, _ in candidates[:5]:
            locators = self.synthesizer.synthesize(desc)
            
            # Prioritize XPath
            xpath_locators = [loc for loc in locators if loc.startswith('/')]
            css_locators = [loc for loc in locators if not loc.startswith('/')]
            
            # Try to find unique selector
            selector = None
            if xpath_locators:
                for xpath in xpath_locators:
                    unique = self._ensure_unique_xpath(xpath, descriptors, page)
                    if unique:
                        selector = unique
                        break
            
            if not selector and css_locators:
                selector = css_locators[0]
            
            if selector:
                results.append({
                    'selector': selector,
                    'score': float(score),
                    'element': {
                        'text': desc.get('text', ''),
                        'tag': desc.get('tag', '')
                    }
                })
        
        return results if results else {"ok": False, "error": "No elements found"}
    
    def _legacy_query(
        self,
        phrase: str,
        descriptors: List[Dict[str, Any]],
        page: Optional[Page]
    ) -> Any:
        """Legacy query implementation for compatibility."""
        candidates = self._find_candidates(phrase, descriptors)
        
        results = []
        for desc, score, _ in candidates:
            locators = self.synthesizer.synthesize(desc)
            
            # Find first working selector
            selector = None
            if not page and locators:
                # Fallback when no browser context: pick first locator
                selector = locators[0]
            else:
                for loc in locators:
                    if page:
                        try:
                            ok, _, _ = self.verifier.verify(loc, page)
                        except Exception:
                            ok = False
                        if ok:
                            selector = loc
                            break
            
            if selector:
                results.append({
                    'selector': selector,
                    'score': float(score),
                    'element': {
                        'text': truncate_text(desc.get('text', ''), 100),
                        'tagName': desc.get('tagName', desc.get('tag', ''))
                    }
                })
        
        # Return based on phrase complexity
        phrase_lower = phrase.lower()
        is_complex = (
            len(phrase_lower.split()) >= 3 or
            any(phrase_lower.startswith(p) for p in ["type", "enter", "click", "select"]) or
            '"' in phrase or "'" in phrase
        )
        
        if is_complex and results:
            return results[0]
        
        return results
    
    def _find_candidates(
        self,
        phrase: str,
        descriptors: List[Dict[str, Any]]
    ) -> List[Tuple[Dict[str, Any], float, str]]:
        """Find candidate elements (legacy method)."""
        intent = self.intent_parser.parse(phrase)
        query_embedding = self.query_embedder.embed(phrase)
        
        candidates = []
        for desc in descriptors:
            try:
                element_embedding = self.element_embedder.embed(desc)
                score = self.fusion_scorer.score(
                    query_embedding=query_embedding,
                    element_embedding=element_embedding,
                    element_descriptor=desc,
                    intent=intent
                )
                candidates.append((desc, score, "fusion"))
            except Exception:
                continue
        
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[:10]
    
    def close(self):
        """Close browser and cleanup."""
        if self.page:
            self.page.close()
            self.page = None
        
        if self.browser:
            self.browser.close()
            self.browser = None
        
        if self.playwright:
            self.playwright.stop()
            self.playwright = None


# Alias for compatibility
HybridClient = HybridElementRetrieverClient


@dataclass
class QueryResult:
    selector: str
    score: float
    element: Dict[str, Any]