from __future__ import annotations

"""
Strict Playwright Executor with Promotion Recording (Step 6)

- Fail-fast if Playwright isn't installed
- Executes click/type/press using XPath selectors
- Records promotion success/failure into SQLite after the action outcome

NOTE:
- We don't "pretend pass" for anything. Missing element or action error -> raises.
- Callers should compute page_sig (stable) and provide frame_hash + label_key for promotion recording.
"""

import time
from typing import Optional

# Fail-fast import guard (no silent fallback)
try:
    from playwright.sync_api import Page
    from playwright.sync_api import TimeoutError as PWTimeoutError
except Exception as e:  # pragma: no cover
    raise RuntimeError(
        "Playwright is required for executor. Install with `pip install playwright` "
        "and run `python -m playwright install chromium`."
    ) from e

from ..promotion.promotion_adapter import record_failure, record_success
from ..vectordb import get_default_kv


class Executor:
    def __init__(self, page: Page, *, action_timeout_ms: int = 10000) -> None:
        self.page = page
        self.action_timeout_ms = int(action_timeout_ms)
        self.kv = get_default_kv()
        self._current_frame = None

    # ---------------- internal helpers ----------------
    def _query_element(self, xpath: str):
        if not xpath or not isinstance(xpath, str):
            raise ValueError("Executor: invalid XPath selector")
        
        # Enhanced frame and shadow DOM support
        return self._locate_element_with_frames_and_shadow(xpath)
    
    def _locate_element_with_frames_and_shadow(self, xpath: str):
        """Locate element with enhanced frame switching and shadow DOM support."""
        # Try main frame first
        try:
            handle = self.page.locator(f"xpath={xpath}")
            if handle.count() > 0:
                return handle
        except Exception:
            pass
        
        # Try all frames
        frames = getattr(self.page, 'frames', [])
        for frame in frames:
            try:
                # Skip main frame (already tried)
                if frame == getattr(self.page, 'main_frame', None):
                    continue
                
                # Switch to frame context
                frame_handle = frame.locator(f"xpath={xpath}")
                if frame_handle.count() > 0:
                    self._current_frame = frame
                    return frame_handle
            except Exception:
                continue
        
        # Try shadow DOM elements
        try:
            shadow_handle = self._locate_in_shadow_dom(xpath)
            if shadow_handle:
                return shadow_handle
        except Exception:
            pass
        
        # Fallback to main frame
        return self.page.locator(f"xpath={xpath}")
    
    def _locate_in_shadow_dom(self, xpath: str):
        """Locate element within shadow DOM."""
        try:
            # Find all shadow root hosts
            shadow_hosts = self.page.query_selector_all('*')
            
            for host in shadow_hosts:
                try:
                    # Check if element has shadow root
                    has_shadow = host.evaluate("element => element.shadowRoot !== null")
                    if not has_shadow:
                        continue
                    
                    # Look for element in shadow DOM
                    shadow_element = host.evaluate(f"""
                        (element, xpath) => {{
                            try {{
                                const shadowRoot = element.shadowRoot;
                                const result = document.evaluate(xpath, shadowRoot, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
                                return result.singleNodeValue;
                            }} catch (e) {{
                                return null;
                            }}
                        }}
                    """, xpath)
                    
                    if shadow_element:
                        # Return a locator for the shadow element
                        return self.page.locator(f"xpath={xpath}")
                        
                except Exception:
                    continue
                    
        except Exception:
            pass
        
        return None
    
    def _switch_to_frame(self, frame_name_or_url: str = None):
        """Switch to a specific frame."""
        try:
            frames = getattr(self.page, 'frames', [])
            
            if frame_name_or_url:
                for frame in frames:
                    if (frame_name_or_url in getattr(frame, 'name', '') or 
                        frame_name_or_url in getattr(frame, 'url', '')):
                        self._current_frame = frame
                        return frame
            
            # If no specific frame requested, use main frame
            self._current_frame = getattr(self.page, 'main_frame', None)
            return self._current_frame
            
        except Exception:
            self._current_frame = None
            return None
    
    def _ensure_element_in_view(self, element):
        """Ensure element is in view with enhanced scrolling."""
        try:
            # Try standard scroll into view
            element.scroll_into_view_if_needed(timeout=2000)
        except Exception:
            try:
                # Fallback: manual scroll calculation
                bbox = element.bounding_box()
                if bbox:
                    viewport = self.page.viewport_size
                    if viewport:
                        # Calculate scroll position to center element
                        center_x = bbox['x'] + bbox['width'] / 2
                        center_y = bbox['y'] + bbox['height'] / 2
                        
                        scroll_x = max(0, center_x - viewport['width'] / 2)
                        scroll_y = max(0, center_y - viewport['height'] / 2)
                        
                        self.page.evaluate(f"window.scrollTo({scroll_x}, {scroll_y})")
            except Exception:
                pass

    def _record(self, ok: bool, *, page_sig: Optional[str], frame_hash: Optional[str], label_key: Optional[str], selector: Optional[str]) -> None:
        if not page_sig or not frame_hash or not label_key or not selector:
            return
        try:
            if ok:
                record_success(self.kv, page_sig=page_sig, frame_hash=frame_hash, label_key=label_key, selector=selector)
            else:
                record_failure(self.kv, page_sig=page_sig, frame_hash=frame_hash, label_key=label_key, selector=selector)
        except Exception:
            # Recording must not mask the action outcome
            pass

    # ---------------- public actions -------------------
    def click(
        self,
        selector: str,
        *,
        page_sig: Optional[str] = None,
        frame_hash: Optional[str] = None,
        label_key: Optional[str] = None,
    ) -> None:
        h = self._query_element(selector)
        ok = False
        try:
            # Enhanced frame and shadow DOM handling
            self._switch_to_frame()
            
            # First try to scroll element into view with enhanced support
            try:
                self._ensure_element_in_view(h.first)
            except Exception:
                pass
            
            # Try to dismiss any overlays first
            try:
                # Common cookie/popup dismiss buttons
                for dismiss_sel in ['button:has-text("Accept")', 'button:has-text("Close")', 
                                   'button[aria-label="Close"]', '#onetrust-accept-btn-handler']:
                    try:
                        dismiss = self.page.locator(dismiss_sel).first
                        if dismiss.is_visible(timeout=100):
                            dismiss.click(timeout=500)
                            time.sleep(0.5)
                    except Exception:
                        continue
            except Exception:
                pass
            
            # Now try the actual click with retries and enhanced frame support
            clicked = False
            for attempt in range(3):
                try:
                    if attempt == 0:
                        # First attempt: wait for visible and click normally
                        h.first.wait_for(state="visible", timeout=self.action_timeout_ms // 2)
                        h.first.click(timeout=self.action_timeout_ms // 2, force=False)
                    elif attempt == 1:
                        # Second attempt: try with JavaScript click (works in frames/shadow DOM)
                        try:
                            if self._current_frame:
                                # Click in frame context
                                self._current_frame.evaluate("(el) => el.click()", h.first.element_handle())
                            else:
                                # Click in main context
                                self.page.evaluate("(el) => el.click()", h.first.element_handle())
                        except Exception:
                            # Fallback to force click
                            h.first.click(force=True, timeout=self.action_timeout_ms // 2)
                    else:
                        # Third attempt: force click
                        h.first.click(force=True, timeout=self.action_timeout_ms // 2)
                    clicked = True
                    break
                except Exception:
                    if attempt < 2:
                        time.sleep(0.5)
                    continue
            
            if not clicked:
                raise TimeoutError(f"Could not click element after 3 attempts")
            ok = True
        except PWTimeoutError as e:
            self._record(False, page_sig=page_sig, frame_hash=frame_hash, label_key=label_key, selector=selector)
            raise TimeoutError(f"Executor.click timeout for selector: {selector}") from e
        except Exception as e:
            self._record(False, page_sig=page_sig, frame_hash=frame_hash, label_key=label_key, selector=selector)
            raise
        else:
            self._record(True, page_sig=page_sig, frame_hash=frame_hash, label_key=label_key, selector=selector)

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
        if not isinstance(value, str):
            raise ValueError("Executor.type value must be a string")
        h = self._query_element(selector)
        try:
            h.first.wait_for(state="visible", timeout=self.action_timeout_ms)
            if clear:
                h.first.fill("", timeout=self.action_timeout_ms)
            h.first.type(value, timeout=self.action_timeout_ms)
        except PWTimeoutError as e:
            self._record(False, page_sig=page_sig, frame_hash=frame_hash, label_key=label_key, selector=selector)
            raise TimeoutError(f"Executor.type timeout for selector: {selector}") from e
        except Exception:
            self._record(False, page_sig=page_sig, frame_hash=frame_hash, label_key=label_key, selector=selector)
            raise
        else:
            self._record(True, page_sig=page_sig, frame_hash=frame_hash, label_key=label_key, selector=selector)

    def press(
        self,
        selector: str,
        key: str,
        *,
        page_sig: Optional[str] = None,
        frame_hash: Optional[str] = None,
        label_key: Optional[str] = None,
    ) -> None:
        if not isinstance(key, str) or not key.strip():
            raise ValueError("Executor.press key must be a non-empty string")
        h = self._query_element(selector)
        try:
            h.first.wait_for(state="visible", timeout=self.action_timeout_ms)
            h.first.press(key, timeout=self.action_timeout_ms)
        except PWTimeoutError as e:
            self._record(False, page_sig=page_sig, frame_hash=frame_hash, label_key=label_key, selector=selector)
            raise TimeoutError(f"Executor.press timeout for selector: {selector}") from e
        except Exception:
            self._record(False, page_sig=page_sig, frame_hash=frame_hash, label_key=label_key, selector=selector)
            raise
        else:
            self._record(True, page_sig=page_sig, frame_hash=frame_hash, label_key=label_key, selector=selector)
