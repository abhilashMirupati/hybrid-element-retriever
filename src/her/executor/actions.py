"""Action executor with occlusion guard and overlay handling."""

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
import logging
import time

from ..config import (
    DEFAULT_TIMEOUT_MS,
    DEFAULT_WAIT_MS,
    DEFAULT_SETTLE_MS,
    DEFAULT_HEADLESS,
    DEFAULT_VIEWPORT,
)

logger = logging.getLogger(__name__)

try:
    from playwright.sync_api import (
        sync_playwright,
        Page,
        Browser,
        BrowserContext,
        Error as PlaywrightError,
        TimeoutError as PlaywrightTimeout,
    )

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    logger.warning("Playwright not available")
    PLAYWRIGHT_AVAILABLE = False
    PlaywrightError = Exception
    PlaywrightTimeout = Exception


@dataclass
class ActionResult:
    """Result of an action execution."""

    success: bool = False
    action: str = ""
    locator: str = ""
    error: Optional[str] = None
    retries: int = 0
    duration_ms: int = 0
    verification: Dict[str, Any] = field(default_factory=dict)
    dismissed_overlays: List[str] = field(default_factory=list)
    screenshot: Optional[bytes] = None


class ActionExecutor:
    """Executes UI actions with retry and recovery capabilities."""

    def __init__(
        self,
        headless: bool = DEFAULT_HEADLESS,
        timeout_ms: int = DEFAULT_TIMEOUT_MS,
        wait_after_action: int = DEFAULT_WAIT_MS,
        wait_after_scroll: int = DEFAULT_SETTLE_MS,
        take_screenshots: bool = False,
        dismiss_overlays: bool = True,
    ):
        """Initialize action executor.

        Args:
            headless: Run browser in headless mode
            timeout_ms: Default timeout for actions
            wait_after_action: Wait time after each action (ms)
            wait_after_scroll: Wait time after scrolling (ms)
            take_screenshots: Whether to take screenshots after actions
            dismiss_overlays: Whether to automatically dismiss overlays
        """
        self.headless = headless
        self.timeout_ms = timeout_ms
        self.wait_after_action = wait_after_action
        self.wait_after_scroll = wait_after_scroll
        self.take_screenshots = take_screenshots
        self.dismiss_overlays_enabled = dismiss_overlays

        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

        if PLAYWRIGHT_AVAILABLE:
            self._initialize_browser()

    def _initialize_browser(self) -> None:
        """Initialize Playwright browser."""
        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(
                headless=self.headless,
                args=["--no-sandbox", "--disable-setuid-sandbox"],
            )
            self.context = self.browser.new_context(
                viewport=DEFAULT_VIEWPORT, ignore_https_errors=True
            )
            self.page = self.context.new_page()

            # Set default timeout
            self.page.set_default_timeout(self.timeout_ms)

            logger.info(f"Browser initialized (headless={self.headless})")

        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            raise

    def navigate(self, url: str) -> bool:
        """Navigate to URL.

        Args:
            url: URL to navigate to

        Returns:
            True if navigation successful
        """
        if not self.page:
            return False

        try:
            self.page.goto(url, wait_until="domcontentloaded")
            logger.info(f"Navigated to {url}")
            return True
        except Exception as e:
            logger.error(f"Failed to navigate to {url}: {e}")
            return False

    def execute(self, action: str, locator: str, **kwargs) -> ActionResult:
        """Execute an action on an element.

        Args:
            action: Action to perform (click, fill, select, etc.)
            locator: Element locator
            **kwargs: Additional action parameters

        Returns:
            ActionResult with execution details
        """
        result = ActionResult(action=action, locator=locator)
        start_time = time.time()

        if not self.page:
            result.error = "Page not initialized"
            return result

        # Dismiss overlays if enabled
        if self.dismiss_overlays_enabled:
            result.dismissed_overlays = self._dismiss_overlays()

        # Try to execute action
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                element = self.page.locator(locator)

                # Wait for element to be ready
                element.wait_for(state="visible", timeout=5000)

                # Scroll into view
                self._scroll_into_view(element)

                # Check for occlusion
                if not self._check_element_occlusion(locator):
                    # Try to dismiss overlays again
                    if self.dismiss_overlays_enabled:
                        new_dismissed = self._dismiss_overlays()
                        result.dismissed_overlays.extend(new_dismissed)
                        self.page.wait_for_timeout(500)

                    # Check again
                    if not self._check_element_occlusion(locator):
                        raise PlaywrightError(f"Element {locator} is occluded")

                # Execute action
                if action == "click":
                    element.click()
                elif action == "fill":
                    text = kwargs.get("text", "")
                    element.fill(text)
                elif action == "select":
                    value = kwargs.get("value", "")
                    element.select_option(value)
                elif action == "check":
                    element.check()
                elif action == "uncheck":
                    element.uncheck()
                elif action == "hover":
                    element.hover()
                elif action == "focus":
                    element.focus()
                elif action == "press":
                    key = kwargs.get("key", "Enter")
                    element.press(key)
                else:
                    raise ValueError(f"Unknown action: {action}")

                # Wait after action
                if self.wait_after_action:
                    self.page.wait_for_timeout(self.wait_after_action)

                # Verify action
                result.verification = self._verify_action(action, element, **kwargs)
                result.success = result.verification.get("verified", True)
                result.retries = attempt

                break

            except PlaywrightTimeout as e:
                logger.warning(f"Timeout on attempt {attempt + 1}: {e}")
                result.error = str(e)

                if attempt < max_attempts - 1:
                    # Try alternative approach
                    try:
                        # Second attempt: try with JavaScript
                        self._execute_with_javascript(action, locator, **kwargs)
                        result.success = True
                        result.retries = attempt + 1
                        result.verification["method"] = "javascript"
                        break
                    except Exception as js_error:
                        logger.debug(f"JavaScript execution failed: {js_error}")
                        result.error = str(js_error)
                else:
                    # Final failure
                    result.success = False

            except Exception as e:
                logger.error(f"Action failed on attempt {attempt + 1}: {e}")
                result.error = str(e)
                result.success = False

                if attempt >= max_attempts - 1:
                    break

        # Calculate duration
        result.duration_ms = int((time.time() - start_time) * 1000)

        # Take screenshot if requested
        if self.take_screenshots:
            try:
                result.screenshot = self.page.screenshot()
            except Exception as screenshot_error:
                logger.debug(f"Failed to take screenshot: {screenshot_error}")

        # Log result
        if result.success:
            logger.info(
                f"Action {action} succeeded on {locator} (retries: {result.retries}, duration: {result.duration_ms}ms)"
            )
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
            except Exception as overlay_error:
                logger.debug(f"Failed to dismiss overlay {selector}: {overlay_error}")

        return dismissed

    def _check_element_occlusion(self, locator: str) -> bool:
        """Check if element is occluded by another element.

        Args:
            locator: Element locator

        Returns:
            True if element is visible and not occluded
        """
        if not self.page:
            return False

        try:
            element = self.page.locator(locator)

            # Get element bounding box
            box = element.bounding_box()
            if not box:
                return False

            # Check center point
            center_x = box["x"] + box["width"] / 2
            center_y = box["y"] + box["height"] / 2

            # Use elementFromPoint to check what's at the center
            js_code = """
            (args) => {
                const [x, y, selector] = args;
                const elem = document.elementFromPoint(x, y);
                const target = document.querySelector(selector);
                if (!elem || !target) return false;
                
                // Check if the element at point is our target or a descendant
                return elem === target || target.contains(elem);
            }
            """

            is_visible = self.page.evaluate(js_code, [center_x, center_y, locator])

            if not is_visible:
                logger.debug(f"Element {locator} is occluded at center point")

                # Try corners as well
                corners = [
                    (box["x"] + 5, box["y"] + 5),  # Top-left
                    (box["x"] + box["width"] - 5, box["y"] + 5),  # Top-right
                    (box["x"] + 5, box["y"] + box["height"] - 5),  # Bottom-left
                    (
                        box["x"] + box["width"] - 5,
                        box["y"] + box["height"] - 5,
                    ),  # Bottom-right
                ]

                for x, y in corners:
                    corner_visible = self.page.evaluate(js_code, [x, y, locator])
                    if corner_visible:
                        logger.debug(
                            f"Element {locator} is visible at corner ({x}, {y})"
                        )
                        return True

                return False

            return True

        except Exception as e:
            logger.warning(f"Failed to check occlusion for {locator}: {e}")
            return True  # Assume visible if check fails

    def _scroll_into_view(self, element: Any) -> None:
        """Scroll element into view."""
        try:
            element.scroll_into_view_if_needed(timeout=2000)
            time.sleep(self.wait_after_scroll / 1000.0)  # Convert ms to seconds
        except Exception as e:
            logger.debug(f"Could not scroll into view: {e}")

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
            text = kwargs.get("text", "")
            self.page.evaluate(
                "(el, text) => { el.value = text; el.dispatchEvent(new Event('input')); }",
                element,
                text,
            )
        elif action == "select":
            value = kwargs.get("value", "")
            self.page.evaluate(
                "(el, value) => { el.value = value; el.dispatchEvent(new Event('change')); }",
                element,
                value,
            )
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

                # Check for URL change
                try:
                    new_url = self.page.url
                    verification["new_url"] = new_url
                except Exception as url_error:
                    logger.debug(f"Failed to get URL: {url_error}")

            elif action == "fill":
                # For fill, check if value was set
                expected_text = kwargs.get("text", "")
                try:
                    actual_value = element.input_value()
                except Exception as value_error:
                    logger.debug(f"Failed to get input value: {value_error}")
                    actual_value = ""

                verification["expected"] = expected_text
                verification["actual"] = actual_value
                verification["verified"] = expected_text == actual_value

            elif action == "select":
                # For select, check if option is selected
                expected_value = kwargs.get("value", "")
                try:
                    actual_value = element.input_value()
                except Exception as value_error:
                    logger.debug(f"Failed to get select value: {value_error}")
                    actual_value = ""

                verification["expected"] = expected_value
                verification["actual"] = actual_value
                verification["verified"] = expected_value == actual_value

            elif action in ["check", "uncheck"]:
                # For checkboxes, verify checked state
                expected_checked = action == "check"
                try:
                    actual_checked = element.is_checked()
                except Exception as check_error:
                    logger.debug(f"Failed to get checked state: {check_error}")
                    actual_checked = False

                verification["expected"] = expected_checked
                verification["actual"] = actual_checked
                verification["verified"] = expected_checked == actual_checked

        except Exception as e:
            verification["error"] = str(e)
            logger.debug(f"Verification failed: {e}")

        # Wait a bit after verification
        try:
            if self.page:
                self.page.wait_for_timeout(200)
        except Exception as wait_error:
            logger.debug(f"Post-action wait failed: {wait_error}")

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
            except Exception as e:
                logger.debug(f"Failed to close page: {e}")

        if self.context:
            try:
                self.context.close()
            except Exception as e:
                logger.debug(f"Failed to close context: {e}")

        if self.browser:
            try:
                self.browser.close()
            except Exception as e:
                logger.debug(f"Failed to close browser: {e}")

        if self.playwright:
            try:
                self.playwright.stop()
            except Exception as e:
                logger.debug(f"Failed to stop playwright: {e}")

        logger.info("ActionExecutor closed")
