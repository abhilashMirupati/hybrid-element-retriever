from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Any, Optional, Dict, List

import logging

logger = logging.getLogger(__name__)

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except Exception:  # pragma: no cover - imported in tests via patch
    sync_playwright = None  # type: ignore
    PLAYWRIGHT_AVAILABLE = False


class ActionError(Exception):
    """Exception raised when an action fails to execute."""


@dataclass
class ActionResult:
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
    """Thin executor around Playwright used by CLI API and tests."""

    def __init__(self, headless: bool = True, timeout_ms: int = 30000, **kwargs) -> None:
        self.headless = headless
        self.timeout_ms = timeout_ms
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

        if PLAYWRIGHT_AVAILABLE:
            try:
                _pw = sync_playwright()
                self.playwright = _pw.start()
                self.browser = self.playwright.chromium.launch(headless=self.headless)
                self.context = self.browser.new_context()
                self.page = self.context.new_page()
            except Exception as e:  # pragma: no cover - environment dependent
                logger.debug(f"Playwright init failed: {e}")
                self.playwright = None
                self.browser = None
                self.context = None
                self.page = None

    # ----------------------- High-level helpers -----------------------
    def navigate(self, url: str) -> bool:
        if not self.page:
            return False
        try:
            self.page.goto(url, wait_until="domcontentloaded")
            return True
        except Exception as e:  # pragma: no cover
            logger.debug(f"navigate failed: {e}")
            return False

    def execute(self, action: str, locator: str, value: Optional[str] = None) -> ActionResult:
        if not self.page:
            return ActionResult(success=False, action=action, locator=locator, error="Page not initialized")

        start = time.time()
        try:
            if action in {"type", "fill"}:
                res = self.fill(locator, value or "")
            elif action == "check":
                res = self.check(locator)
            else:
                res = self.click(locator)
            res.duration_ms = int((time.time() - start) * 1000)
            return res
        except Exception as e:
            return ActionResult(success=False, action=action, locator=locator, error=str(e), duration_ms=int((time.time() - start) * 1000))

    def wait_for_condition(self, condition: str, timeout: Optional[int] = None) -> bool:
        to = timeout or self.timeout_ms
        if not self.page:
            return False
        try:
            if condition == "load":
                self.page.wait_for_load_state("load", timeout=to)
                return True
            if condition == "networkidle":
                self.page.wait_for_load_state("networkidle", timeout=to)
                return True
            # assume selector
            self.page.wait_for_selector(condition, timeout=to)
            return True
        except Exception as e:  # pragma: no cover
            logger.debug(f"wait_for_condition failed: {e}")
            return False

    # ----------------------- Primitive actions -----------------------
    def click(self, locator: str) -> ActionResult:
        if not self.page:
            return ActionResult(success=False, action="click", locator=locator, error="Page not initialized")
        try:
            el = self._string_to_locator(locator)
            _scroll_into_view(el)
            _overlay_guard(self.page)
            _occlusion_guard(el)
            el.click()
            _verify_post_action(el, "click")
            return ActionResult(success=True, action="click", locator=locator, verification={"method": "standard"})
        except Exception as e:
            return ActionResult(success=False, action="click", locator=locator, error=str(e))

    def fill(self, locator: str, text: str) -> ActionResult:
        if not self.page:
            return ActionResult(success=False, action="fill", locator=locator, error="Page not initialized")
        try:
            el = self._string_to_locator(locator)
            _scroll_into_view(el)
            _overlay_guard(self.page)
            _occlusion_guard(el)
            el.fill(text)
            _verify_post_action(el, "fill", text)
            return ActionResult(success=True, action="fill", locator=locator, verification={"method": "standard"})
        except Exception as e:
            return ActionResult(success=False, action="fill", locator=locator, error=str(e))

    def check(self, locator: str) -> ActionResult:
        if not self.page:
            return ActionResult(success=False, action="check", locator=locator, error="Page not initialized")
        try:
            el = self._string_to_locator(locator)
            _scroll_into_view(el)
            _overlay_guard(self.page)
            _occlusion_guard(el)
            el.check()
            _verify_post_action(el, "check")
            return ActionResult(success=True, action="check", locator=locator, verification={"method": "standard"})
        except Exception as e:
            return ActionResult(success=False, action="check", locator=locator, error=str(e))

    def close(self) -> None:
        try:
            if self.page:
                self.page.close()
        except Exception:
            pass
        try:
            if self.context:
                self.context.close()
        except Exception:
            pass
        try:
            if self.browser:
                self.browser.close()
        except Exception:
            pass
        try:
            if self.playwright:
                self.playwright.stop()
        except Exception:
            pass

    # ----------------------- Utilities -----------------------
    def _string_to_locator(self, sel: str):  # type: ignore[override]
        # For simplicity, use page.locator for css/xpath/text/role patterns
        if sel.startswith("role=") and hasattr(self.page, "get_by_role"):
            role, name = _parse_role_sel(sel)
            if name:
                return self.page.get_by_role(role, name=name)
            return self.page.get_by_role(role)
        if sel.startswith("text=") and hasattr(self.page, "get_by_text"):
            t = sel[len("text=") :]
            if (t.startswith('"') and t.endswith('"')) or (t.startswith("'") and t.endswith("'")):
                t = t[1:-1]
            return self.page.get_by_text(t, exact=True)
        if sel.startswith("xpath="):
            return self.page.locator(sel)
        if sel.startswith("//"):
            return self.page.locator(f"xpath={sel}")
        return self.page.locator(sel)


