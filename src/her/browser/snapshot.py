"""Playwright-based page snapshotter.

Produces a normalized list of visible page elements with text, tag, role,
selected attributes, absolute XPath, and bounding box.
"""

from __future__ import annotations

import asyncio
import logging
import time
from threading import Thread
from typing import Any, Dict, List, Optional

from playwright.async_api import async_playwright, Error as PlaywrightError, TimeoutError as PlaywrightTimeoutError


logger = logging.getLogger("her.browser")


class PageSnapshotter:
    def __init__(self, headless: bool = True, default_timeout_ms: int = 15000) -> None:
        self.headless = bool(headless)
        self.default_timeout_ms = int(default_timeout_ms)

    async def snapshot(self, url: str, timeout_ms: Optional[int] = None) -> List[Dict[str, Any]]:
        """Navigate and return normalized elements.

        Args:
            url: The URL to navigate to.
            timeout_ms: Optional per-call timeout in milliseconds.
        Returns:
            List of element dictionaries with keys: text, tag, role, attrs, xpath, bbox
        Raises:
            TimeoutError: If the operation exceeds the timeout.
            RuntimeError: For navigation or capture failures.
        """

        total_timeout_ms = int(timeout_ms if timeout_ms is not None else self.default_timeout_ms)

        async def _do_snapshot() -> List[Dict[str, Any]]:
            start_time = time.time()
            logger.info("[snapshot] start url=%s headless=%s timeout_ms=%s", url, self.headless, total_timeout_ms)

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=self.headless)
                context = await browser.new_context()
                page = await context.new_page()
                # Belt-and-suspenders timeouts
                page.set_default_timeout(total_timeout_ms)

                last_error: Optional[BaseException] = None
                # Simple retry on navigation
                for attempt in range(2):
                    try:
                        await page.goto(url, wait_until="load")
                        break
                    except PlaywrightTimeoutError as e:
                        last_error = e
                        if attempt == 1:
                            raise
                        await asyncio.sleep(0.25)
                    except PlaywrightError as e:
                        last_error = e
                        if attempt == 1:
                            raise
                        await asyncio.sleep(0.25)

                # DOM extraction script
                js = """
(() => {
  const selectedAttrs = ['id','class','href','aria-label','title','alt'];
  const collapse = (s) => (s || '').replace(/\s+/g, ' ').trim();
  const maxText = 1024;

  function isElementVisible(el) {
    const style = window.getComputedStyle(el);
    if (style.display === 'none' || style.visibility === 'hidden') return false;
    const opacity = parseFloat(style.opacity);
    if (!isNaN(opacity) && opacity === 0) return false;
    if (el.hasAttribute('hidden')) return false;
    const rect = el.getBoundingClientRect();
    const w = Math.max(0, Math.round(rect.width));
    const h = Math.max(0, Math.round(rect.height));
    if (w <= 0 || h <= 0) return false;
    return true;
  }

  function hasUsefulAttr(el) {
    return !!(el.getAttribute('href') || el.getAttribute('aria-label') || el.getAttribute('title') || el.getAttribute('alt'));
  }

  function isInterestingTag(el) {
    const t = el.tagName;
    return /^(A|BUTTON|INPUT|SELECT|TEXTAREA|LABEL|H1|H2|H3|H4|H5|H6)$/.test(t);
  }

  function siblingIndex(el) {
    let i = 1; let s = el.previousElementSibling;
    while (s) { if (s.nodeName === el.nodeName) i++; s = s.previousElementSibling; }
    return i;
  }

  function absoluteXPath(el) {
    if (!el) return '';
    if (el.nodeType !== Node.ELEMENT_NODE) el = el.parentElement;
    const segments = [];
    while (el && el.nodeType === Node.ELEMENT_NODE) {
      const name = el.nodeName.toUpperCase();
      const idx = siblingIndex(el);
      segments.unshift(name + '[' + idx + ']');
      if (name === 'HTML') break;
      el = el.parentElement;
    }
    return '/' + segments.join('/');
  }

  const all = Array.from(document.querySelectorAll('*'));
  const stats = { seen: all.length, kept: 0, hidden: 0, skipped: 0 };
  const items = [];

  for (const el of all) {
    if (!isElementVisible(el)) { stats.hidden++; continue; }
    const tag = el.tagName.toUpperCase();
    const roleAttr = el.getAttribute('role');
    const textRaw = collapse(el.innerText || '');
    const attrs = {};
    for (const k of selectedAttrs) {
      const v = el.getAttribute(k);
      if (v !== null && v !== undefined && v !== '') attrs[k] = v;
    }
    const hasText = textRaw.length > 0;
    const keep = hasText || hasUsefulAttr(el) || isInterestingTag(el) || !!roleAttr;
    if (!keep) { stats.skipped++; continue; }
    const rect = el.getBoundingClientRect();
    const item = {
      text: textRaw.slice(0, maxText),
      tag: tag,
      role: roleAttr || null,
      attrs: attrs,
      xpath: absoluteXPath(el),
      bbox: { x: Math.max(0, Math.round(rect.x)), y: Math.max(0, Math.round(rect.y)), w: Math.max(0, Math.round(rect.width)), h: Math.max(0, Math.round(rect.height)) }
    };
    items.push(item);
  }

  stats.kept = items.length;
  return { items, stats };
})()
                """

                result = await page.evaluate(js)
                items = result.get("items", []) if isinstance(result, dict) else result
                stats = result.get("stats", {}) if isinstance(result, dict) else {}

                duration = time.time() - start_time
                logger.debug(
                    "[snapshot] filter stats url=%s seen=%s kept=%s hidden=%s skipped=%s",
                    url,
                    stats.get("seen"),
                    stats.get("kept"),
                    stats.get("hidden"),
                    stats.get("skipped"),
                )
                logger.info("[snapshot] finish url=%s count=%s duration_ms=%s", url, len(items), int(duration * 1000))

                # Cleanup
                await context.close()
                await browser.close()
                return items

        try:
            return await asyncio.wait_for(_do_snapshot(), timeout=total_timeout_ms / 1000.0)
        except asyncio.TimeoutError as e:
            raise TimeoutError(f"Snapshot timed out for URL {url!r} after {total_timeout_ms} ms") from e
        except PlaywrightTimeoutError as e:
            # Surface as timeout to the caller for consistency
            raise TimeoutError(f"Navigation timed out for URL {url!r} after {total_timeout_ms} ms") from e
        except PlaywrightError as e:
            raise RuntimeError(f"Navigation failed for URL {url!r}: {e}") from e


