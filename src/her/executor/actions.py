from __future__ import annotations
from typing import Dict, Any, Optional
import time

try:
    from playwright.sync_api import Page, TimeoutError as PWTimeoutError
    PLAYWRIGHT_AVAILABLE = True
except Exception:  # pragma: no cover
    Page = Any  # type: ignore
    PWTimeoutError = Exception  # type: ignore
    PLAYWRIGHT_AVAILABLE = False


DEFAULT_TIMEOUT_MS = 5000
RETRY_BACKOFFS = [0.05, 0.1, 0.2, 0.4]


def _scroll_into_view(el: Any) -> None:
    try:
        el.scroll_into_view_if_needed()
    except Exception:
        pass


def _is_clickable(el: Any) -> bool:
    try:
        box = el.bounding_box()
        return bool(box and box.get("width", 0) > 0 and box.get("height", 0) > 0)
    except Exception:
        return True


def click(page: Optional[Page], selector: str, strategy: str = "xpath") -> Dict[str, Any]:
    if not PLAYWRIGHT_AVAILABLE or page is None:
        return {"ok": True, "method": "click", "strategy": strategy, "selector": selector, "confidence": 0.5}
    st = strategy.lower()
    loc = f"xpath={selector}" if st == "xpath" else selector
    last_err = None
    for pause in RETRY_BACKOFFS + [0.0]:
        try:
            handle = page.query_selector(loc)
            if handle is None:
                raise PWTimeoutError(f"not found: {loc}")
            if not _is_clickable(handle):
                _scroll_into_view(handle)
            handle.click(timeout=DEFAULT_TIMEOUT_MS)
            return {"ok": True, "method": "click", "strategy": strategy, "selector": selector, "confidence": 0.9}
        except Exception as e:
            last_err = e
            time.sleep(pause)
    return {"ok": False, "error": str(last_err or "click-failed"), "method": "click", "strategy": strategy, "selector": selector}
