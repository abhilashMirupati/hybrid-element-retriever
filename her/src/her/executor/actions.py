"""Action executor for performing web interactions."""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from playwright.async_api import Page, Frame, Locator, TimeoutError as PlaywrightTimeout

from her.locator.verify import LocatorVerifier, VerificationResult

logger = logging.getLogger(__name__)


class ActionType(Enum):
    """Supported action types."""
    CLICK = "click"
    TYPE = "type"
    SELECT = "select"
    CHECK = "check"
    UNCHECK = "uncheck"
    HOVER = "hover"
    FOCUS = "focus"
    CLEAR = "clear"
    UPLOAD = "upload"
    PRESS = "press"
    WAIT = "wait"
    

@dataclass
class ActionResult:
    """Result of action execution."""
    success: bool
    action_type: str
    selector: str
    value: Optional[Any]
    duration_ms: float
    wait_before_ms: float
    wait_after_ms: float
    post_action: Dict[str, Any]
    error: Optional[str] = None
    retries: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
        

@dataclass
class PostActionState:
    """State captured after action."""
    url_changed: bool
    new_url: Optional[str]
    dom_changed: bool
    value_changed: bool
    new_value: Optional[str]
    toggle_state: Optional[bool]
    overlay_closed: bool
    spinner_gone: bool
    

