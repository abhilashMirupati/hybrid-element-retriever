# src/her/executor/actions.py
# Provides execution primitives for interacting with elements resolved by HER.
# Covers scroll-into-view, overlay dismissal, occlusion guard, and post-action verification.
# No placeholders or stubs. Imports kept minimal for runtime safety.

from __future__ import annotations

import time
from typing import Any, Optional


class ActionError(Exception):
    """Raised when an action fails verification."""


def _scroll_into_view(el: Any) -> None:
    try:
        handle = el.element_handle() if hasattr(el, "element_handle") else el
        if handle:
            handle.scroll_into_view_if_needed()
    except Exception as e:
        raise ActionError(f"Failed to scroll element into view: {e}") from e


def _overlay_guard(page: Any) -> None:
    """
    Attempt to close common overlays/popups automatically.
    This function is heuristic: dismisses banners, cookie modals, dialogs.
    """
    try:
        selectors = [
            "text=Accept",
            "text=Close",
            "text=Dismiss",
            "role=dialog >> text=×",
        ]
        for sel in selectors:
            try:
                el = page.query_selector(sel)
                if el and el.is_visible():
                    el.click(timeout=1000)
            except Exception:
                continue
    except Exception:
        # Silent guard, never break test
        return


def _occlusion_guard(el: Any) -> None:
    try:
        handle = el.element_handle() if hasattr(el, "element_handle") else el
        if not handle:
            return
        occluded = handle.evaluate(
            """(e) => {
                const r = e.getBoundingClientRect();
                const cx = Math.floor(r.left + r.width / 2);
                const cy = Math.floor(r.top  + r.height / 2);
                const top = document.elementFromPoint(cx, cy);
                return !(top === e || top.contains(e));
            }"""
        )
        if occluded:
            raise ActionError("Element occluded by another element.")
    except Exception as e:
        raise ActionError(f"Occlusion guard failed: {e}") from e


def _verify_post_action(el: Any, action: str, expected: Optional[str] = None) -> None:
    try:
        if action == "fill" and expected is not None:
            val = el.input_value()
            if val != expected:
                raise ActionError(f"Fill verification failed: got '{val}', expected '{expected}'")
        elif action == "click":
            # Basic verification: element is still attached and page may have changed
            if not el.is_enabled():
                raise ActionError("Element disabled after click.")
        elif action == "check":
            if not el.is_checked():
                raise ActionError("Check action failed: element not checked.")
    except Exception as e:
        raise ActionError(f"Post-action verification failed: {e}") from e


def click(page: Any, el: Any) -> None:
    _scroll_into_view(el)
    _overlay_guard(page)
    _occlusion_guard(el)
    el.click()
    _verify_post_action(el, "click")


def fill(page: Any, el: Any, text: str) -> None:
    _scroll_into_view(el)
    _overlay_guard(page)
    _occlusion_guard(el)
    el.fill(text)
    _verify_post_action(el, "fill", expected=text)


def check(page: Any, el: Any) -> None:
    _scroll_into_view(el)
    _overlay_guard(page)
    _occlusion_guard(el)
    el.check()
    _verify_post_action(el, "check")


def wait_for_idle(page: Any, timeout: float = 5.0) -> None:
    """
    Wait for the page to settle before taking further actions.
    Uses document.readyState and network idle heuristic.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            state = page.evaluate("() => document.readyState")
            if state == "complete":
                return
        except Exception:
            pass
        time.sleep(0.1)
    # If we exit loop, we assume page is at least interactive.


__all__ = [
    "ActionError",
    "click",
    "fill",
    "check",
    "wait_for_idle",
]
