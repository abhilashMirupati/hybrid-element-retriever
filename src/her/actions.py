"""Production-ready action execution with comprehensive edge case handling."""

import time
import logging
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ActionType(Enum):
    """Supported action types."""
    CLICK = "click"
    TYPE = "type"
    SELECT = "select"
    CHECK = "check"
    HOVER = "hover"
    SCROLL = "scroll"
    WAIT = "wait"


@dataclass
class ActionResult:
    """Result of an action execution."""
    success: bool
    action_type: ActionType
    selector: str
    frame_path: str = "main"
    frame_id: Optional[str] = None
    frame_url: Optional[str] = None
    waits: Dict[str, bool] = field(default_factory=dict)
    post_action: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    retries: int = 0
    strategy_used: str = "primary"
    duration_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "success": self.success,
            "action_type": self.action_type.value,
            "selector": self.selector,
            "frame": {
                "used_frame_id": self.frame_id or "",
                "frame_url": self.frame_url or "",
                "frame_path": self.frame_path
            },
            "waits": {
                "readyState_ok": self.waits.get("readyState_ok", False),
                "network_idle_ok": self.waits.get("network_idle_ok", False),
                "spinner_cleared": self.waits.get("spinner_cleared", False),
                "overlay_closed": self.waits.get("overlay_closed", False)
            },
            "post_action": {
                "url_changed": self.post_action.get("url_changed", False),
                "dom_changed": self.post_action.get("dom_changed", False),
                "value_set": self.post_action.get("value_set", False),
                "toggled": self.post_action.get("toggled", False)
            },
            "error": self.error or "",
            "retries": self.retries,
            "strategy_used": self.strategy_used,
            "duration_ms": self.duration_ms
        }


