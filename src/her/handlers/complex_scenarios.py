"""Advanced handlers for complex web scenarios."""

import logging
import time
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
try:
    from playwright.sync_api import Page, ElementHandle, Frame, Error as PlaywrightError
    PLAYWRIGHT_AVAILABLE = True
except Exception:  # pragma: no cover
    Page = object  # type: ignore
    ElementHandle = object  # type: ignore
    Frame = object  # type: ignore
    class PlaywrightError(Exception):
        pass
    PLAYWRIGHT_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class WaitStrategy:
    """Strategy for waiting for elements in dynamic pages."""
    
    timeout: float = 30.0
    poll_interval: float = 0.5
    stable_time: float = 0.5
    retry_on_stale: bool = True
    max_retries: int = 3


class StaleElementHandler:
    """Handles stale element references in dynamic pages."""
    
    def __init__(self, wait_strategy: Optional[WaitStrategy] = None):
        self.strategy = wait_strategy or WaitStrategy()
        self.retry_count = 0
    
    def safe_execute(
        self,
        element_getter: Callable,
        action: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute action with stale element protection.
        
        Args:
            element_getter: Function to get/re-get the element
            action: Action to perform on element
            *args, **kwargs: Arguments for action
            
        Returns:
            Result of action execution
        """
        last_error = None
        
        for attempt in range(self.strategy.max_retries):
            try:
                # Get fresh element reference
                element = element_getter()
                if not element:
                    raise ValueError("Element not found")
                
                # Wait for element to be stable
                if hasattr(element, 'wait_for_element_state'):
                    element.wait_for_element_state('stable', timeout=self.strategy.timeout * 1000)
                
                # Execute action
                result = action(element, *args, **kwargs)
                self.retry_count = 0  # Reset on success
                return result
                
            except (PlaywrightError, Exception) as e:
                last_error = e
                error_msg = str(e).lower()
                
                # Check if it's a stale element error
                if any(term in error_msg for term in ['stale', 'detached', 'not connected']):
                    logger.warning(f"Stale element detected (attempt {attempt + 1}): {e}")
                    time.sleep(self.strategy.poll_interval)
                    continue
                
                # Check if element is not visible/interactable
                if any(term in error_msg for term in ['not visible', 'not enabled', 'intercepted']):
                    logger.warning(f"Element not ready (attempt {attempt + 1}): {e}")
                    time.sleep(self.strategy.poll_interval)
                    continue
                
                # Other errors, re-raise
                raise
        
        raise Exception(f"Failed after {self.strategy.max_retries} attempts: {last_error}")


class DynamicContentHandler:
    """Handles dynamic content loading scenarios."""
    
    def __init__(self, page: Page):
        self.page = page
        self.wait_strategy = WaitStrategy()
    
    def wait_for_ajax(self, timeout: float = 10.0) -> None:
        """Wait for AJAX requests to complete.
        
        Args:
            timeout: Maximum wait time in seconds
        """
        try:
            # Wait for no network activity
            self.page.wait_for_load_state('networkidle', timeout=timeout * 1000)
        except Exception:
            # Fallback: wait for DOM to be stable
            self.wait_for_dom_stable(timeout / 2)
    
    def wait_for_dom_stable(self, timeout: float = 5.0) -> None:
        """Wait for DOM to stop changing.
        
        Args:
            timeout: Maximum wait time in seconds
        """
        start_time = time.time()
        last_dom_hash = ""
        stable_count = 0
        required_stable_checks = 3
        
        while time.time() - start_time < timeout:
            try:
                # Get current DOM hash
                current_hash = self.page.evaluate("""
                    () => {
                        const elements = document.querySelectorAll('*');
                        return elements.length + '-' + document.body.innerHTML.length;
                    }
                """)
                
                if current_hash == last_dom_hash:
                    stable_count += 1
                    if stable_count >= required_stable_checks:
                        logger.debug("DOM is stable")
                        return
                else:
                    stable_count = 0
                    last_dom_hash = current_hash
                
                time.sleep(0.2)
                
            except Exception as e:
                logger.warning(f"Error checking DOM stability: {e}")
                break
        
        logger.warning(f"DOM did not stabilize within {timeout}s")
    
    def wait_for_element_text_change(
        self,
        selector: str,
        original_text: str,
        timeout: float = 10.0
    ) -> bool:
        """Wait for element text to change from original.
        
        Args:
            selector: Element selector
            original_text: Original text to wait for change
            timeout: Maximum wait time
            
        Returns:
            True if text changed, False if timeout
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                element = self.page.query_selector(selector)
                if element:
                    current_text = element.inner_text()
                    if current_text != original_text:
                        return True
            except Exception:
                # Ignore transient errors while probing dynamic content
                continue
            
            time.sleep(0.2)
        
        return False
    
    def handle_infinite_scroll(
        self,
        container_selector: str = "body",
        max_scrolls: int = 10,
        wait_after_scroll: float = 1.0
    ) -> int:
        """Handle infinite scroll to load all content.
        
        Args:
            container_selector: Selector for scrollable container
            max_scrolls: Maximum number of scrolls
            wait_after_scroll: Wait time after each scroll
            
        Returns:
            Number of scrolls performed
        """
        scrolls = 0
        last_height = 0
        
        for _ in range(max_scrolls):
            # Get current scroll height
            current_height = self.page.evaluate(f"""
                () => {{
                    const container = document.querySelector('{container_selector}');
                    return container ? container.scrollHeight : document.body.scrollHeight;
                }}
            """)
            
            if current_height == last_height:
                # No new content loaded
                break
            
            # Scroll to bottom
            self.page.evaluate(f"""
                () => {{
                    const container = document.querySelector('{container_selector}');
                    if (container) {{
                        container.scrollTop = container.scrollHeight;
                    }} else {{
                        window.scrollTo(0, document.body.scrollHeight);
                    }}
                }}
            """)
            
            scrolls += 1
            last_height = current_height
            
            # Wait for new content to load
            time.sleep(wait_after_scroll)
            self.wait_for_ajax(timeout=wait_after_scroll * 2)
        
        logger.info(f"Performed {scrolls} scrolls to load content")
        return scrolls
    
    def handle_lazy_loading(
        self,
        viewport_height: int = 800,
        scroll_step: int = 400,
        wait_between: float = 0.5
    ) -> None:
        """Handle lazy-loaded content by scrolling through page.
        
        Args:
            viewport_height: Height of viewport
            scroll_step: Pixels to scroll each step
            wait_between: Wait time between scrolls
        """
        # Get total page height
        try:
            total_height = self.page.evaluate("() => document.body.scrollHeight")
        except Exception:
            total_height = 0
        try:
            total_height = int(total_height) if total_height is not None else 0
        except Exception:
            total_height = 0
        if total_height <= 0:
            total_height = int(viewport_height)
        
        # Scroll through the page
        current_position = 0
        while current_position < total_height:
            # Scroll down
            self.page.evaluate(f"window.scrollTo(0, {current_position})")
            
            # Wait for content to load
            time.sleep(wait_between)
            
            # Update position
            current_position += scroll_step
            
            # Check if page height increased (new content loaded)
            try:
                new_height = self.page.evaluate("() => document.body.scrollHeight")
                nh = int(new_height) if new_height is not None else total_height
                if nh > total_height:
                    total_height = nh
            except Exception:
                pass
        
        # Scroll back to top
        self.page.evaluate("window.scrollTo(0, 0)")
        logger.debug("Completed lazy loading scroll")


class FrameHandler:
    """Handles iframe and frame navigation."""
    
    def __init__(self, page: Page):
        self.page = page
        self.frame_cache: Dict[str, Frame] = {}
    
    def find_frame_with_element(self, selector: str) -> Optional[Frame]:
        """Find frame containing element matching selector.
        
        Args:
            selector: Element selector to search for
            
        Returns:
            Frame containing the element, or None
        """
        # Check main frame first
        if self.page.query_selector(selector):
            return self.page.main_frame
        
        # Check all frames
        for frame in self.page.frames:
            try:
                if frame.query_selector(selector):
                    return frame
            except Exception:
                # Frame might be detached
                continue
        
        return None
    
    def get_frame_by_attributes(
        self,
        name: Optional[str] = None,
        url_pattern: Optional[str] = None,
        title: Optional[str] = None
    ) -> Optional[Frame]:
        """Get frame by various attributes.
        
        Args:
            name: Frame name attribute
            url_pattern: Pattern to match in frame URL
            title: Frame title
            
        Returns:
            Matching frame or None
        """
        for frame in self.page.frames:
            try:
                if name and frame.name == name:
                    return frame
                
                if url_pattern and url_pattern in frame.url:
                    return frame
                
                if title:
                    frame_title = frame.title()
                    if frame_title == title:
                        return frame
                        
            except Exception:
                continue
        
        return None
    
    def switch_to_frame(self, frame_selector: str) -> Optional[Frame]:
        """Switch context to iframe.
        
        Args:
            frame_selector: Selector for iframe element
            
        Returns:
            Frame object or None
        """
        try:
            # Get iframe element
            iframe_element = self.page.query_selector(frame_selector)
            if not iframe_element:
                return None
            
            # Get frame from element
            frame = iframe_element.content_frame()
            if frame:
                self.frame_cache[frame_selector] = frame
                logger.debug(f"Switched to frame: {frame_selector}")
            
            return frame
            
        except Exception as e:
            logger.error(f"Failed to switch to frame {frame_selector}: {e}")
            return None
    
    def execute_in_frame(
        self,
        frame: Frame,
        action: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute action within frame context.
        
        Args:
            frame: Frame to execute in
            action: Action to perform
            *args, **kwargs: Arguments for action
            
        Returns:
            Result of action execution
        """
        try:
            # Ensure frame is attached
            if frame.is_detached():
                raise Exception("Frame is detached")
            
            # Execute action
            return action(frame, *args, **kwargs)
            
        except Exception as e:
            logger.error(f"Failed to execute in frame: {e}")
            raise


class ShadowDOMHandler:
    """Handles Shadow DOM traversal and element access."""
    
    def __init__(self, page: Page):
        self.page = page
    
    def pierce_shadow_dom(self, host_selector: str) -> List[Any]:
        """Pierce through shadow DOM to get elements.
        
        Args:
            host_selector: Selector for shadow host element
            
        Returns:
            List of elements within shadow DOM
        """
        try:
            # Use JavaScript to pierce shadow DOM
            elements = self.page.evaluate(f"""
                () => {{
                    const host = document.querySelector('{host_selector}');
                    if (!host || !host.shadowRoot) return [];
                    
                    const elements = [];
                    const shadowRoot = host.shadowRoot;
                    
                    // Get all elements in shadow DOM
                    const allElements = shadowRoot.querySelectorAll('*');
                    for (const el of allElements) {{
                        elements.push({{
                            tagName: el.tagName.toLowerCase(),
                            id: el.id || '',
                            className: el.className || '',
                            textContent: el.textContent || '',
                            innerHTML: el.innerHTML || ''
                        }});
                    }}
                    
                    return elements;
                }}
            """)
            
            return elements
            
        except Exception as e:
            logger.error(f"Failed to pierce shadow DOM: {e}")
            return []
    
    def find_in_shadow_dom(
        self,
        host_selector: str,
        target_selector: str
    ) -> Optional[Dict]:
        """Find element within shadow DOM.
        
        Args:
            host_selector: Selector for shadow host
            target_selector: Selector for target element within shadow
            
        Returns:
            Element info or None
        """
        try:
            result = self.page.evaluate(f"""
                () => {{
                    const host = document.querySelector('{host_selector}');
                    if (!host || !host.shadowRoot) return null;
                    
                    const target = host.shadowRoot.querySelector('{target_selector}');
                    if (!target) return null;
                    
                    return {{
                        found: true,
                        tagName: target.tagName.toLowerCase(),
                        id: target.id || '',
                        className: target.className || '',
                        textContent: target.textContent || '',
                        isVisible: target.offsetParent !== null
                    }};
                }}
            """)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to find in shadow DOM: {e}")
            return None
    
    def click_in_shadow_dom(
        self,
        host_selector: str,
        target_selector: str
    ) -> bool:
        """Click element within shadow DOM.
        
        Args:
            host_selector: Selector for shadow host
            target_selector: Selector for target element
            
        Returns:
            True if clicked successfully
        """
        try:
            success = self.page.evaluate(f"""
                () => {{
                    const host = document.querySelector('{host_selector}');
                    if (!host || !host.shadowRoot) return false;
                    
                    const target = host.shadowRoot.querySelector('{target_selector}');
                    if (!target) return false;
                    
                    target.click();
                    return true;
                }}
            """)
            
            return bool(success)
            
        except Exception as e:
            logger.error(f"Failed to click in shadow DOM: {e}")
            return False


class SPANavigationHandler:
    """Handles Single Page Application navigation."""
    
    def __init__(self, page: Page):
        self.page = page
        self.route_history: List[str] = []
        self.setup_route_listener()
    
    def setup_route_listener(self) -> None:
        """Setup listener for route changes."""
        try:
            # Inject route change detector
            self.page.evaluate("""
                () => {
                    if (!window.__herRouteListener) {
                        window.__herRouteListener = true;
                        window.__herRoutes = [];
                        
                        // Listen to pushState
                        const originalPushState = history.pushState;
                        history.pushState = function() {
                            window.__herRoutes.push({
                                type: 'pushState',
                                url: arguments[2],
                                timestamp: Date.now()
                            });
                            return originalPushState.apply(history, arguments);
                        };
                        
                        // Listen to replaceState
                        const originalReplaceState = history.replaceState;
                        history.replaceState = function() {
                            window.__herRoutes.push({
                                type: 'replaceState',
                                url: arguments[2],
                                timestamp: Date.now()
                            });
                            return originalReplaceState.apply(history, arguments);
                        };
                        
                        // Listen to popstate
                        window.addEventListener('popstate', function(event) {
                            window.__herRoutes.push({
                                type: 'popstate',
                                url: location.href,
                                timestamp: Date.now()
                            });
                        });
                        
                        // Listen to hashchange
                        window.addEventListener('hashchange', function(event) {
                            window.__herRoutes.push({
                                type: 'hashchange',
                                url: location.href,
                                timestamp: Date.now()
                            });
                        });
                    }
                }
            """)
            
            logger.debug("Route listener setup complete")
            
        except Exception as e:
            logger.error(f"Failed to setup route listener: {e}")
    
    def detect_route_change(self, timeout: float = 5.0) -> bool:
        """Detect if route has changed.
        
        Args:
            timeout: Maximum wait time
            
        Returns:
            True if route changed
        """
        initial_url = getattr(self.page, 'url', None)
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                current_url = getattr(self.page, 'url', None)
                if current_url != initial_url:
                    self.route_history.append(current_url)
                    logger.info(f"Route changed: {initial_url} -> {current_url}")
                    return True
                try:
                    routes = self.page.evaluate("() => window.__herRoutes || []")
                    # Only check length when routes is a sequence
                    if isinstance(routes, (list, tuple)) and len(routes) > len(self.route_history):
                        logger.info("Client-side route change detected")
                        return True
                except Exception:
                    # Ignore evaluate errors in mocks
                    pass
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Error detecting route change: {e}")
                # Keep waiting despite transient errors
                time.sleep(0.1)
                continue
        return False
    
    def wait_for_spa_navigation(self, timeout: float = 10.0) -> None:
        """Wait for SPA navigation to complete.
        
        Args:
            timeout: Maximum wait time
        """
        # Wait for route change
        self.detect_route_change(timeout / 2)
        
        # Wait for content to load
        dynamic_handler = DynamicContentHandler(self.page)
        dynamic_handler.wait_for_ajax(timeout / 2)
        dynamic_handler.wait_for_dom_stable(timeout / 2)


class ComplexScenarioHandler:
    """Main handler combining all complex scenario handlers."""
    
    def __init__(self, page: Page):
        self.page = page
        self.stale_handler = StaleElementHandler()
        self.dynamic_handler = DynamicContentHandler(page)
        self.frame_handler = FrameHandler(page)
        self.shadow_handler = ShadowDOMHandler(page)
        self.spa_handler = SPANavigationHandler(page)
    
    def handle_element_interaction(
        self,
        selector: str,
        action: str = "click",
        value: Optional[str] = None,
        handle_stale: bool = True,
        handle_frames: bool = True,
        handle_shadow: bool = True,
        wait_stable: bool = True
    ) -> bool:
        """Handle element interaction with all complex scenarios.
        
        Args:
            selector: Element selector
            action: Action to perform (click, fill, etc.)
            value: Value for fill action
            handle_stale: Handle stale elements
            handle_frames: Search in frames
            handle_shadow: Search in shadow DOM
            wait_stable: Wait for page stability
            
        Returns:
            True if action succeeded
        """
        try:
            # Wait for stability if requested
            if wait_stable:
                self.dynamic_handler.wait_for_dom_stable()
            
            # Try main frame first
            element = self._find_element_anywhere(
                selector,
                handle_frames,
                handle_shadow
            )
            
            if not element:
                logger.error(f"Element not found: {selector}")
                return False
            
            # Execute action with stale protection if needed
            if handle_stale:
                def element_getter():
                    return self._find_element_anywhere(
                        selector,
                        handle_frames,
                        handle_shadow
                    )
                
                def perform_action(el):
                    if action == "click":
                        el.click()
                    elif action == "fill" and value:
                        el.fill(value)
                    elif action == "check":
                        el.check()
                    elif action == "hover":
                        el.hover()
                    else:
                        el.click()  # Default
                
                self.stale_handler.safe_execute(
                    element_getter,
                    perform_action
                )
            else:
                # Direct execution
                if action == "click":
                    element.click()
                elif action == "fill" and value:
                    element.fill(value)
                elif action == "check":
                    element.check()
                elif action == "hover":
                    element.hover()
            
            logger.info(f"Successfully performed {action} on {selector}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to interact with {selector}: {e}")
            return False
    
    def _find_element_anywhere(
        self,
        selector: str,
        search_frames: bool = True,
        search_shadow: bool = True
    ) -> Optional[ElementHandle]:
        """Find element anywhere in the page.
        
        Args:
            selector: Element selector
            search_frames: Search in iframes
            search_shadow: Search in shadow DOM
            
        Returns:
            Element handle or None
        """
        # Try main page
        element = self.page.query_selector(selector)
        if element:
            return element
        
        # Try frames
        if search_frames:
            frame = self.frame_handler.find_frame_with_element(selector)
            if frame:
                return frame.query_selector(selector)
        
        # Try shadow DOM (requires special handling)
        if search_shadow:
            # Minimal shadow handling: try evaluating to pierce simple shadow roots
            try:
                handle = None
                if page:
                    handle = page.evaluate_handle("() => document.querySelector(arguments[0])", selector)
                return handle
            except Exception:
                return None
        
        return None
    
    def prepare_page_for_automation(self) -> None:
        """Prepare page for automation by handling common issues."""
        try:
            # Dismiss cookie banners
            self._dismiss_cookie_banners()
            
            # Close popups
            self._close_popups()
            
            # Handle lazy loading
            self.dynamic_handler.handle_lazy_loading()
            
            # Setup SPA listeners
            self.spa_handler.setup_route_listener()
            
            logger.info("Page prepared for automation")
            
        except Exception as e:
            logger.error(f"Error preparing page: {e}")
    
    def _dismiss_cookie_banners(self) -> None:
        """Dismiss common cookie consent banners."""
        common_selectors = [
            "button:has-text('Accept')",
            "button:has-text('Accept all')",
            "button:has-text('I agree')",
            "[class*='cookie'] button:has-text('OK')",
            "#onetrust-accept-btn-handler",
            ".cookie-consent-accept",
        ]
        
        for selector in common_selectors:
            try:
                button = self.page.query_selector(selector)
                if button and button.is_visible():
                    button.click()
                    logger.debug(f"Dismissed cookie banner: {selector}")
                    time.sleep(0.5)
                    break
            except Exception:
                continue
    
    def _close_popups(self) -> None:
        """Close common popup dialogs."""
        popup_selectors = [
            "[aria-label='Close']",
            "button:has-text('×')",
            "button:has-text('X')",
            ".modal-close",
            ".popup-close",
            "[class*='close-button']"
        ]
        
        for selector in popup_selectors:
            try:
                close_btn = self.page.query_selector(selector)
                if close_btn and close_btn.is_visible():
                    close_btn.click()
                    logger.debug(f"Closed popup: {selector}")
                    time.sleep(0.5)
            except Exception:
                continue


__all__ = [
    "ComplexScenarioHandler",
    "StaleElementHandler",
    "DynamicContentHandler",
    "FrameHandler",
    "ShadowDOMHandler",
    "SPANavigationHandler",
    "WaitStrategy"
]