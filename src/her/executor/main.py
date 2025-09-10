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

    # ---------------- internal helpers ----------------
    def _query_element(self, xpath: str):
        if not xpath or not isinstance(xpath, str):
            raise ValueError("Executor: invalid XPath selector")
        handle = self.page.locator(f"xpath={xpath}")
        return handle

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
            # First try to scroll element into view
            try:
                h.first.scroll_into_view_if_needed(timeout=2000)
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
            
            # Now try the actual click with retries
            clicked = False
            for attempt in range(3):
                try:
                    if attempt == 0:
                        # First attempt: wait for visible and click normally
                        h.first.wait_for(state="visible", timeout=self.action_timeout_ms // 2)
                        h.first.click(timeout=self.action_timeout_ms // 2, force=False)
                    elif attempt == 1:
                        # Second attempt: try with JavaScript click
                        self.page.evaluate("(el) => el.click()", h.first.element_handle())
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
