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

from typing import Optional
import time

# Fail-fast import guard (no silent fallback)
try:
    from playwright.sync_api import Page, TimeoutError as PWTimeoutError
except Exception as e:  # pragma: no cover
    raise RuntimeError(
        "Playwright is required for executor. Install with `pip install playwright` "
        "and run `python -m playwright install chromium`."
    ) from e

from her.vectordb import get_default_kv
from her.promotion_adapter import record_success, record_failure


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
            h.first.wait_for(state="visible", timeout=self.action_timeout_ms)
            h.first.click(timeout=self.action_timeout_ms, force=False)
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
