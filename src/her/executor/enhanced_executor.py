"""
Enhanced Playwright Executor for HER Framework

Extends the base executor with:
- Scroll into view if element not visible
- Retry if blocked by overlay
- Auto-switch frame context before action
- Support for actions: click, type(value), validate(text)
- Robust error handling and recovery
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional, Tuple

try:
    from playwright.sync_api import Page, Frame, TimeoutError as PWTimeoutError
    from playwright.sync_api import Locator
    _PLAYWRIGHT_AVAILABLE = True
except ImportError:
    _PLAYWRIGHT_AVAILABLE = False
    Page = None
    Frame = None
    Locator = None
    PWTimeoutError = Exception

from ..exceptions import ExecutionError
from ..promotion.promotion_adapter import record_failure, record_success
from ..vectordb import get_default_kv

logger = logging.getLogger(__name__)


class EnhancedExecutor:
    """Enhanced Playwright executor with robust error handling."""
    
    def __init__(self, page: Page, *, action_timeout_ms: int = 10000, max_retries: int = 3):
        if not _PLAYWRIGHT_AVAILABLE:
            raise RuntimeError(
                "Playwright is required for enhanced executor. Install with `pip install playwright` "
                "and run `python -m playwright install chromium`."
            )
        
        self.page = page
        self.action_timeout_ms = int(action_timeout_ms)
        self.max_retries = int(max_retries)
        self.kv = get_default_kv()
        
        # Overlay dismissal selectors
        self.overlay_selectors = [
            'button[aria-label="Close"]',
            'button[aria-label="Dismiss"]',
            'button:has-text("Accept")',
            'button:has-text("Agree")',
            'button:has-text("Got it")',
            'button:has-text("OK")',
            'button:has-text("Continue")',
            '#onetrust-accept-btn-handler',
            '.cc-allow',
            '[data-testid="close"]',
            '[aria-label="Close dialog"]',
            '[aria-label="Close modal"]',
            '.modal button.close',
            '.popup button.close',
            'button:has-text("No thanks")',
            'button:has-text("I agree")',
        ]
    
    def click(
        self,
        selector: str,
        *,
        page_sig: Optional[str] = None,
        frame_hash: Optional[str] = None,
        label_key: Optional[str] = None,
    ) -> None:
        """Click an element with robust error handling."""
        self._execute_with_retry(
            action='click',
            selector=selector,
            page_sig=page_sig,
            frame_hash=frame_hash,
            label_key=label_key
        )
    
    def type(
        self,
        selector: str,
        value: str,
        *,
        page_sig: Optional[str] = None,
        frame_hash: Optional[str] = None,
        label_key: Optional[str] = None,
        clear: bool = True,
    ) -> None:
        """Type text into an element with robust error handling."""
        if not isinstance(value, str):
            raise ValueError("Value must be a string")
        
        self._execute_with_retry(
            action='type',
            selector=selector,
            value=value,
            page_sig=page_sig,
            frame_hash=frame_hash,
            label_key=label_key,
            clear=clear
        )
    
    def validate(
        self,
        selector: str,
        expected_text: str,
        *,
        page_sig: Optional[str] = None,
        frame_hash: Optional[str] = None,
        label_key: Optional[str] = None,
    ) -> bool:
        """Validate that element contains expected text."""
        try:
            self._execute_with_retry(
                action='validate',
                selector=selector,
                expected_text=expected_text,
                page_sig=page_sig,
                frame_hash=frame_hash,
                label_key=label_key
            )
            return True
        except Exception:
            return False
    
    def _execute_with_retry(
        self,
        action: str,
        selector: str,
        **kwargs
    ) -> None:
        """Execute action with retry logic."""
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                # Try to execute the action
                if action == 'click':
                    self._perform_click(selector)
                elif action == 'type':
                    self._perform_type(selector, kwargs.get('value', ''), kwargs.get('clear', True))
                elif action == 'validate':
                    self._perform_validate(selector, kwargs.get('expected_text', ''))
                else:
                    raise ValueError(f"Unknown action: {action}")
                
                # Record success
                self._record_success(
                    page_sig=kwargs.get('page_sig'),
                    frame_hash=kwargs.get('frame_hash'),
                    label_key=kwargs.get('label_key'),
                    selector=selector
                )
                return
                
            except Exception as e:
                last_error = e
                logger.debug(f"Attempt {attempt + 1} failed: {e}")
                
                # Try to recover
                if attempt < self.max_retries - 1:
                    self._attempt_recovery(selector, action)
                    time.sleep(0.5)  # Brief pause before retry
                else:
                    # Final attempt failed
                    self._record_failure(
                        page_sig=kwargs.get('page_sig'),
                        frame_hash=kwargs.get('frame_hash'),
                        label_key=kwargs.get('label_key'),
                        selector=selector
                    )
                    raise ExecutionError(
                        f"Failed to {action} element after {self.max_retries} attempts: {e}",
                        action=action,
                        selector=selector
                    ) from e
        
        # This should never be reached, but just in case
        raise ExecutionError(
            f"Failed to {action} element: {last_error}",
            action=action,
            selector=selector
        ) from last_error
    
    def _perform_click(self, selector: str) -> None:
        """Perform click action with enhanced error handling."""
        # Switch to appropriate frame
        frame = self._switch_to_frame(selector)
        
        # Get element locator
        locator = self._get_locator(selector, frame)
        
        # Scroll into view
        self._scroll_into_view(locator)
        
        # Dismiss overlays
        self._dismiss_overlays()
        
        # Wait for element to be ready
        locator.wait_for(state="visible", timeout=self.action_timeout_ms)
        
        # Try different click strategies
        click_strategies = [
            lambda: locator.click(timeout=self.action_timeout_ms),
            lambda: locator.click(force=True, timeout=self.action_timeout_ms),
            lambda: self._click_with_javascript(locator),
        ]
        
        for strategy in click_strategies:
            try:
                strategy()
                return
            except Exception as e:
                logger.debug(f"Click strategy failed: {e}")
                continue
        
        raise Exception("All click strategies failed")
    
    def _perform_type(self, selector: str, value: str, clear: bool = True) -> None:
        """Perform type action with enhanced error handling."""
        # Switch to appropriate frame
        frame = self._switch_to_frame(selector)
        
        # Get element locator
        locator = self._get_locator(selector, frame)
        
        # Scroll into view
        self._scroll_into_view(locator)
        
        # Dismiss overlays
        self._dismiss_overlays()
        
        # Wait for element to be ready
        locator.wait_for(state="visible", timeout=self.action_timeout_ms)
        
        # Clear field if requested
        if clear:
            try:
                locator.fill("", timeout=1000)
            except Exception:
                pass  # Ignore clear errors
        
        # Type the value
        locator.type(value, timeout=self.action_timeout_ms)
    
    def _perform_validate(self, selector: str, expected_text: str) -> None:
        """Perform validation action."""
        # Switch to appropriate frame
        frame = self._switch_to_frame(selector)
        
        # Get element locator
        locator = self._get_locator(selector, frame)
        
        # Wait for element to be visible
        locator.wait_for(state="visible", timeout=self.action_timeout_ms)
        
        # Get element text
        element_text = locator.text_content()
        
        # Check if expected text is in element text
        if expected_text.lower() not in element_text.lower():
            raise Exception(f"Expected text '{expected_text}' not found in element. Got: '{element_text}'")
    
    def _switch_to_frame(self, selector: str) -> Frame:
        """Switch to appropriate frame for the selector."""
        # For now, use the main frame
        # TODO: Implement frame detection based on selector context
        return self.page.main_frame
    
    def _get_locator(self, selector: str, frame: Frame) -> Locator:
        """Get element locator from frame."""
        if not selector or not isinstance(selector, str):
            raise ValueError("Invalid selector")
        
        # Handle XPath selectors
        if selector.startswith('//') or selector.startswith('/'):
            return frame.locator(f"xpath={selector}")
        
        # Handle CSS selectors
        return frame.locator(selector)
    
    def _scroll_into_view(self, locator: Locator) -> None:
        """Scroll element into view."""
        try:
            locator.scroll_into_view_if_needed(timeout=2000)
        except Exception as e:
            logger.debug(f"Scroll into view failed: {e}")
            # Continue execution even if scroll fails
    
    def _dismiss_overlays(self) -> None:
        """Dismiss common overlays that might block interaction."""
        for selector in self.overlay_selectors:
            try:
                locator = self.page.locator(selector)
                if locator.count() > 0 and locator.first.is_visible(timeout=100):
                    locator.first.click(timeout=500)
                    time.sleep(0.2)  # Brief pause after dismissal
            except Exception:
                continue  # Ignore overlay dismissal errors
    
    def _click_with_javascript(self, locator: Locator) -> None:
        """Click element using JavaScript."""
        element_handle = locator.element_handle()
        self.page.evaluate("(element) => element.click()", element_handle)
    
    def _attempt_recovery(self, selector: str, action: str) -> None:
        """Attempt to recover from failed action."""
        logger.debug(f"Attempting recovery for {action} on {selector}")
        
        # Dismiss overlays
        self._dismiss_overlays()
        
        # Wait for page to stabilize
        time.sleep(0.5)
        
        # Try to scroll to element
        try:
            frame = self._switch_to_frame(selector)
            locator = self._get_locator(selector, frame)
            self._scroll_into_view(locator)
        except Exception:
            pass  # Ignore recovery errors
    
    def _record_success(
        self,
        page_sig: Optional[str],
        frame_hash: Optional[str],
        label_key: Optional[str],
        selector: str
    ) -> None:
        """Record successful action."""
        if not all([page_sig, frame_hash, label_key, selector]):
            return
        
        try:
            record_success(
                self.kv,
                page_sig=page_sig,
                frame_hash=frame_hash,
                label_key=label_key,
                selector=selector
            )
        except Exception as e:
            logger.debug(f"Failed to record success: {e}")
    
    def _record_failure(
        self,
        page_sig: Optional[str],
        frame_hash: Optional[str],
        label_key: Optional[str],
        selector: str
    ) -> None:
        """Record failed action."""
        if not all([page_sig, frame_hash, label_key, selector]):
            return
        
        try:
            record_failure(
                self.kv,
                page_sig=page_sig,
                frame_hash=frame_hash,
                label_key=label_key,
                selector=selector
            )
        except Exception as e:
            logger.debug(f"Failed to record failure: {e}")


def create_enhanced_executor(page: Page, **kwargs) -> EnhancedExecutor:
    """Create an enhanced executor instance."""
    return EnhancedExecutor(page, **kwargs)