class ActionExecutor:
    """Executes actions on web elements with safety checks."""
    
    # Default wait times (ms)
    DEFAULT_WAIT_BEFORE = 100
    DEFAULT_WAIT_AFTER = 500
    DEFAULT_IDLE_TIMEOUT = 3000
    DEFAULT_ACTION_TIMEOUT = 30000
    
    def __init__(self, page: Page):
        self.page = page
        self.verifier = LocatorVerifier(page)
        self._overlay_selectors = [
            '.modal', '.overlay', '.popup', '.cookie-banner',
            '[role="dialog"]', '[aria-modal="true"]'
        ]
        self._spinner_selectors = [
            '.spinner', '.loader', '.loading', '.progress',
            '[aria-busy="true"]', '.sk-spinner'
        ]
        
    async def execute(
        self,
        action_type: ActionType,
        selector: str,
        value: Optional[Any] = None,
        strategy: str = 'css',
        frame_path: Optional[List[str]] = None,
        wait_before_ms: Optional[int] = None,
        wait_after_ms: Optional[int] = None,
        auto_close_overlays: bool = True,
        scroll_into_view: bool = True,
        verify_after: bool = True
    ) -> ActionResult:
        """Execute an action on an element.
        
        Args:
            action_type: Type of action to perform
            selector: Element selector
            value: Value for type/select actions
            strategy: Selector strategy
            frame_path: Frame path if in iframe
            wait_before_ms: Wait before action
            wait_after_ms: Wait after action
            auto_close_overlays: Auto-close overlays
            scroll_into_view: Scroll element into view
            verify_after: Verify action success
            
        Returns:
            ActionResult with execution details
        """
        start_time = time.time()
        
        # Set wait times
        wait_before = wait_before_ms or self.DEFAULT_WAIT_BEFORE
        wait_after = wait_after_ms or self.DEFAULT_WAIT_AFTER
        
        # Wait for idle state
        await self.wait_for_idle()
        
        # Auto-close overlays if needed
        if auto_close_overlays:
            await self._auto_close_overlays()
            
        # Wait before action
        if wait_before > 0:
            await asyncio.sleep(wait_before / 1000)
            
        # Get initial state
        initial_url = self.page.url
        initial_value = None
        
        try:
            # Get target frame
            frame = await self._get_frame(frame_path)
            if not frame:
                return ActionResult(
                    success=False,
                    action_type=action_type.value,
                    selector=selector,
                    value=value,
                    duration_ms=(time.time() - start_time) * 1000,
                    wait_before_ms=wait_before,
                    wait_after_ms=wait_after,
                    post_action={},
                    error="Frame not found"
                )
                
            # Create locator
            locator = self._create_locator(frame, selector, strategy)
            
            # Wait for element
            await locator.wait_for(state='visible', timeout=self.DEFAULT_ACTION_TIMEOUT)
            
            # Scroll into view if needed
            if scroll_into_view:
                await locator.scroll_into_view_if_needed()
                
            # Get initial value for inputs
            if action_type in [ActionType.TYPE, ActionType.CLEAR]:
                try:
                    initial_value = await locator.input_value()
                except:
                    pass
                    
            # Execute action
            await self._perform_action(locator, action_type, value)
            
            # Wait after action
            if wait_after > 0:
                await asyncio.sleep(wait_after / 1000)
                
            # Wait for any navigation/updates
            await self.wait_for_idle()
            
            # Capture post-action state
            post_action = await self._capture_post_action_state(
                initial_url,
                initial_value,
                locator,
                action_type
            )
            
            # Verify if requested
            if verify_after and action_type != ActionType.WAIT:
                verification = await self.verifier.verify(
                    selector=selector,
                    strategy=strategy,
                    frame_path=frame_path
                )
                if not verification.ok and action_type == ActionType.CLICK:
                    # Click might have navigated away, still consider success
                    if post_action.get('url_changed'):
                        logger.info("Click navigated to new page")
                        
            duration_ms = (time.time() - start_time) * 1000
            
            return ActionResult(
                success=True,
                action_type=action_type.value,
                selector=selector,
                value=value,
                duration_ms=duration_ms,
                wait_before_ms=wait_before,
                wait_after_ms=wait_after,
                post_action=post_action
            )
            
        except Exception as e:
            logger.error(f"Action failed: {e}")
            duration_ms = (time.time() - start_time) * 1000
            
            return ActionResult(
                success=False,
                action_type=action_type.value,
                selector=selector,
                value=value,
                duration_ms=duration_ms,
                wait_before_ms=wait_before,
                wait_after_ms=wait_after,
                post_action={},
                error=str(e)
            )
            
    async def _perform_action(
        self,
        locator: Locator,
        action_type: ActionType,
        value: Optional[Any]
    ) -> None:
        """Perform the actual action.
        
        Args:
            locator: Target element locator
            action_type: Type of action
            value: Action value
        """
        if action_type == ActionType.CLICK:
            await locator.click()
            
        elif action_type == ActionType.TYPE:
            if value is not None:
                await locator.fill(str(value))
                
        elif action_type == ActionType.SELECT:
            if value is not None:
                await locator.select_option(value)
                
        elif action_type == ActionType.CHECK:
            await locator.check()
            
        elif action_type == ActionType.UNCHECK:
            await locator.uncheck()
            
        elif action_type == ActionType.HOVER:
            await locator.hover()
            
        elif action_type == ActionType.FOCUS:
            await locator.focus()
            
        elif action_type == ActionType.CLEAR:
            await locator.clear()
            
        elif action_type == ActionType.UPLOAD:
            if value is not None:
                await locator.set_input_files(value)
                
        elif action_type == ActionType.PRESS:
            if value is not None:
                await locator.press(str(value))
                
        elif action_type == ActionType.WAIT:
            # Just wait, no action
            if value:
                await asyncio.sleep(float(value) / 1000)
                
        else:
            raise ValueError(f"Unknown action type: {action_type}")
            
    async def wait_for_idle(
        self,
        timeout_ms: Optional[int] = None
    ) -> None:
        """Wait for page to reach idle state.
        
        Waits for:
        - Document ready state
        - Network idle
        - No spinners
        
        Args:
            timeout_ms: Maximum wait time
        """
        timeout = timeout_ms or self.DEFAULT_IDLE_TIMEOUT
        start_time = time.time()
        
        # Wait for load state
        try:
            await self.page.wait_for_load_state('networkidle', timeout=timeout)
        except PlaywrightTimeout:
            logger.debug("Network idle timeout, continuing")
            
        # Wait for document ready
        await self.page.evaluate(
            """() => {
                return new Promise((resolve) => {
                    if (document.readyState === 'complete') {
                        resolve();
                    } else {
                        window.addEventListener('load', resolve);
                    }
                });
            }"""
        )
        
        # Wait for spinners to disappear
        await self._wait_for_spinners_gone()
        
        elapsed = (time.time() - start_time) * 1000
        logger.debug(f"Waited {elapsed:.0f}ms for idle state")
        
    async def _wait_for_spinners_gone(
        self,
        timeout_ms: int = 5000
    ) -> None:
        """Wait for loading spinners to disappear.
        
        Args:
            timeout_ms: Maximum wait time
        """
        for selector in self._spinner_selectors:
            try:
                spinner = self.page.locator(selector).first
                if await spinner.count() > 0:
                    await spinner.wait_for(state='hidden', timeout=timeout_ms)
            except:
                # Spinner might not exist or already hidden
                continue
                
    async def _auto_close_overlays(self) -> bool:
        """Auto-close overlays like cookie banners.
        
        Returns:
            True if any overlay was closed
        """
        closed_any = False
        
        # Common close button selectors
        close_selectors = [
            'button:has-text("Accept")',
            'button:has-text("OK")',
            'button:has-text("Close")',
            'button:has-text("Got it")',
            'button:has-text("Agree")',
            '[aria-label="Close"]',
            '.close-button',
            '.modal-close'
        ]
        
        for overlay_sel in self._overlay_selectors:
            try:
                overlay = self.page.locator(overlay_sel).first
                if await overlay.count() > 0 and await overlay.is_visible():
                    # Try to find and click close button
                    for close_sel in close_selectors:
                        close_btn = overlay.locator(close_sel).first
                        if await close_btn.count() > 0:
                            await close_btn.click()
                            await asyncio.sleep(0.5)  # Wait for animation
                            closed_any = True
                            logger.info(f"Auto-closed overlay: {overlay_sel}")
                            break
            except:
                continue
                
        return closed_any
        
    async def _get_frame(self, frame_path: Optional[List[str]]) -> Optional[Frame]:
        """Get frame by path.
        
        Args:
            frame_path: List of frame names/URLs
            
        Returns:
            Frame object or None
        """
        if not frame_path:
            return self.page.main_frame
            
        current_frame = self.page.main_frame
        
        for frame_spec in frame_path:
            found = False
            for child_frame in current_frame.child_frames:
                if (child_frame.name == frame_spec or
                    frame_spec in child_frame.url):
                    current_frame = child_frame
                    found = True
                    break
                    
            if not found:
                return None
                
        return current_frame
        
    def _create_locator(self, frame: Frame, selector: str, strategy: str) -> Locator:
        """Create Playwright locator.
        
        Args:
            frame: Target frame
            selector: Selector string
            strategy: Selector strategy
            
        Returns:
            Locator object
        """
        if strategy == 'xpath':
            return frame.locator(f"xpath={selector}")
        elif strategy == 'text':
            if selector.startswith('text='):
                return frame.locator(selector)
            return frame.locator(f"text={selector}")
        elif strategy == 'aria':
            if selector.startswith('aria-label='):
                aria_value = selector[11:]
                return frame.locator(f"[aria-label='{aria_value}']")
            return frame.locator(f"[aria-label='{selector}']")
        else:
            # Default to CSS
            # Handle jQuery-style :contains
            if ':contains(' in selector:
                base = selector.split(':contains(')[0]
                text = selector.split(":contains('")[1].split("')")[0] if ":contains('" in selector else ""
                if text:
                    return frame.locator(f"{base}:has-text('{text}')")
            return frame.locator(selector)
            
    async def _capture_post_action_state(
        self,
        initial_url: str,
        initial_value: Optional[str],
        locator: Locator,
        action_type: ActionType
    ) -> Dict[str, Any]:
        """Capture state after action.
        
        Args:
            initial_url: URL before action
            initial_value: Value before action
            locator: Element locator
            action_type: Type of action performed
            
        Returns:
            Dictionary of post-action state
        """
        state = {}
        
        # Check URL change
        current_url = self.page.url
        state['url_changed'] = current_url != initial_url
        if state['url_changed']:
            state['new_url'] = current_url
            
        # Check DOM change (simplified)
        state['dom_changed'] = state['url_changed']  # Assume DOM changed if URL changed
        
        # Check value change for inputs
        if action_type in [ActionType.TYPE, ActionType.CLEAR, ActionType.SELECT]:
            try:
                new_value = await locator.input_value()
                state['value_changed'] = new_value != initial_value
                state['new_value'] = new_value
            except:
                state['value_changed'] = False
                
        # Check toggle state for checkboxes
        if action_type in [ActionType.CHECK, ActionType.UNCHECK]:
            try:
                state['toggle_state'] = await locator.is_checked()
            except:
                pass
                
        # Check if overlays were closed
        state['overlay_closed'] = False
        for overlay_sel in self._overlay_selectors:
            try:
                if await self.page.locator(overlay_sel).count() == 0:
                    state['overlay_closed'] = True
                    break
            except:
                continue
                
        # Check if spinners are gone
        state['spinner_gone'] = True
        for spinner_sel in self._spinner_selectors:
            try:
                if await self.page.locator(spinner_sel).is_visible():
                    state['spinner_gone'] = False
                    break
            except:
                continue
                
        return state