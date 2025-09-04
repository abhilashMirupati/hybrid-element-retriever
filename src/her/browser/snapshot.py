"""
Playwright-based page snapshotter (production-hardened).

Features:
- Real Chromium (headless by default)
- Visibility filtering (display/visibility/opacity/area + viewport intersection)
- Stable absolute XPath (with sibling indices)
- Iframe traversal (configurable depth)
- Shadow DOM traversal (pierce shadow roots)
- Auto-scroll to trigger lazy/infinite content (time/step bounded)
- Wait-until='networkidle' (configurable)
- Optional banner/overlay dismissal (CSS selectors)
- Locale/UA/viewport configuration
- Duplicate suppression (text/tag/role/href/xpath)
- Optional full-page screenshot capture
- Timeouts, retries, guaranteed cleanup
- Sync wrapper that works in/out of running event loops

Returns a tuple (elements, dom_hash) where elements is list[dict] with keys:
text, tag, role, attrs, xpath, bbox, visible, frame_url
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, asdict, field
from threading import Thread
from typing import Any, Dict, List, Optional, Tuple, Set

try:
    from playwright.async_api import (
        async_playwright,
        Error as PlaywrightError,
        TimeoutError as PlaywrightTimeoutError,
    )
    _PLAYWRIGHT_AVAILABLE = True
except Exception:  # pragma: no cover - allow module import without Playwright
    _PLAYWRIGHT_AVAILABLE = False
    class PlaywrightError(Exception):
        pass
    class PlaywrightTimeoutError(Exception):
        pass
from .. import hashing

logger = logging.getLogger("her.browser")


@dataclass
class SnapshotOptions:
    # Browser/session
    headless: bool = True
    default_timeout_ms: int = 15_000
    wait_until: str = "networkidle"     # "load" | "domcontentloaded" | "networkidle"
    viewport_width: int = 1366
    viewport_height: int = 768
    locale: Optional[str] = None
    user_agent: Optional[str] = None

    # Extraction
    max_text_length: int = 2048
    include_offscreen: bool = False
    min_area: int = 1

    # DOM reach
    include_iframes: bool = True
    max_iframe_depth: int = 2
    include_shadow_dom: bool = True

    # Lazy-content scroll
    auto_scroll: bool = True
    scroll_steps: int = 8
    scroll_pause_ms: int = 400

    # Banner / overlay dismissal (clicked before snapshot; safe best-effort)
    dismiss_selectors: List[str] = field(default_factory=lambda: [
        'button[aria-label="Close"]',
        'button[aria-label="Dismiss"]',
        'button:has-text("Accept")',
        'button:has-text("Agree")',
        '#onetrust-accept-btn-handler',
        '.cc-allow',
    ])

    # Attributes policy
    attr_include: Optional[List[str]] = None
    include_data_attrs: bool = True
    attr_exclude: List[str] = field(default_factory=lambda: ["style"])
    attr_exclude_prefixes: List[str] = field(default_factory=lambda: ["on"])  # onClick, etc.
    useful_attrs: List[str] = field(default_factory=lambda: ["href", "aria-label", "title", "alt", "placeholder", "value", "name"])
    interesting_tags: List[str] = field(default_factory=lambda: ["A", "BUTTON", "INPUT", "SELECT", "TEXTAREA", "LABEL", "H1", "H2", "H3", "H4", "H5", "H6"])

    # Output
    screenshot_path: Optional[str] = None   # if provided, save full-page PNG to this path


class PageSnapshotter:
    def __init__(self, headless: bool = True, default_timeout_ms: int = 15_000, **kwargs: Any) -> None:
        self.opts = SnapshotOptions(headless=headless, default_timeout_ms=default_timeout_ms, **kwargs)

    async def _dismiss_banners(self, page) -> None:
        if not self.opts.dismiss_selectors:
            return
        try:
            for sel in self.opts.dismiss_selectors:
                try:
                    el = await page.query_selector(sel)
                    if el:
                        await el.click(timeout=500)
                except Exception:
                    continue
        except Exception:
            pass

    async def _auto_scroll(self, page) -> None:
        if not self.opts.auto_scroll or self.opts.scroll_steps <= 0:
            return
        try:
            for _ in range(self.opts.scroll_steps):
                await page.evaluate("""() => {
                  return new Promise((resolve) => {
                    const y = Math.min(document.body.scrollHeight, window.scrollY + window.innerHeight);
                    window.scrollTo({ top: y, behavior: 'instant' });
                    setTimeout(resolve, 10);
                  });
                }""")
                await page.wait_for_timeout(self.opts.scroll_pause_ms)
        except Exception:
            pass

    async def _collect_from_frame(self, frame, options_dict: Dict[str, Any], depth: int, max_depth: int) -> List[Dict[str, Any]]:
        # Evaluate the DOM in this frame (includes shadow DOM traversal when enabled).
        js = """(opts) => {
  const collapse = (s) => (s || '').replace(/\\s+/g, ' ').trim();

  function isElementVisible(el, includeOffscreen, minArea) {
    const style = window.getComputedStyle(el);
    if (style.display === 'none' || style.visibility === 'hidden') return false;
    const op = parseFloat(style.opacity);
    if (!isNaN(op) && op === 0) return false;

    const rect = el.getBoundingClientRect();
    const w = Math.max(0, Math.round(rect.width));
    const h = Math.max(0, Math.round(rect.height));
    if ((w * h) < Math.max(0, minArea || 0)) return false;

    if (!includeOffscreen) {
      const vw = Math.max(document.documentElement.clientWidth, window.innerWidth || 0);
      const vh = Math.max(document.documentElement.clientHeight, window.innerHeight || 0);
      const left = rect.left, right = rect.right, top = rect.top, bottom = rect.bottom;
      const horizontallyVisible = right > 0 && left < vw;
      const verticallyVisible   = bottom > 0 && top < vh;
      if (!(horizontallyVisible && verticallyVisible)) return false;
    }
    return true;
  }

  function siblingIndex(el) {
    let i = 1; let s = el.previousElementSibling;
    while (s) { if (s.nodeName === el.nodeName) i++; s = s.previousElementSibling; }
    return i;
  }

  function absoluteXPath(el) {
    if (!el || el.nodeType !== 1) return '';
    const parts = [];
    while (el && el.nodeType === 1 && el !== document) {
      const ix = siblingIndex(el);
      parts.unshift(el.tagName.toUpperCase() + '[' + ix + ']');
      el = el.parentElement;
    }
    return '/' + parts.join('/');
  }

  function shouldExcludeAttr(name, cfg) {
    if (cfg.attrExclude.has(name)) return true;
    for (const pref of cfg.attrExcludePrefixes) {
      if (name.startsWith(pref)) return true;
    }
    return false;
  }

  function collectAttributes(el, cfg) {
    const result = {};
    const attrs = el.attributes;
    if (cfg.attrInclude && cfg.attrInclude.length > 0) {
      for (const name of cfg.attrInclude) {
        const v = el.getAttribute(name);
        if (v != null && String(v).trim() !== '') {
          if (!cfg.includeData && name.startsWith('data-')) continue;
          result[name] = collapse(String(v));
        }
      }
    } else {
      for (let i = 0; i < attrs.length; i++) {
        const name = attrs[i].name;
        if (!cfg.includeData && name.startsWith('data-')) continue;
        if (shouldExcludeAttr(name, cfg)) continue;
        const v = attrs[i].value;
        if (v != null && String(v).trim() !== '') {
          result[name] = collapse(String(v));
        }
      }
    }
    return result;
  }

  function hasUsefulAttribute(attrs, cfg) {
    for (const k of Object.keys(attrs)) {
      if (cfg.usefulAttrs.has(k)) return true;
    }
    return false;
  }

  // Traverse DOM, optionally piercing shadow roots.
  const cfg = {
    maxText: opts.max_text_length || 2048,
    includeOffscreen: !!opts.include_offscreen,
    minArea: parseInt(opts.min_area || 1, 10),
    attrInclude: Array.isArray(opts.attr_include) ? opts.attr_include.map(String) : null,
    includeData: !!opts.include_data_attrs,
    attrExclude: new Set((opts.attr_exclude || []).map(String)),
    attrExcludePrefixes: (opts.attr_exclude_prefixes || []).map(String),
    usefulAttrs: new Set((opts.useful_attrs || []).map(String)),
    interestingTags: new Set((opts.interesting_tags || []).map(s => String(s).toUpperCase())),
    includeShadow: !!opts.include_shadow_dom,
  };

  const out = [];
  const visited = new Set();

  function pushElement(el) {
    if (!isElementVisible(el, cfg.includeOffscreen, cfg.minArea)) return;
    const key = el;  // identity in this realm
    if (visited.has(key)) return;
    visited.add(key);

    const tag = el.tagName.toUpperCase();
    const role = el.getAttribute('role');
    const attrs = collectAttributes(el, cfg);
    const textRaw = (el.innerText || '').replace(/\\s+/g, ' ').trim();
    const text = textRaw.length > cfg.maxText ? textRaw.slice(0, cfg.maxText) : textRaw;

    const keep = (text.length > 0) || hasUsefulAttribute(attrs, cfg) || cfg.interestingTags.has(tag) || !!role;
    if (!keep) return;

    const rect = el.getBoundingClientRect();
    out.push({
      text,
      tag,
      role: role || null,
      attrs,
      xpath: absoluteXPath(el),
      bbox: {
        x: Math.max(0, Math.round(rect.x)),
        y: Math.max(0, Math.round(rect.y)),
        // Provide both width/height and w/h for downstream compatibility
        width: Math.max(0, Math.round(rect.width)),
        height: Math.max(0, Math.round(rect.height)),
        w: Math.max(0, Math.round(rect.width)),
        h: Math.max(0, Math.round(rect.height))
      },
      visible: true
    });
  }

  function walk(node) {
    if (!(node instanceof Element)) return;
    pushElement(node);

    // Regular children
    for (const child of node.children) {
      walk(child);
    }

    // Shadow root
    if (cfg.includeShadow && node.shadowRoot) {
      for (const sChild of node.shadowRoot.querySelectorAll('*')) {
        pushElement(sChild);
      }
    }
  }

  walk(document.documentElement);
  return out;
}"""
        items = await frame.evaluate(js, options_dict)
        # Tag each item with the frame URL (useful for iframes)
        try:
            f_url = frame.url
        except Exception:
            f_url = ""
        for it in items:
            it["frame_url"] = f_url
        # Compute a stable frame hash and attach it to each element's meta
        try:
            fh = hashing.frame_hash(f_url, items)
            for it in items:
                (it.setdefault("meta", {}))["frame_hash"] = fh
        except Exception:
            pass
        results = list(items)

        # Recurse into child frames (iframes), bounded by depth
        if self.opts.include_iframes and depth < max_depth:
            for child in frame.child_frames:
                try:
                    results += await self._collect_from_frame(child, options_dict, depth + 1, max_depth)
                except Exception:
                    continue
        return results

    def _dedupe(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen: Set[Tuple] = set()
        out: List[Dict[str, Any]] = []
        for it in items:
            key = (
                it.get("text", "")[:256],
                it.get("tag"),
                it.get("role"),
                (it.get("attrs") or {}).get("href", ""),
                it.get("xpath"),
                it.get("frame_url", ""),
            )
            if key in seen:
                continue
            seen.add(key)
            out.append(it)
        return out

    async def snapshot(self, url: str, timeout_ms: Optional[int] = None) -> Tuple[List[Dict[str, Any]], str]:
        t0 = time.time()
        timeout_ms = int(timeout_ms or self.opts.default_timeout_ms)

        if not _PLAYWRIGHT_AVAILABLE:
            # In environments without Playwright, return empty but well-typed values
            return [], ""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.opts.headless)
            context = await p.chromium.launch_persistent_context(
                user_data_dir="",  # ephemeral
                headless=self.opts.headless,
                locale=self.opts.locale or "en-US",
                user_agent=self.opts.user_agent or None,
                viewport={"width": self.opts.viewport_width, "height": self.opts.viewport_height},
            )
            page = await context.new_page()
            try:
                page.set_default_timeout(timeout_ms)

                # Navigation with retry
                for attempt in range(2):
                    try:
                        await page.goto(url, wait_until=self.opts.wait_until)
                        break
                    except (PlaywrightTimeoutError, PlaywrightError):
                        if attempt == 1:
                            raise
                        await asyncio.sleep(0.25)

                # Optional banner dismissal & lazy loading scroll
                await self._dismiss_banners(page)
                await self._auto_scroll(page)

                # Optional screenshot
                if self.opts.screenshot_path:
                    try:
                        await page.screenshot(path=self.opts.screenshot_path, full_page=True)
                    except Exception:
                        pass

                # Collect from main frame and child frames
                options = asdict(self.opts)
                items = await self._collect_from_frame(page.main_frame, options, depth=0, max_depth=self.opts.max_iframe_depth)

                # De-duplicate
                items = self._dedupe(items)

                # Page-level DOM hash from per-frame sketches
                try:
                    frames_map: Dict[str, List[Dict[str, Any]]] = {}
                    for it in items:
                        furl = it.get("frame_url") or ""
                        frames_map.setdefault(furl, []).append(it)
                    frames = [{"frame_url": k, "elements": v} for k, v in frames_map.items()]
                    dom_hash = hashing.dom_hash(frames)
                except Exception:
                    dom_hash = ""

                logger.info("[snapshot] url=%s frames=%d items=%d dur_ms=%d",
                            url, len(page.frames), len(items), int((time.time() - t0) * 1000))
                return items, dom_hash

            except PlaywrightTimeoutError as e:
                raise TimeoutError(f"Snapshot timeout after {timeout_ms} ms for {url}") from e
            except PlaywrightError as e:
                raise RuntimeError(f"Snapshot error for {url}: {e}") from e
            finally:
                try:
                    await page.close()
                except Exception:
                    pass
                try:
                    await context.close()
                except Exception:
                    pass
                try:
                    await browser.close()
                except Exception:
                    pass


def snapshot_sync(
    url: str,
    timeout_ms: Optional[int] = None,
    headless: Optional[bool] = None,
    **kwargs: Any,
) -> Tuple[List[Dict[str, Any]], str]:
    """Sync wrapper for PageSnapshotter.snapshot(); accepts SnapshotOptions fields as kwargs."""
    opts = dict(kwargs)
    if headless is not None:
        opts["headless"] = headless
    snap = PageSnapshotter(**opts)

    async def _run():
        return await snap.snapshot(url, timeout_ms=timeout_ms)

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        container: Dict[str, Any] = {"result": None, "error": None}

        def _target() -> None:
            new_loop = asyncio.new_event_loop()
            try:
                asyncio.set_event_loop(new_loop)
                container["result"] = new_loop.run_until_complete(_run())
            except Exception as e:
                container["error"] = e
            finally:
                try:
                    new_loop.stop()
                except Exception:
                    pass
                new_loop.close()

        t = Thread(target=_target, daemon=True)
        t.start(); t.join()
        if container["error"] is not None:
            raise container["error"]
        return container["result"]  # type: ignore[return-value]

    return asyncio.run(_run())


if __name__ == "__main__":
    # Simple probe: build two fake frames with a couple of elements,
    # print per-frame hashes and verify dom_hash stability across ordering.
    import json as _json

    def _el(tag: str, text: str, xpath: str) -> Dict[str, Any]:
        return {
            "tag": tag.upper(),
            "text": text,
            "attrs": {"id": "", "class": "", "title": "", "placeholder": "", "href": "", "value": "", "name": "", "aria-label": ""},
            "xpath": xpath,
            "bbox": {"x": 0, "y": 0, "width": 10, "height": 10, "w": 10, "h": 10},
            "visible": True,
        }

    frame_a = {"frame_url": "https://example.com/a", "elements": [_el("button", "OK", "/HTML[1]/BODY[1]/BUTTON[1]")]} 
    frame_b = {"frame_url": "https://example.com/b", "elements": [_el("a", "Home", "/HTML[1]/BODY[1]/A[1]"), _el("input", "", "/HTML[1]/BODY[1]/INPUT[1]")]}

    for fr in [frame_a, frame_b]:
        fh = hashing.frame_hash(fr["frame_url"], fr["elements"])  # type: ignore[arg-type]
        print(f"frame_url={fr['frame_url']} frame_hash={fh}")

    dom1 = hashing.dom_hash([frame_a, frame_b])
    dom2 = hashing.dom_hash([frame_b, frame_a])
    print(f"dom_hash1={dom1}")
    print(f"dom_hash2={dom2}")
    assert dom1 == dom2, "dom_hash should be stable under frame ordering"
    print("dom_hash stability check passed")
