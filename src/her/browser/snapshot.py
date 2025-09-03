"""Playwright-based page snapshotter (dynamic & configurable).

Returns a normalized list of visible page elements:
{ text, tag, role, attrs, xpath, bbox }.

Key points:
- Collects ALL non-empty attributes by default (configurable allow/block lists).
- Robust visibility (display/visibility/opacity/area + viewport intersection).
- Stable absolute XPath using sibling indices.
- Timeouts, retries, and guaranteed cleanup.
- Works in and out of existing event loops (sync wrapper).
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, asdict
from threading import Thread
from typing import Any, Dict, List, Optional

from playwright.async_api import (
    async_playwright,
    Error as PlaywrightError,
    TimeoutError as PlaywrightTimeoutError,
)

logger = logging.getLogger("her.browser")


@dataclass
class SnapshotOptions:
    # Browser controls
    headless: bool = True
    default_timeout_ms: int = 15_000

    # Extraction config
    max_text_length: int = 2048      # max chars of innerText to keep
    include_offscreen: bool = False  # include elements fully outside viewport
    min_area: int = 1                # minimum visible area (w*h) to keep

    # Attribute inclusion policy:
    # If attr_include is non-empty -> include ONLY those names (plus data-* if include_data_attrs=True).
    # Else include ALL non-empty attributes EXCEPT those in attr_exclude or with prefixes in attr_exclude_prefixes.
    attr_include: Optional[List[str]] = None
    include_data_attrs: bool = True
    attr_exclude: List[str] = ("style",)
    attr_exclude_prefixes: List[str] = ("on",)  # drop on* event handlers
    useful_attrs: List[str] = ("href", "aria-label", "title", "alt", "placeholder", "value", "name")

    # Tag/role heuristics (still configurable)
    interesting_tags: List[str] = ("A", "BUTTON", "INPUT", "SELECT", "TEXTAREA", "LABEL", "H1", "H2", "H3", "H4", "H5", "H6")


class PageSnapshotter:
    def __init__(self, headless: bool = True, default_timeout_ms: int = 15_000, **kwargs: Any) -> None:
        # kwargs can override any SnapshotOptions field
        self.opts = SnapshotOptions(headless=headless, default_timeout_ms=default_timeout_ms, **kwargs)

    async def snapshot(self, url: str, timeout_ms: Optional[int] = None) -> List[Dict[str, Any]]:
        """Navigate to URL and return normalized visible elements."""
        t0 = time.time()
        timeout_ms = int(timeout_ms or self.opts.default_timeout_ms)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.opts.headless)
            context = await browser.new_context()
            try:
                page = await context.new_page()
                page.set_default_timeout(timeout_ms)

                # Simple retry on nav flake
                for attempt in range(2):
                    try:
                        await page.goto(url, wait_until="load")
                        break
                    except (PlaywrightTimeoutError, PlaywrightError):
                        if attempt == 1:
                            raise
                        await asyncio.sleep(0.25)

                # Pass options to the page; Playwright JSON-serializes the dict automatically.
                options = asdict(self.opts)
                result = await page.evaluate(
                    """(opts) => {
  const collapse = (s) => (s || '').replace(/\\s+/g, ' ').trim();

  function isElementVisible(el, includeOffscreen, minArea) {
    const style = window.getComputedStyle(el);
    if (style.display === 'none' || style.visibility === 'hidden') return false;
    const opacity = parseFloat(style.opacity);
    if (!isNaN(opacity) && opacity === 0) return false;

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

  const els = Array.from(document.querySelectorAll('*'));
  const out = [];
  const stats = { seen: els.length, kept: 0, hidden: 0, skipped: 0 };

  const cfg = {
    maxText: opts.max_text_length || 2048,
    includeOffscreen: !!opts.include_offscreen,
    minArea: parseInt(opts.min_area || 1, 10),
    attrInclude: Array.isArray(opts.attr_include) ? opts.attr_include.map(String) : null,
    includeData: !!opts.include_data_attrs,
    attrExclude: new Set((opts.attr_exclude || []).map(String)),
    attrExcludePrefixes: (opts.attr_exclude_prefixes || []).map(String),
    usefulAttrs: new Set((opts.useful_attrs || []).map(String)),
    interestingTags: new Set((opts.interesting_tags || []).map(s => String(s).toUpperCase()))
  };

  function shouldExcludeAttr(name) {
    if (cfg.attrExclude.has(name)) return true;
    for (const pref of cfg.attrExcludePrefixes) {
      if (name.startsWith(pref)) return true; // drop on*, etc.
    }
    return false;
  }

  function collectAttributes(el) {
    const result = {};
    const attrs = el.attributes;
    if (cfg.attrInclude && cfg.attrInclude.length > 0) {
      // allowlist
      for (const name of cfg.attrInclude) {
        const v = el.getAttribute(name);
        if (v != null && String(v).trim() !== '') {
          if (!cfg.includeData && name.startsWith('data-')) continue;
          result[name] = collapse(String(v));
        }
      }
    } else {
      // include all non-empty, minus excludes/prefixes
      for (let i = 0; i < attrs.length; i++) {
        const name = attrs[i].name;
        if (!cfg.includeData && name.startsWith('data-')) continue;
        if (shouldExcludeAttr(name)) continue;
        const v = attrs[i].value;
        if (v != null && String(v).trim() !== '') {
          result[name] = collapse(String(v));
        }
      }
    }
    return result;
  }

  function hasUsefulAttribute(attrs) {
    for (const k of Object.keys(attrs)) {
      if (cfg.usefulAttrs.has(k)) return true;
    }
    return false;
  }

  for (const el of els) {
    if (!isElementVisible(el, cfg.includeOffscreen, cfg.minArea)) { stats.hidden++; continue; }

    const tag = el.tagName.toUpperCase();
    const role = el.getAttribute('role');
    const attrs = collectAttributes(el);
    const textRaw = collapse(el.innerText || '');
    const text = textRaw.length > cfg.maxText ? textRaw.slice(0, cfg.maxText) : textRaw;

    const keep = (text.length > 0) || hasUsefulAttribute(attrs) || cfg.interestingTags.has(tag) || !!role;
    if (!keep) { stats.skipped++; continue; }

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
        w: Math.max(0, Math.round(rect.width)),
        h: Math.max(0, Math.round(rect.height))
      }
    });
  }

  stats.kept = out.length;
  return { items: out, stats };
}""",
                    options,
                )

                items = result.get("items", []) if isinstance(result, dict) else result
                stats = result.get("stats", {}) if isinstance(result, dict) else {}
                logger.debug(
                    "[snapshot] stats url=%s seen=%s kept=%s hidden=%s skipped=%s",
                    url, stats.get("seen"), stats.get("kept"), stats.get("hidden"), stats.get("skipped"),
                )
                return items

            except PlaywrightTimeoutError as e:
                raise TimeoutError(f"Snapshot timeout after {timeout_ms} ms for {url}") from e
            except PlaywrightError as e:
                raise RuntimeError(f"Snapshot error for {url}: {e}") from e
            finally:
                # always clean up
                try:
                    await context.close()
                except Exception:
                    pass
                try:
                    await browser.close()
                except Exception:
                    pass

        logger.info("[snapshot] captured url=%s in %d ms", url, int((time.time() - t0) * 1000))


def snapshot_sync(
    url: str,
    timeout_ms: Optional[int] = None,
    headless: Optional[bool] = None,
    **kwargs: Any,
) -> List[Dict[str, Any]]:
    """Sync wrapper around PageSnapshotter.snapshot(); accepts SnapshotOptions via kwargs."""
    snap = PageSnapshotter(
        headless=self_or_default(headless, True),
        **kwargs
    )

    async def _run() -> List[Dict[str, Any]]:
        return await snap.snapshot(url, timeout_ms=timeout_ms)

    # If we're inside a running loop, run in a separate thread with its own loop
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
        t.start()
        t.join()
        if container["error"] is not None:
            raise container["error"]
        return container["result"]  # type: ignore[return-value]

    return asyncio.run(_run())


def self_or_default(value: Optional[bool], default: bool) -> bool:
    return default if value is None else value
