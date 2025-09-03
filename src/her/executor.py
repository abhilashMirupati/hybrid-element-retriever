from __future__ import annotations
from typing import Optional
from playwright.sync_api import sync_playwright, Page, TimeoutError as PlaywrightTimeout

class PageLoadError(RuntimeError): pass
class ElementNotFoundError(RuntimeError): pass
class ElementNotInteractableError(RuntimeError): pass

def _get_frame_by_url(page: Page, frame_url_substr: str):
    for f in page.frames:
        if frame_url_substr and frame_url_substr in (f.url or ""):
            return f
    return page.main_frame

def _ensure_visible(el):
    try:
        el.scroll_into_view_if_needed(timeout=5000)
    except Exception:
        pass

def run_action(url: str, action: str, selector: str, value: Optional[str] = None, frame_url_hint: Optional[str] = None, timeout_ms: int = 15000):
    """
    Minimal executor: opens page, switches to frame if needed, performs action.
    selector is XPath (recommended) returned by pipeline.
    """
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            page.goto(url, timeout=timeout_ms, wait_until="networkidle")
        except PlaywrightTimeout as e:
            browser.close()
            raise PageLoadError(str(e))

        try:
            frame = _get_frame_by_url(page, frame_url_hint or "")
            el = frame.locator(f"xpath={selector}")
            _ensure_visible(el)
            if action == "click":
                el.click(timeout=timeout_ms)
            elif action == "type":
                if value is None:
                    raise ElementNotInteractableError("No value provided for type action.")
                el.fill(value, timeout=timeout_ms)
            elif action == "press":
                key = value or "Enter"
                frame.keyboard.press(key)
            elif action == "list":
                # no-op in executor; listing handled by pipeline
                pass
            else:
                raise ElementNotInteractableError(f"Unsupported action: {action}")
        except PlaywrightTimeout:
            browser.close()
            raise ElementNotFoundError(f"Selector not found or not interactable: {selector}")
        finally:
            browser.close()
