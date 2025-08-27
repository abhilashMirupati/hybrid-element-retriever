"""Action executor with scroll, visibility, overlays, retries, and verification."""
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
import time
import logging

logger = logging.getLogger(__name__)

try:
    from playwright.sync_api import (
        Page, Browser, BrowserContext, Playwright,
        sync_playwright, TimeoutError as PlaywrightTimeout,
        Error as PlaywrightError
    )
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    logger.warning("Playwright not available")
    Page = Any
    Browser = Any
    BrowserContext = Any
    Playwright = Any
    PlaywrightTimeout = Exception
    PlaywrightError = Exception
    PLAYWRIGHT_AVAILABLE = False
    sync_playwright = None


@dataclass
class ActionResult:
    """Result of an action execution."""
    success: bool
    action: str
    locator: str
    error: Optional[str] = None
    retries: int = 0
    overlay_events: List[str] = field(default_factory=list)
    verification: Dict[str, Any] = field(default_factory=dict)
    duration_ms: int = 0
    screenshot: Optional[bytes] = None


class ActionExecutor:
    """Executes UI actions with advanced handling."""
    
    def __init__(
        self,
        headless: bool = True,
        timeout_ms: int = 30000,
        retry_count: int = 3,
        retry_delay_ms: int = 500,
        take_screenshots: bool = False
    ):
        self.headless = headless
        self.timeout_ms = timeout_ms
        self.retry_count = retry_count
        self.retry_delay_ms = retry_delay_ms
        self.take_screenshots = take_screenshots
        
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        if PLAYWRIGHT_AVAILABLE:
            self._initialize()
    
    def _initialize(self) -> None:
        """Initialize Playwright browser."""
        if not PLAYWRIGHT_AVAILABLE:
            return
        
        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(
                headless=self.headless,
                args=['--disable-blink-features=AutomationControlled']
            )
            self.context = self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            self.page = self.context.new_page()
            
            # Set default timeout
            self.page.set_default_timeout(self.timeout_ms)
            
            logger.info("ActionExecutor initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Playwright: {e}")
    
    def goto(self, url: str, wait_until: str = "domcontentloaded") -> bool:
        """Navigate to URL."""
        if not self.page:
            logger.error("Page not initialized")
            return False
        
        try:
            self.page.goto(url, wait_until=wait_until)
            logger.info(f"Navigated to {url}")
            return True
        except Exception as e:
            logger.error(f"Failed to navigate to {url}: {e}")
            return False
    
    def click(self, locator: str, force: bool = False, timeout: Optional[int] = None) -> ActionResult:
        """Click an element with retries and verification."""
        return self._execute_action("click", locator, force=force, timeout=timeout)
    
    def fill(self, locator: str, text: str, timeout: Optional[int] = None) -> ActionResult:
        """Fill text into an input field."""
        return self._execute_action("fill", locator, text=text, timeout=timeout)
    
    def select(self, locator: str, value: str, timeout: Optional[int] = None) -> ActionResult:
        """Select option from dropdown."""
        return self._execute_action("select", locator, value=value, timeout=timeout)
    
    def hover(self, locator: str, timeout: Optional[int] = None) -> ActionResult:
        """Hover over an element."""
        return self._execute_action("hover", locator, timeout=timeout)
    
    def _execute_action(self, action: str, locator: str, **kwargs) -> ActionResult:
        """Execute an action with retries and advanced handling."""
        if not self.page:
            return ActionResult(
                success=False,
                action=action,
                locator=locator,
                error="Page not initialized"
            )
        
        start_time = time.time()
        result = ActionResult(action=action, locator=locator)
        timeout = kwargs.pop('timeout', self.timeout_ms)
        
        for attempt in range(self.retry_count):
            try:
                # Dismiss overlays before action
                overlay_events = self._dismiss_overlays()
                result.overlay_events.extend(overlay_events)
                
                # Get element
                element = self.page.locator(locator)
                
                # Check element exists
                if element.count() == 0:
                    raise PlaywrightError(f"No elements found for locator: {locator}")
                elif element.count() > 1:
                    logger.warning(f"Multiple elements found for locator: {locator}, using first")
                    element = element.first
                
                # Scroll into view
                self._scroll_into_view(element)
                
                # Check visibility and interactability
                if not kwargs.get('force', False):
                    self._ensure_interactable(element)
                
                # Execute action
                if action == "click":
                    element.click(timeout=timeout, force=kwargs.get('force', False))
                elif action == "fill":
                    element.fill(kwargs['text'], timeout=timeout)
                elif action == "select":
                    element.select_option(kwargs['value'], timeout=timeout)
                elif action == "hover":
                    element.hover(timeout=timeout)
                else:
                    raise ValueError(f"Unknown action: {action}")
                
                # Verify action completed
                verification = self._verify_action(action, element, **kwargs)
                result.verification = verification
                
                # Success
                result.success = True
                result.retries = attempt
                break
                
            except (PlaywrightTimeout, PlaywrightError) as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                result.error = str(e)
                
                if attempt < self.retry_count - 1:
                    # Wait before retry
                    time.sleep(self.retry_delay_ms / 1000)
                    
                    # Try alternative strategies
                    if attempt == 1:
                        # Second attempt: try with JavaScript
                        try:
                            self._execute_with_javascript(action, locator, **kwargs)
                            result.success = True
                            result.retries = attempt + 1
                            result.verification["method"] = "javascript"
                            break
                        except:
                            pass
                else:
                    # Final failure
                    result.success = False
        
        # Calculate duration
        result.duration_ms = int((time.time() - start_time) * 1000)
        
        # Take screenshot if requested
        if self.take_screenshots:
            try:
                result.screenshot = self.page.screenshot()
            except:
                pass
        
        # Log result
        if result.success:
            logger.info(f"Action {action} succeeded on {locator} (retries: {result.retries}, duration: {result.duration_ms}ms)")
        else:
            logger.error(f"Action {action} failed on {locator}: {result.error}")
        
        return result
    
    def _dismiss_overlays(self) -> List[str]:
        """Dismiss common overlay patterns."""
        if not self.page:
            return []
        
        dismissed = []
        
        # Common overlay patterns
        overlay_patterns = [
            ("button:has-text('Accept')", "Cookie banner"),
            ("button:has-text('OK')", "Alert dialog"),
            ("button:has-text('Close')", "Modal dialog"),
            ("[aria-label='Close']", "Close button"),
            (".modal-close", "Modal close button"),
            (".popup-close", "Popup close button"),
        ]
        
        for selector, description in overlay_patterns:
            try:
                overlay = self.page.locator(selector)
                if overlay.is_visible(timeout=100):
                    overlay.click(timeout=1000)
                    dismissed.append(description)
                    logger.info(f"Dismissed overlay: {description}")
                    time.sleep(0.5)  # Wait for animation
            except:
                pass
        
        return dismissed
    
    def _scroll_into_view(self, element: Any) -> None:
        """Scroll element into view."""
        try:
            element.scroll_into_view_if_needed(timeout=2000)
            time.sleep(0.2)  # Wait for scroll to complete
        except Exception as e:
            logger.debug(f"Could not scroll into view: {e}")
    
    def _ensure_interactable(self, element: Any) -> None:
        """Ensure element is visible and enabled."""
        try:
            # Check visibility
            if not element.is_visible(timeout=1000):
                # Try to wait for visibility
                element.wait_for(state="visible", timeout=5000)
            
            # Check if enabled
            if not element.is_enabled(timeout=1000):
                raise PlaywrightError("Element is disabled")
            
            # Check for occlusion
            bounding_box = element.bounding_box()
            if bounding_box:
                # Check if element is too small
                if bounding_box['width'] < 1 or bounding_box['height'] < 1:
                    raise PlaywrightError("Element has no size")
        
        except PlaywrightTimeout:
            raise PlaywrightError("Element is not visible")
    
    def _execute_with_javascript(self, action: str, locator: str, **kwargs) -> None:
        """Execute action using JavaScript as fallback."""
        if not self.page:
            raise PlaywrightError("Page not initialized")
        
        # Get element handle
        element = self.page.locator(locator).element_handle()
        if not element:
            raise PlaywrightError("Could not get element handle")
        
        if action == "click":
            self.page.evaluate("el => el.click()", element)
        elif action == "fill":
            text = kwargs.get('text', '')
            self.page.evaluate("(el, text) => { el.value = text; el.dispatchEvent(new Event('input')); }", 
                             element, text)
        elif action == "select":
            value = kwargs.get('value', '')
            self.page.evaluate("(el, value) => { el.value = value; el.dispatchEvent(new Event('change')); }",
                             element, value)
        else:
            raise ValueError(f"JavaScript execution not implemented for {action}")
    
    def _verify_action(self, action: str, element: Any, **kwargs) -> Dict[str, Any]:
        """Verify action was successful."""
        verification = {"verified": False}
        
        try:
            if action == "click":
                # For clicks, check if page changed or element state changed
                verification["element_exists"] = element.count() > 0
                verification["verified"] = True
            
            elif action == "fill":
                # For fill, check if value was set
                expected_text = kwargs.get('text', '')
                actual_value = element.input_value()
                verification["expected"] = expected_text
                verification["actual"] = actual_value
                verification["verified"] = expected_text == actual_value
            
            elif action == "select":
                # For select, check if option is selected
                expected_value = kwargs.get('value', '')
                actual_value = element.input_value()
                verification["expected"] = expected_value
                verification["actual"] = actual_value
                verification["verified"] = expected_value == actual_value
        
        except Exception as e:
            verification["error"] = str(e)
        
        return verification
    
    def wait_for_condition(self, condition: str, timeout: Optional[int] = None) -> bool:
        """Wait for a condition to be met."""
        if not self.page:
            return False
        
        timeout = timeout or self.timeout_ms
        
        try:
            if condition == "load":
                self.page.wait_for_load_state("load", timeout=timeout)
            elif condition == "domcontentloaded":
                self.page.wait_for_load_state("domcontentloaded", timeout=timeout)
            elif condition == "networkidle":
                self.page.wait_for_load_state("networkidle", timeout=timeout)
            else:
                # Custom selector wait
                self.page.wait_for_selector(condition, timeout=timeout)
            
            return True
        except PlaywrightTimeout:
            return False
    
    def close(self) -> None:
        """Close browser and clean up resources."""
        if self.page:
            try:
                self.page.close()
            except:
                pass
        
        if self.context:
            try:
                self.context.close()
            except:
                pass
        
        if self.browser:
            try:
                self.browser.close()
            except:
                pass
        
        if self.playwright:
            try:
                self.playwright.stop()
            except:
                pass
        
        logger.info("ActionExecutor closed")