class ActionExecutor:
    """Executes actions with comprehensive edge case handling."""
    
    # Spinner/loading selectors to wait for disappearance
    SPINNER_SELECTORS = [
        "[role='progressbar']",
        ".spinner",
        ".loading",
        ".loader",
        ".MuiBackdrop-root",
        "[data-testid='loading']",
        "[aria-busy='true']",
        ".skeleton",
        ".shimmer",
        "[class*='loading']",
        "[class*='spinner']"
    ]
    
    # Safe auto-close selectors for overlays
    SAFE_CLOSE_SELECTORS = [
        "button:has-text('Accept')",
        "button:has-text('OK')",
        "button:has-text('Close')",
        "[aria-label='Close']",
        "[data-testid='modal-close']",
        ".cookie-banner button:has-text('Accept')",
        ".cookie-consent button:has-text('Accept')",
        "[data-testid='cookie-accept']",
        "button:has-text('Got it')",
        "button:has-text('Dismiss')"
    ]
    
    # Dangerous selectors to avoid auto-clicking
    DANGER_SELECTORS = [
        "[data-danger]",
        ".danger",
        ".destructive",
        "button:has-text('Delete')",
        "button:has-text('Remove')",
        "button:has-text('Cancel')",
        "button:has-text('Decline')",
        "[aria-label*='Delete']",
        "[data-testid*='delete']"
    ]
    
    def __init__(self, page: Any = None, timeout: float = 15.0, network_idle_ms: int = 500):
        """Initialize action executor.
        
        Args:
            page: Playwright page or similar (optional)
            timeout: Maximum wait time in seconds
            network_idle_ms: Network idle window in milliseconds
        """
        self.page = page
        self.timeout = timeout
        self.network_idle_ms = network_idle_ms
        self._network_requests = set()
        self._last_network_activity = time.time()
        self._setup_network_tracking()
    
    def _setup_network_tracking(self) -> None:
        """Setup network request tracking for idle detection."""
        if not self.page:
            return
            
        def on_request(request):
            self._network_requests.add(request.url)
            self._last_network_activity = time.time()
        
        def on_response(response):
            self._network_requests.discard(response.url)
            self._last_network_activity = time.time()
        
        def on_request_failed(request):
            self._network_requests.discard(request.url)
        
        try:
            self.page.on("request", on_request)
            self.page.on("response", on_response)
            self.page.on("requestfailed", on_request_failed)
        except Exception as e:
            logger.warning(f"Failed to setup network tracking: {e}")
    
    def wait_for_idle(self, timeout: Optional[float] = None) -> Dict[str, bool]:
        """Wait for page to be idle with comprehensive checks.
        
        Returns:
            Dictionary of wait results
        """
        timeout = timeout or self.timeout
        start = time.time()
        waits = {
            "readyState_ok": False,
            "network_idle_ok": False,
            "spinner_cleared": False,
            "overlay_closed": False
        }
        
        # Wait for document ready
        try:
            ready_state = self.page.evaluate("document.readyState")
            if ready_state != "complete":
                self.page.wait_for_load_state("domcontentloaded", timeout=timeout * 1000)
                self.page.wait_for_load_state("load", timeout=timeout * 1000)
            waits["readyState_ok"] = True
        except Exception as e:
            logger.debug(f"Ready state wait failed: {e}")
        
        # Wait for network idle
        waits["network_idle_ok"] = self._wait_for_network_idle(timeout - (time.time() - start))
        
        # Wait for spinners to disappear
        waits["spinner_cleared"] = self._wait_for_spinners_gone(timeout - (time.time() - start))
        
        # Try to close overlays
        waits["overlay_closed"] = self._try_close_overlays()
        
        return waits
    
    def _wait_for_network_idle(self, timeout: float) -> bool:
        """Wait for network to be idle."""
        start = time.time()
        
        while time.time() - start < timeout:
            if not self._network_requests:
                idle_duration = (time.time() - self._last_network_activity) * 1000
                if idle_duration >= self.network_idle_ms:
                    return True
            time.sleep(0.1)
        
        return False
    
    def _wait_for_spinners_gone(self, timeout: float) -> bool:
        """Wait for all spinners/loaders to disappear."""
        start = time.time()
        
        for selector in self.SPINNER_SELECTORS:
            if time.time() - start >= timeout:
                return False
                
            try:
                self.page.wait_for_selector(
                    selector,
                    state="hidden",
                    timeout=(timeout - (time.time() - start)) * 1000
                )
            except Exception:
                # Selector not found or already hidden
                pass
        
        return True
    
    def _try_close_overlays(self) -> bool:
        """Try to safely close overlays."""
        closed_any = False
        
        for selector in self.SAFE_CLOSE_SELECTORS:
            try:
                # Check if selector exists and is not in danger list
                element = self.page.query_selector(selector)
                if element:
                    # Verify it's not a dangerous button
                    is_dangerous = False
                    for danger in self.DANGER_SELECTORS:
                        if self.page.query_selector(f"{selector}{danger}"):
                            is_dangerous = True
                            break
                    
                    if not is_dangerous:
                        element.click(timeout=1000)
                        closed_any = True
                        time.sleep(0.5)  # Brief pause after closing
            except Exception:
                pass
        
        return closed_any
    
    def execute_click(
        self,
        selector: str,
        frame_path: Optional[str] = None,
        verify: bool = True
    ) -> ActionResult:
        """Execute click action with full edge case handling.
        
        Args:
            selector: Element selector
            frame_path: Optional frame path
            verify: Whether to verify post-action
            
        Returns:
            ActionResult with comprehensive metadata
        """
        start_time = time.time()
        result = ActionResult(
            success=False,
            action_type=ActionType.CLICK,
            selector=selector,
            frame_path=frame_path or "main"
        )
        
        # Pre-action waits
        result.waits = self.wait_for_idle()
        
        # Get initial state for verification
        initial_url = self.page.url if self.page else ""
        initial_dom_hash = self._get_dom_hash()
        
        # Switch to frame if needed
        target_frame = self._switch_to_frame(frame_path) if frame_path else self.page
        if target_frame:
            result.frame_id = self._get_frame_id(target_frame)
            result.frame_url = self._get_frame_url(target_frame)
        
        # Try click with retries
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Scroll element into view first
                self._scroll_into_view(selector, target_frame)
                
                # Check for occlusion
                if self._is_occluded(selector, target_frame):
                    self._try_close_overlays()
                    time.sleep(0.5)
                
                # Perform click
                target_frame.click(selector, timeout=5000)
                result.success = True
                result.retries = attempt
                break
                
            except Exception as e:
                logger.debug(f"Click attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                else:
                    result.error = str(e)
        
        # Post-action verification
        if verify and result.success:
            time.sleep(0.5)  # Brief pause for DOM updates
            
            result.post_action["url_changed"] = self.page.url != initial_url
            result.post_action["dom_changed"] = self._get_dom_hash() != initial_dom_hash
            
            # Check for navigation or significant DOM change
            if not result.post_action["url_changed"] and not result.post_action["dom_changed"]:
                # Try to detect toggle state change
                try:
                    element = target_frame.query_selector(selector)
                    if element:
                        aria_pressed = element.get_attribute("aria-pressed")
                        aria_expanded = element.get_attribute("aria-expanded")
                        result.post_action["toggled"] = bool(aria_pressed or aria_expanded)
                except Exception:
                    pass
        
        result.duration_ms = (time.time() - start_time) * 1000
        return result
    
    def execute_type(
        self,
        selector: str,
        text: str,
        frame_path: Optional[str] = None,
        clear_first: bool = True,
        verify: bool = True
    ) -> ActionResult:
        """Execute type action with full edge case handling.
        
        Args:
            selector: Element selector
            text: Text to type
            frame_path: Optional frame path
            clear_first: Whether to clear existing text
            verify: Whether to verify post-action
            
        Returns:
            ActionResult with comprehensive metadata
        """
        start_time = time.time()
        result = ActionResult(
            success=False,
            action_type=ActionType.TYPE,
            selector=selector,
            frame_path=frame_path or "main"
        )
        
        # Pre-action waits
        result.waits = self.wait_for_idle()
        
        # Switch to frame if needed
        target_frame = self._switch_to_frame(frame_path) if frame_path else self.page
        if target_frame:
            result.frame_id = self._get_frame_id(target_frame)
            result.frame_url = self._get_frame_url(target_frame)
        
        # Try type with retries
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Scroll element into view
                self._scroll_into_view(selector, target_frame)
                
                # Clear and type
                if clear_first:
                    target_frame.fill(selector, "")
                
                # Handle masked inputs carefully
                element = target_frame.query_selector(selector)
                if element:
                    input_type = element.get_attribute("type")
                    if input_type in ["password", "tel", "ssn"]:
                        # Type slowly for masked inputs
                        target_frame.type(selector, text, delay=50)
                    else:
                        target_frame.fill(selector, text)
                
                result.success = True
                result.retries = attempt
                break
                
            except Exception as e:
                logger.debug(f"Type attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                else:
                    result.error = str(e)
        
        # Post-action verification
        if verify and result.success:
            time.sleep(0.2)  # Brief pause for value update
            
            try:
                actual_value = target_frame.evaluate(f"""
                    document.querySelector('{selector}').value
                """)
                result.post_action["value_set"] = str(actual_value) == str(text)
            except Exception:
                result.post_action["value_set"] = False
        
        result.duration_ms = (time.time() - start_time) * 1000
        return result
    
    def _switch_to_frame(self, frame_path: str) -> Optional[Any]:
        """Switch to specified frame."""
        if not frame_path or frame_path == "main":
            return self.page
        
        try:
            # Handle nested frames
            frames = frame_path.split("/")
            current = self.page
            
            for frame_selector in frames:
                if frame_selector:
                    frame_element = current.query_selector(frame_selector)
                    if frame_element:
                        current = frame_element.content_frame()
            
            return current
        except Exception as e:
            logger.warning(f"Failed to switch to frame {frame_path}: {e}")
            return None
    
    def _get_frame_id(self, frame: Any) -> Optional[str]:
        """Get frame ID."""
        try:
            return frame.evaluate("window.frameElement ? window.frameElement.id : ''")
        except Exception:
            return None
    
    def _get_frame_url(self, frame: Any) -> Optional[str]:
        """Get frame URL."""
        try:
            return frame.url
        except Exception:
            return None
    
    def _scroll_into_view(self, selector: str, frame: Any) -> None:
        """Scroll element into view."""
        try:
            frame.evaluate(f"""
                document.querySelector('{selector}')?.scrollIntoView({{
                    behavior: 'smooth',
                    block: 'center'
                }})
            """)
            time.sleep(0.3)  # Wait for scroll animation
        except Exception:
            pass
    
    def _is_occluded(self, selector: str, frame: Any) -> bool:
        """Check if element is occluded by another element."""
        try:
            return frame.evaluate(f"""
                (() => {{
                    const elem = document.querySelector('{selector}');
                    if (!elem) return false;
                    
                    const rect = elem.getBoundingClientRect();
                    const centerX = rect.left + rect.width / 2;
                    const centerY = rect.top + rect.height / 2;
                    
                    const topElement = document.elementFromPoint(centerX, centerY);
                    return topElement !== elem && !elem.contains(topElement);
                }})()
            """)
        except Exception:
            return False
    
    def _get_dom_hash(self) -> str:
        """Get simple DOM hash for change detection."""
        try:
            return str(hash(self.page.content()[:1000]))
        except Exception:
            return "0"