def _scroll_into_view(el: Any) -> None:
    try:
        h = el.element_handle() if hasattr(el, 'element_handle') else el
        if h:
            h.scroll_into_view_if_needed()
    except Exception as e:
        raise ActionError(f'scroll failed: {e}') from e


def _overlay_guard(page: Any) -> None:
    try:
        for sel in ['text=Accept', 'text=Close', 'text=Dismiss', 'role=dialog >> text=×']:
            try:
                el = page.query_selector(sel)
                if el and el.is_visible():
                    el.click(timeout=1000)
            except Exception:
                continue
    except Exception:
        return


def _occlusion_guard(el: Any) -> None:
    try:
        h = el.element_handle() if hasattr(el, 'element_handle') else el
        if not h:
            return
        occ = h.evaluate('(e)=>{const r=e.getBoundingClientRect();const cx=Math.floor(r.left+r.width/2);const cy=Math.floor(r.top+r.height/2);const top=document.elementFromPoint(cx,cy);return !(top===e||top.contains(e));}')
        if occ:
            raise ActionError('occluded')
    except Exception as e:
        raise ActionError(f'occlusion: {e}') from e


def _verify_post_action(el: Any, action: str, expected: Optional[str] = None) -> None:
    try:
        if action == 'fill' and expected is not None:
            if el.input_value() != expected:
                raise ActionError('fill verify failed')
        elif action == 'click':
            if not el.is_enabled():
                raise ActionError('disabled after click')
        elif action == 'check':
            if not el.is_checked():
                raise ActionError('check failed')
    except Exception as e:
        raise ActionError(f'post verify: {e}') from e


def wait_for_idle(page: Any, timeout: float = 5.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if page.evaluate('() => document.readyState') == 'complete':
                return
        except Exception:
            # Page might be navigating or closed, continue waiting
            pass
        time.sleep(0.1)


def _parse_role_sel(sel: str) -> tuple[str, Optional[str]]:
    s = sel[len("role=") :]
    role = s
    name = None
    if "[" in s and "]" in s:
        role, rest = s.split("[", 1)
        rest = rest.rstrip("]")
        if rest.startswith("name="):
            v = rest[len("name=") :]
            if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                v = v[1:-1]
            name = v
    return role, name


__all__ = [
    'ActionError',
    'ActionExecutor',
    'ActionResult',
    'wait_for_idle',
]