def snapshot_sync(url: str, timeout_ms: Optional[int] = None, headless: bool = True) -> List[Dict[str, Any]]:
    """Runs PageSnapshotter.snapshot() in its own event loop, returns list[dict]."""

    snapshotter = PageSnapshotter(headless=headless, default_timeout_ms=int(timeout_ms or 15000))

    async def _run() -> List[Dict[str, Any]]:
        # Per-call override ensures we do not double-apply timeout
        return await snapshotter.snapshot(url, timeout_ms=timeout_ms)

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None  # no running loop

    if loop and loop.is_running():
        # Run in a dedicated thread with its own event loop
        container: Dict[str, Any] = {"result": None, "error": None}

        def _thread_target() -> None:
            try:
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                container["result"] = new_loop.run_until_complete(_run())
            except BaseException as e:  # noqa: BLE001
                container["error"] = e
            finally:
                try:
                    new_loop.run_until_complete(asyncio.sleep(0))
                except Exception:
                    pass
                new_loop.close()

        t = Thread(target=_thread_target, daemon=True)
        t.start()
        t.join()
        if container["error"] is not None:
            raise container["error"]  # type: ignore[misc]
        return container["result"]  # type: ignore[return-value]
    else:
        # Simple path when no loop is running in this thread
        return asyncio.run(_run())

