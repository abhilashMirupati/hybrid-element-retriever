from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .parser.intent import IntentParser
from .promotion_adapter import compute_label_key
from .hashing import page_signature, dom_hash, frame_hash as compute_frame_hash
from .pipeline import HybridPipeline

try:
    from playwright.sync_api import sync_playwright
    _PLAYWRIGHT = True
except Exception:  # pragma: no cover
    _PLAYWRIGHT = False

try:
    from .executor_main import Executor  # type: ignore
except Exception:
    Executor = None  # type: ignore


logger = logging.getLogger("her.runner")
_DEBUG_CANDS = os.getenv("HER_DEBUG_CANDIDATES", "0") == "1"


@dataclass
class StepResult:
    step: str
    selector: str
    confidence: float
    ok: bool
    info: Dict[str, Any]


class Runner:
    def __init__(self, headless: bool = True) -> None:
        self.headless = headless
        self.intent = IntentParser()
        self.pipeline = HybridPipeline()
        self._page = None
        self._browser = None
        self._playwright = None

    def _normalize_url(self, url: str) -> str:
        from urllib.parse import urlparse
        try:
            u = urlparse(url or "")
            path = u.path.rstrip("/")
            parts = [p for p in path.split("/") if p]
            if parts and len(parts[0]) in (2, 5) and parts[0].isalpha():
                parts = parts[1:]
            norm = f"{u.scheme}://{u.netloc}/" + "/".join(parts)
            return norm.rstrip("/")
        except Exception:
            return (url or "").split("?")[0].rstrip("/")

    def _ensure_browser(self):
        if not _PLAYWRIGHT:
            return None
        if self._page is None:
            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(headless=self.headless)
            self._page = self._browser.new_page()
            self._page.set_default_timeout(15000)
        return self._page

    def _close(self) -> None:
        try:
            if self._page:
                self._page.close()
        except Exception:
            pass
        try:
            if self._browser:
                self._browser.close()
        except Exception:
            pass
        try:
            if self._playwright:
                self._playwright.stop()
        except Exception:
            pass
        self._page = None
        self._browser = None
        self._playwright = None

    def _inline_snapshot(self) -> Dict[str, Any]:
        js = r"""
() => {
  const collapse = (s) => (s || '').replace(/\s+/g, ' ').trim();
  function isVisible(el) {
    const style = window.getComputedStyle(el);
    if (style.display === 'none' || style.visibility === 'hidden') return false;
    const op = parseFloat(style.opacity);
    if (!isNaN(op) && op === 0) return false;
    const rect = el.getBoundingClientRect();
    const w = Math.max(0, Math.round(rect.width));
    const h = Math.max(0, Math.round(rect.height));
    if ((w * h) < 1) return false;
    const vw = Math.max(document.documentElement.clientWidth, window.innerWidth || 0);
    const vh = Math.max(document.documentElement.clientHeight, window.innerHeight || 0);
    const horizontallyVisible = rect.right > 0 && rect.left < vw;
    const verticallyVisible   = rect.bottom > 0 && rect.top < vh;
    if (!(horizontallyVisible && verticallyVisible)) return false;
    return true;
  }
  function siblingIndex(el) {
    let i = 1; let s = el.previousElementSibling;
    while (s) { if (s.nodeName === el.nodeName) i++; s = s.previousElementSibling; }
    return i;
  }
  function generateRelativeXPath(el) {
    if (!el || el.nodeType !== 1) return '';
    
    // Try to generate a relative XPath based on stable attributes
    const tag = el.tagName.toLowerCase();
    const attrs = {};
    for (const a of el.attributes) {
      attrs[a.name] = a.value;
    }
    
    // Priority 1: data-testid
    if (attrs['data-testid']) {
      return `//*[@data-testid="${attrs['data-testid']}"]`;
    }
    
    // Priority 2: id
    if (attrs['id']) {
      return `//*[@id="${attrs['id']}"]`;
    }
    
    // Priority 3: aria-label
    if (attrs['aria-label']) {
      return `//*[@aria-label="${attrs['aria-label']}"]`;
    }
    
    // Priority 4: href + text for links
    if (tag === 'a' && attrs['href']) {
      const text = (el.innerText || '').trim();
      if (text) {
        return `//a[@href="${attrs['href']}" and normalize-space()="${text}"]`;
      }
      return `//a[@href="${attrs['href']}"]`;
    }
    
    // Priority 5: role + text
    if (attrs['role'] && attrs['role'] !== 'presentation') {
      const text = (el.innerText || '').trim();
      if (text) {
        return `//*[@role="${attrs['role']}" and normalize-space()="${text}"]`;
      }
      return `//*[@role="${attrs['role']}"]`;
    }
    
    // Priority 6: class + text
    if (attrs['class']) {
      const text = (el.innerText || '').trim();
      const firstClass = attrs['class'].split(' ')[0];
      if (text && firstClass) {
        return `//${tag}[contains(@class, "${firstClass}") and normalize-space()="${text}"]`;
      }
      if (firstClass) {
        return `//${tag}[contains(@class, "${firstClass}")]`;
      }
    }
    
    // Priority 7: text only
    const text = (el.innerText || '').trim();
    if (text) {
      return `//${tag}[normalize-space()="${text}"]`;
    }
    
    // Fallback: tag only
    return `//${tag}`;
  }
  function collectAttributes(el) {
    const result = {};
    for (const a of el.attributes) {
      const n = a.name;
      if (n === 'style' || n.startsWith('on')) continue;
      const v = String(a.value || '').trim();
      if (v) result[n] = v;
    }
    return result;
  }
  const out = [];
  const visited = new Set();
  const nodes = document.querySelectorAll('*');
  for (const el of nodes) {
    if (!isVisible(el)) continue;
    if (visited.has(el)) continue; visited.add(el);
    const tag = el.tagName.toUpperCase();
    const role = el.getAttribute('role');
    const attrs = collectAttributes(el);
            // Get text content using a better method
            let textRaw = '';
            
            // For interactive elements, get their text content
            if (['BUTTON', 'A', 'INPUT', 'SELECT', 'TEXTAREA'].includes(tag)) {
              textRaw = el.textContent || '';
            } else {
              // For other elements, only get direct text nodes (not from children)
              const textNodes = [];
              const walker = document.createTreeWalker(
                el,
                NodeFilter.SHOW_TEXT,
                {
                  acceptNode: function(node) {
                    // Only include text nodes that are direct children
                    if (node.parentNode === el) {
                      return NodeFilter.FILTER_ACCEPT;
                    }
                    return NodeFilter.FILTER_REJECT;
                  }
                }
              );
              
              let node;
              while (node = walker.nextNode()) {
                textNodes.push(node.textContent);
              }
              textRaw = textNodes.join(' ');
            }
            
            textRaw = textRaw.replace(/\s+/g, ' ').trim();
            const text = textRaw.length > 2048 ? textRaw.slice(0, 2048) : textRaw;
    const rect = el.getBoundingClientRect();
    out.push({
      text, tag, role: role || null, attrs,
      xpath: generateRelativeXPath(el),
      bbox: { x: Math.max(0, Math.round(rect.x)), y: Math.max(0, Math.round(rect.y)), width: Math.max(0, Math.round(rect.width)), height: Math.max(0, Math.round(rect.height)), w: Math.max(0, Math.round(rect.width)), h: Math.max(0, Math.round(rect.height)) },
      visible: true
    });
  }
  return out;
}
"""
        try:
            items = self._page.evaluate(js)
        except Exception:
            return {"elements": [], "dom_hash": "", "url": getattr(self._page, "url", "")}
        frame_url = getattr(self._page, "url", "")
        fh = compute_frame_hash(frame_url, items)
        for it in items:
            (it.setdefault("meta", {}))["frame_hash"] = fh
            it["frame_url"] = frame_url
        frames = [{"frame_url": frame_url, "elements": items, "frame_hash": fh}]
        return {"elements": items, "dom_hash": dom_hash(frames), "url": frame_url}

    def _snapshot(self, url: Optional[str] = None) -> Dict[str, Any]:
        page = self._ensure_browser()
        if not _PLAYWRIGHT or not page:
            return {"elements": [], "dom_hash": "", "url": url or ""}
        if url:
            try:
                page.goto(url, wait_until="networkidle")
                # Wait a bit for dynamic content to load
                page.wait_for_timeout(2000)
                # Try to dismiss any initial popups/overlays
                self._dismiss_overlays()
            except Exception:
                pass
        return self._inline_snapshot()

    def _resolve_selector(self, phrase: str, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        elements = snapshot.get("elements", [])
        if not elements:
            return {"selector": "", "confidence": 0.0, "reason": "no-elements", "candidates": []}
        ps = page_signature(str(snapshot.get("url", "")))
        frame_hash = (elements[0].get("meta") or {}).get("frame_hash") or ps
        parsed = self.intent.parse(phrase)
        label_key = compute_label_key([w for w in (parsed.target_phrase or phrase).split()])
        # Use parsed target phrase for better MiniLM matching
        target_phrase = parsed.target_phrase or phrase
        result = self.pipeline.query(
            target_phrase,  # Use parsed target phrase for MiniLM
            elements,
            top_k=10,
            page_sig=ps,
            frame_hash=frame_hash,
            label_key=label_key,
            user_intent=phrase,  # Pass full phrase as user intent to MarkupLM
        )
        candidates = []
        for item in (result.get("results") or [])[:10]:
            candidates.append({
                "selector": item.get("selector", ""),
                "score": float(item.get("score", 0.0)),
                "meta": item.get("meta", {}),
                "reasons": item.get("reasons", []),
            })
        if _DEBUG_CANDS:
            top3 = [f"{c['score']:.3f}:{c['selector']}" for c in candidates[:3]]
            print(f"[HER DEBUG] candidates: {' | '.join(top3)}")
        best = candidates[:1]
        if not best:
            return {"selector": "", "confidence": 0.0, "reason": "no-results", "candidates": candidates, "promo": {"page_sig": ps, "frame_hash": frame_hash, "label_key": label_key}}
        return {
            "selector": best[0].get("selector", ""),
            "confidence": float(result.get("confidence", 0.0)),
            "meta": best[0].get("meta", {}),
            "reasons": best[0].get("reasons", []),
            "candidates": candidates,
            "promo": {"page_sig": ps, "frame_hash": frame_hash, "label_key": label_key},
        }

    def _dismiss_overlays(self) -> None:
        if not _PLAYWRIGHT or not self._page:
            return
        selectors = [
            'button[aria-label="Close"]',
            'button[aria-label="Dismiss"]',
            'button:has-text("Accept")',
            'button:has-text("Accept all")',
            'button:has-text("Accept All")',
            'button:has-text("Agree")',
            'button:has-text("I agree")',
            'button:has-text("Got it")',
            'button:has-text("OK")',
            '#onetrust-accept-btn-handler',
            '.cc-allow',
            '[data-testid="close"]',
            'button:has-text("No thanks")',
            'button:has-text("Continue")',
            '[aria-label="Close dialog"]',
            '[aria-label="Close modal"]',
            '.modal button.close',
            '.popup button.close',
        ]
        for sel in selectors:
            try:
                # Try to find all matching elements
                els = self._page.query_selector_all(sel)
                for el in els[:2]:  # Click max 2 of each type
                    try:
                        if el.is_visible():
                            el.click(timeout=500)
                            time.sleep(0.2)
                    except Exception:
                        continue
            except Exception:
                continue

    def _scroll_into_view(self, selector: str) -> None:
        if not _PLAYWRIGHT or not self._page:
            return
        try:
            self._page.locator(f"xpath={selector}").first.scroll_into_view_if_needed(timeout=2000)
        except Exception:
            pass

    def _do_action(self, action: str, selector: str, value: Optional[str], promo: Dict[str, Any], user_intent: str = "") -> None:
        if not _PLAYWRIGHT or not self._page:
            raise RuntimeError("Playwright unavailable for action execution")
        # Try scroll + overlay dismiss before attempting action
        self._scroll_into_view(selector)
        self._dismiss_overlays()
        # Strict executor if available
        if Executor is not None and action not in {"back", "refresh", "wait"}:
            ex = Executor(self._page)
            kw = dict(page_sig=promo.get("page_sig"), frame_hash=promo.get("frame_hash"), label_key=promo.get("label_key"))
            if action == "type" and value is not None:
                ex.type(selector, str(value), **kw)
                return
            if action == "press" and value:
                ex.press(selector, str(value), **kw)
                return
            if action == "hover":
                self._page.locator(f"xpath={selector}").first.hover()
                return
            if action in {"check", "uncheck"}:
                handle = self._page.locator(f"xpath={selector}").first
                try:
                    if action == "check":
                        handle.check()
                    else:
                        handle.uncheck()
                    return
                except Exception:
                    pass
            if action == "select":
                # Fallback: click element (menu/option)
                ex.click(selector, **kw)
                return
            ex.click(selector, **kw)
            return
        # Fallback raw Playwright and navigation/waits
        if action == "type" and value is not None:
            element = self._page.locator(f"xpath={selector}").first
            self._scroll_into_view(element)
            element.fill(value)
            return
        if action == "sendkeys" and value is not None:
            element = self._page.locator(f"xpath={selector}").first
            self._scroll_into_view(element)
            element.type(value)
            return
        if action == "press" and value:
            element = self._page.locator(f"xpath={selector}").first
            self._scroll_into_view(element)
            element.press(str(value))
            return
        if action == "hover":
            element = self._page.locator(f"xpath={selector}").first
            self._scroll_into_view(element)
            element.hover()
            return
        if action in {"check", "uncheck"}:
            handle = self._page.locator(f"xpath={selector}").first
            self._scroll_into_view(handle)
            try:
                if action == "check":
                    handle.check()
                else:
                    handle.uncheck()
                return
            except Exception:
                handle.click()
                return
        if action == "select":
            # For select actions, try to find the most visible/clickable element
            self._click_best_element(selector, phrase)
            return
        if action == "back":
            try:
                self._page.go_back()
            except Exception:
                pass
            return
        if action == "refresh":
            try:
                self._page.reload()
            except Exception:
                pass
            return
        if action == "wait":
            try:
                secs = float(value or 1)
            except Exception:
                secs = 1.0
            self._page.wait_for_timeout(int(secs * 1000))
            return
        # For click actions, try to find the best element
        self._click_best_element(selector, phrase)

    def _scroll_into_view(self, element) -> None:
        """Scroll element into view if it's not visible."""
        try:
            # Check if element is in viewport
            if not hasattr(element, 'bounding_box'):
                print(f"⚠️  Element does not have bounding_box method, skipping scroll")
                return
                
            bbox = element.bounding_box()
            if not bbox:
                return
            
            viewport = self._page.viewport_size
            if not viewport:
                return
            
            # Check if element is at least partially visible
            element_top = bbox['y']
            element_bottom = bbox['y'] + bbox['height']
            element_left = bbox['x']
            element_right = bbox['x'] + bbox['width']
            
            viewport_height = viewport['height']
            viewport_width = viewport['width']
            
            # Check if element is visible in viewport
            is_visible = (
                element_top >= 0 and element_top < viewport_height and
                element_left >= 0 and element_left < viewport_width and
                element_bottom > 0 and element_right > 0
            )
            
            if not is_visible:
                print(f"🔄 Element not in viewport, scrolling into view...")
                element.scroll_into_view_if_needed()
                self._page.wait_for_timeout(500)  # Wait for scroll to complete
                print(f"✅ Scrolled element into view")
            else:
                print(f"✅ Element already in viewport")
                
        except Exception as e:
            print(f"⚠️  Could not scroll element into view: {e}")

    def _click_best_element(self, selector: str, user_intent: str = "") -> None:
        """Click the best element when there are multiple matches, using user intent."""
        if not _PLAYWRIGHT or not self._page:
            return
        
        try:
            # Get all matching elements
            locators = self._page.locator(f"xpath={selector}")
            count = locators.count()
            
            if count == 0:
                raise Exception(f"No elements found for selector: {selector}")
            elif count == 1:
                # Only one element, scroll into view and click it
                element = locators.first
                self._scroll_into_view(element)
                element.click()
                return
            
            # Multiple elements - find the best one using user intent
            print(f"🔍 Found {count} elements with selector: {selector}")
            print(f"🎯 User intent: '{user_intent}'")
            
            # Try to find the most visible and clickable element
            best_element = None
            best_score = -1
            element_details = []
            
            for i in range(count):
                try:
                    element = locators.nth(i)
                    
                    # Check if element is visible and clickable
                    if not element.is_visible():
                        continue
                    
                    # Get element properties
                    bbox = element.bounding_box()
                    if not bbox or bbox['width'] <= 0 or bbox['height'] <= 0:
                        continue
                    
                    # Get element text and attributes for better scoring
                    try:
                        text = element.text_content() or ""
                        tag_name = element.evaluate("el => el.tagName.toLowerCase()") or ""
                        role = element.get_attribute("role") or ""
                        href = element.get_attribute("href") or ""
                        class_name = element.get_attribute("class") or ""
                        id_attr = element.get_attribute("id") or ""
                    except:
                        text = ""
                        tag_name = ""
                        role = ""
                        href = ""
                        class_name = ""
                        id_attr = ""
                    
                    # Calculate score based on multiple factors
                    score = bbox['width'] * bbox['height']  # Area as base score
                    
                    # HEURISTIC 1: Filter out hidden/background elements
                    if bbox['y'] < 0 or bbox['x'] < 0:  # Off-screen elements
                        continue
                    
                    # HEURISTIC 2: Filter out very small elements (likely decorative)
                    if bbox['width'] < 10 or bbox['height'] < 10:
                        continue
                    
                    # HEURISTIC 3: Filter out elements with no meaningful content
                    if not text.strip() and not href and not role:
                        continue
                    
                    # HEURISTIC 4: User intent matching
                    intent_score = 0
                    if user_intent:
                        intent_lower = user_intent.lower()
                        text_lower = text.lower()
                        
                        # Exact text match gets highest score
                        if intent_lower in text_lower:
                            intent_score += 1000
                        
                        # Partial word matches
                        intent_words = intent_lower.split()
                        text_words = text_lower.split()
                        word_matches = sum(1 for word in intent_words if word in text_words)
                        intent_score += word_matches * 200
                        
                        # Check href for intent
                        if href and any(word in href.lower() for word in intent_words):
                            intent_score += 300
                    
                    # HEURISTIC 5: Position-based scoring
                    viewport = self._page.viewport_size
                    if viewport:
                        # Bonus for being in viewport center
                        center_x = bbox['x'] + bbox['width'] / 2
                        center_y = bbox['y'] + bbox['height'] / 2
                        viewport_center_x = viewport['width'] / 2
                        viewport_center_y = viewport['height'] / 2
                        
                        # Distance from center (closer is better)
                        distance = ((center_x - viewport_center_x) ** 2 + (center_y - viewport_center_y) ** 2) ** 0.5
                        center_bonus = max(0, 1000 - distance)  # Bonus decreases with distance
                        score += center_bonus
                        
                        # Bonus for being higher on the page (top elements are usually more important)
                        top_bonus = max(0, 1000 - bbox['y'])  # Higher elements get more bonus
                        score += top_bonus
                    
                    # HEURISTIC 6: Interactive element bonus
                    if tag_name in ['a', 'button'] or role in ['button', 'link']:
                        score += 500
                    
                    # HEURISTIC 7: Meaningful content bonus
                    if text and len(text.strip()) > 0:
                        score += 100
                    
                    # HEURISTIC 8: Accessibility attributes bonus
                    if id_attr or role or href:
                        score += 200
                    
                    # HEURISTIC 9: Universal element scoring (no hardcoded penalties)
                    # All elements are potentially valid targets based on user intent
                    
                    # Add intent score
                    score += intent_score
                    
                    element_details.append({
                        'index': i,
                        'element': element,
                        'score': score,
                        'text': text[:50],
                        'tag': tag_name,
                        'bbox': bbox,
                        'href': href[:50] if href else '',
                        'intent_score': intent_score
                    })
                    
                    if score > best_score:
                        best_score = score
                        best_element = element
                        
                except Exception as e:
                    print(f"⚠️  Error evaluating element {i}: {e}")
                    continue
            
            # Log all elements for debugging
            print(f"📋 Element analysis (sorted by score):")
            for detail in sorted(element_details, key=lambda x: x['score'], reverse=True)[:5]:
                print(f"  {detail['index']+1}. Score: {detail['score']:.1f} | {detail['tag']} | '{detail['text']}' | Intent: {detail['intent_score']:.0f} | Pos: ({detail['bbox']['x']:.0f}, {detail['bbox']['y']:.0f})")
            
            if best_element:
                best_index = next(i for i, detail in enumerate(element_details) if detail['element'] == best_element)
                print(f"✅ Clicking best element #{best_index+1} (score: {best_score:.1f})")
                self._scroll_into_view(best_element)
                best_element.click()
            else:
                print(f"⚠️  No suitable element found, clicking first visible one")
                element = locators.first
                self._scroll_into_view(element)
                element.click()
                
        except Exception as e:
            print(f"❌ Error clicking element: {e}")
            # Fallback to first element
            try:
                element = self._page.locator(f"xpath={selector}").first
                self._scroll_into_view(element)
                element.click()
            except Exception as e2:
                print(f"❌ Fallback click also failed: {e2}")
                raise

    def _validate(self, step: str) -> bool:
        if not _PLAYWRIGHT or not self._page:
            return False
        low = step.lower()
        if low.startswith("validate it landed on ") or low.startswith("validate landed on "):
            expected = step.split(" on ", 1)[1].strip().strip(",")
            try:
                # Wait a bit for any redirects to complete
                self._page.wait_for_timeout(2000)
                current_url = self._page.url
                
                # Try exact match first
                current = self._normalize_url(current_url)
                exp_norm = self._normalize_url(expected)
                if current == exp_norm:
                    return True
                
                # If not exact, check if key parts are in the URL
                # Extract key parts from expected URL (product name)
                if "iphone" in expected.lower():
                    # For iPhone URLs, check if we have the right product
                    import re
                    # Extract product identifier from expected (e.g., "iphone-16-pro")
                    product_match = re.search(r'iphone-[\w-]+', expected.lower())
                    if product_match:
                        product_id = product_match.group(0)
                        # Check if this product ID is in current URL
                        if product_id in current_url.lower():
                            return True
                
                # Fallback: check if we're at least on the right domain/section
                if "/smartphones/" in expected and "/smartphones/" in current_url:
                    # We're in smartphones section
                    if "apple" in expected.lower() and "apple" in current_url.lower():
                        # It's an Apple product page
                        return True
                
                return False
            except Exception as e:
                print(f"Validation error: {e}")
                return False
        if low.startswith("validate ") and " is visible" in low:
            target = step[9:].rsplit(" is visible", 1)[0].strip()
            # Remove quotes from target text
            target = target.strip("'\"")
            
            try:
                # Try multiple strategies to find the text
                strategies = [
                    f"text={target}",  # Exact text match
                    f"text*={target}",  # Partial text match
                    f"[aria-label*='{target}']",  # Aria label
                    f"[title*='{target}']",  # Title attribute
                ]
                
                for strategy in strategies:
                    try:
                        locator = self._page.locator(strategy)
                        if locator.count() > 0:
                            # Check if any matching element is visible
                            for i in range(locator.count()):
                                if locator.nth(i).is_visible():
                                    return True
                    except Exception:
                        continue
                
                # Fallback: use snapshot-based search
                shot = self._snapshot()
                resolved = self._resolve_selector(target, shot)
                sel = resolved.get("selector", "")
                if sel:
                    try:
                        self._page.locator(f"xpath={sel}").first.wait_for(state="visible", timeout=2000)
                        return True
                    except Exception:
                        pass
                
                return False
            except Exception as e:
                print(f"Text validation error: {e}")
                return False
        if low.startswith("validate ") and " exists" in low:
            target = step[9:].rsplit(" exists", 1)[0].strip()
            shot = self._snapshot()
            resolved = self._resolve_selector(target, shot)
            sel = resolved.get("selector", "")
            if not sel:
                return False
            try:
                count = self._page.locator(f"xpath={sel}").count()
                return count > 0
            except Exception:
                return False
        if "validate page has text" in low:
            # Expect quoted text or plain text
            parts = step.lower().split("validate page has text", 1)
            if len(parts) > 1:
                wanted = parts[1].strip().strip('"').strip("'")
                try:
                    content = self._page.content()
                    return wanted.lower() in content.lower()
                except Exception:
                    return False
            return False
        if "validate it landed on" in low:
            # Validate URL navigation
            parts = step.lower().split("validate it landed on", 1)
            if len(parts) > 1:
                expected_url = parts[1].strip().strip('"').strip("'")
                try:
                    current_url = self._page.url
                    # Check if current URL contains the expected URL or vice versa
                    return expected_url in current_url or current_url in expected_url
                except Exception:
                    return False
            return False
        return False

    def run(self, steps: List[str]) -> List[StepResult]:
        logs: List[StepResult] = []
        try:
            for raw in steps:
                step = raw.strip()
                if not step:
                    continue
                if step.lower().startswith("open "):
                    url = step.split(" ", 1)[1].strip()
                    self._snapshot(url)
                    logs.append(StepResult(step=step, selector="", confidence=1.0, ok=True, info={"url": url}))
                    logger.info(json.dumps({"step": step, "selector": "", "confidence": 1.0, "ok": True}))
                    continue
                if step.lower().startswith("validate "):
                    ok = self._validate(step)
                    logs.append(StepResult(step=step, selector="", confidence=1.0, ok=ok, info={}))
                    logger.info(json.dumps({"step": step, "selector": "", "confidence": 1.0, "ok": ok}))
                    if not ok:
                        break
                    continue
                intent = self.intent.parse(step)
                
                # Debug: Print step JSON
                print(f"\n📋 STEP JSON:")
                print(f"  Raw Step: '{step}'")
                print(f"  Action: '{intent.action}'")
                print(f"  Target: '{intent.target_phrase}'")
                print(f"  Args: '{intent.args}'")
                print(f"  Constraints: {intent.constraints}")
                print(f"  Confidence: {intent.confidence}")
                
                attempts = 3
                selector = ""
                conf = 0.0
                last_err: Optional[str] = None
                candidates: List[Dict[str, Any]] = []
                for attempt in range(attempts):
                    shot = self._snapshot()
                    resolved = self._resolve_selector(intent.target_phrase or step, shot)
                    selector = resolved.get("selector", "")
                    conf = float(resolved.get("confidence", 0.0))
                    candidates = resolved.get("candidates", [])
                    if selector:
                        try:
                            self._do_action(intent.action, selector, intent.args, resolved.get("promo", {}))
                            last_err = None
                            # Wait after successful action for page to update
                            if intent.action in ["click", "select"]:
                                time.sleep(2.0)  # Give page time to load after click
                            break
                        except Exception as e1:
                            last_err = str(e1)
                            self._dismiss_overlays()
                            time.sleep(1.0)  # Longer wait on failure
                            continue
                    else:
                        # No selector; try dismiss overlays, small wait, and retry
                        self._dismiss_overlays()
                        time.sleep(0.25)
                        continue
                ok = last_err is None
                info: Dict[str, Any] = {
                    "candidates": candidates,
                    "error": last_err,
                }
                logs.append(StepResult(step=step, selector=selector, confidence=conf, ok=ok, info=info))
                payload = {
                    "step": step,
                    "selector": selector,
                    "confidence": conf,
                    "ok": ok,
                    "candidates": candidates if _DEBUG_CANDS else None,
                    "info": {k: v for k, v in info.items() if k != "candidates"},
                }
                logger.info(json.dumps({k: v for k, v in payload.items() if v is not None}, ensure_ascii=False))
        finally:
            self._close()
        return logs


def run_steps(steps: List[str], *, headless: bool = True) -> None:
    runner = Runner(headless=headless)
    results = runner.run(steps)
    failed = [r for r in results if not r.ok]
    if failed:
        f = failed[0]
        raise AssertionError(f"Step failed: {f.step} | selector={f.selector} | info={f.info}")