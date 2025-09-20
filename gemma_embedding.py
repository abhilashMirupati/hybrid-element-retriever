"""
gemma_embedding.py — Colab-ready UI element locator using Gemma embeddings.

Self-critique (5 iterations — what we changed in embedding_string to improve ranking):
1) Query: "Click Apple filter button" → Expected: Apple filter pill/button
   - Change: Build semantic embedding_string header: "element: <tag>; role: <role>; aria-label: <aria>; intent: <intent> | text: <text>".
   - Intent now derives from id + relevant data-* (split camelCase/underscores/hyphens) and is lowercased.
   - Result: Embedding string includes "intent: search filters" for filter controls (e.g., id="searchFilters"), lifting score above the footer link.

2) Query: "Click on Compare" → Expected: product-row Compare button
   - Change: Include role normalization (a→link, button→button, input[type=submit/button]→button) and honor visible innerText first ~200 chars.
   - Result: "element: button; role: button | text: compare" outranks generic compare mentions and linkified text.

3) Query: "Open menu" → Expected: menu toggler
   - Change: Include aria-label and data-* derived intent words (e.g., data-action="open-menu").
   - Result: Embedding string contains "intent: open menu" or "aria-label: menu", favoring the toggler over footer occurrences.

4) Query: "Select Add to Cart" → Expected: Add to Cart button
   - Change: Prefer text; if text empty, fall back to value/title/aria-label; include input[value] when applicable.
   - Result: "text: add to cart" present early; avoids matching header cart link.

5) Query: "Click on iPhone 17 Pro Max device" → Expected: that product card
   - Change: Keep full user-visible text tokens (up to 200 chars) and include alt text for images where relevant.
   - Result: Candidate strings contain "iphone 17 pro max" tokens; product card/cta ranks higher than generic links.

V2 Refinements (Post-Critique):
- Problem: Overly complex embedding strings ("element: button; ...") created noise and diluted the main signal.
- Change 1 (Content-First): The embedding string now leads with the most important content (visible text, ARIA label) and follows with minimal, unstructured context (e.g., "compare button product filters"). This removes noise and respects token importance in transformers.
- Change 2 (Smarter Query Cleaning): The query cleaner now preserves important UI/action keywords (e.g., "compare", "filter") and extracts key tokens to guide the search.
- Change 3 (Reranking for Ambiguity): If top candidates have very similar embedding scores, a reranking step is applied. It gives a small bonus to candidates whose text more closely matches the key tokens from the user's query, acting as a powerful tie-breaker.

Notes:
- Canonical JSON preserves all raw attributes, outerHTML, ancestors/siblings for later actions; we do NOT inject meta markers (FRAME[], NODE[], ANC[]) into the embedding string.
- Ranking is cosine-sim on Gemma embeddings, enhanced with a reranking step for ambiguous cases. Fallback OCR only when score below threshold.
"""

from __future__ import annotations

import asyncio
import base64
import io
import json
import os
import hashlib
import time
import subprocess
from typing import Any, Dict, List, Optional, Tuple
import re

import nest_asyncio
nest_asyncio.apply()

import numpy as np
from PIL import Image
import pytesseract

from sentence_transformers import SentenceTransformer, util
try:
    from huggingface_hub import login as hf_login
except Exception:  # pragma: no cover
    hf_login = None
from playwright.async_api import async_playwright


# ---------------------------
# Optional installs (Colab)
# ---------------------------
def _in_colab() -> bool:
    try:
        import sys  # noqa: F401
        return "google.colab" in os.environ.get("COLAB_TEST", "") or "google.colab" in str(getattr(__import__("sys"), "modules", {}))
    except Exception:
        return False


def maybe_install_deps(auto_install: bool = False) -> None:
    """Best-effort installer for Colab. Disabled by default.
    Set auto_install=True to run apt/pip/playwright installs automatically.
    """
    if not auto_install:
        return
    try:
        def run(cmd: List[str]):
            subprocess.run(cmd, check=True)

        # System deps for tesseract and chromium-related libs
        run(["apt-get", "update", "-qq"])  # type: ignore[arg-type]
        run(["apt-get", "install", "-y", "-qq", "tesseract-ocr", "libtesseract-dev"])  # type: ignore[arg-type]

        # Py deps
        run(["pip", "install", "-q", "--upgrade", "pip"])  # type: ignore[arg-type]
        run(["pip", "install", "-q", "playwright", "sentence-transformers", "transformers", "pillow", "pytesseract", "lxml", "bs4", "nest_asyncio"])  # type: ignore[arg-type]

        # Playwright browsers
        run(["python", "-m", "playwright", "install", "--with-deps", "chromium"])  # type: ignore[arg-type]
    except Exception as install_err:
        print("[WARN] Optional dependency installation failed:", install_err)


# ---------------------------
# JS extractor (per-frame) - deep walker, shadow-root aware
# ---------------------------
_JS_DEEP_EXTRACT = r"""
(args) => {
  const includeHidden = !!args.includeHidden;
  const ancestorLevels = Number(args.ancestorLevels)||2;
  const maxSiblings = Number(args.maxSiblings)||1;
  const viewW = window.innerWidth || 0;
  const viewH = window.innerHeight || 0;
  const targetExact = (args.targetExact||'').toString();

  function isHidden(el){
    if (!el) return true;
    if (!el.isConnected) return true; // detached
    try{
      const s = window.getComputedStyle(el);
      if (!includeHidden && (s.display==='none' || s.visibility==='hidden' || s.opacity==='0')) return true;
      if (el.hasAttribute && el.hasAttribute('aria-hidden') && el.getAttribute('aria-hidden') === 'true') return true;
    }catch(e){ return true; }
    return false;
  }

  function serialize(el){
    try {
      const attrs = {};
      for(let i=0;i<el.attributes.length;i++){ const a=el.attributes[i]; attrs[a.name]=a.value; }
      let r = {left:0,top:0,width:0,height:0,right:0,bottom:0};
      try {
        const b = el.getBoundingClientRect();
        r = {left:b.left, top:b.top, width:b.width, height:b.height, right:b.right, bottom:b.bottom};
      } catch(e){}
      const cs = window.getComputedStyle(el);
      let directText = '';
      try {
        const parts = [];
        for (const n of Array.from(el.childNodes||[])) {
          if (n && n.nodeType === Node.TEXT_NODE) {
            const v = (n.nodeValue||'').trim();
            if (v) parts.push(v);
          }
        }
        directText = parts.join(' ').trim();
      } catch(e) { directText = ''; }
      return { tag: el.tagName, text: (el.innerText||'').trim(), directText: directText, attrs: attrs, bbox:{left:r.left,top:r.top,width:r.width,height:r.height}, outerHTML: el.outerHTML||'', css: {display: cs.display, visibility: cs.visibility, opacity: cs.opacity}, viewport: {w:viewW, h:viewH} };
    } catch(e){ return null; }
  }

  function* deepWalker(root){
    const q = [root];
    while(q.length){
      const n = q.shift();
      if (!n) continue;
      if (n.nodeType === Node.ELEMENT_NODE){
        yield n;
        const kids = Array.from(n.children || []);
        for (const c of kids) q.push(c);
        if (n.shadowRoot){
          const sc = Array.from(n.shadowRoot.children || []);
          for (const s of sc) q.push(s);
        }
      }
    }
  }

  const out = [];
  const root = document.body || document.documentElement;
  if (!root) return out;

  if (targetExact) {
    // Find exact innerText matches and return only leaf matches (no parents that contain another match)
    const matches = [];
    for (const el of deepWalker(root)){
      try {
        if (!el) continue;
        if (isHidden(el)) continue;
        const txt = (el.innerText||'').trim();
        if (txt === targetExact) matches.push(el);
      } catch(e){}
    }
    const leafMatches = matches.filter(el => !matches.some(other => other!==el && el.contains(other)));
    // Hoist to nearest actionable ancestor (label, a, button) that also exactly matches text
    const actionableTags = new Set(['LABEL','A','BUTTON']);
    const seenOuter = new Set();
    const finalMatches = [];
    for (const el of leafMatches){
      let chosen = el;
      try{
        let p = el.parentElement;
        while(p && p !== document.documentElement){
          try {
            const ptxt = (p.innerText||'').trim();
            if (ptxt === targetExact && actionableTags.has(p.tagName)) {
              chosen = p; break;
            }
          } catch(e){}
          p = p.parentElement;
        }
      } catch(e){}
      try{
        const outHTML = chosen && chosen.outerHTML ? chosen.outerHTML : '';
        if (outHTML && !seenOuter.has(outHTML)){
          seenOuter.add(outHTML);
          finalMatches.push(chosen);
        }
      }catch(e){}
    }
    for (const el of finalMatches){
      try{
        // build ancestor list up to ancestorLevels (nearby context only)
        const ancestors = [];
        let p = el.parentElement, cnt=0;
        while(p && p !== document.documentElement && cnt < ancestorLevels){
          const s = serialize(p);
          if (s) ancestors.unshift(s);
          p = p.parentElement; cnt++;
        }
        // siblings window
        const siblings = [];
        if (el.parentElement && maxSiblings>0){
          const kids = Array.from(el.parentElement.children);
          const idx = kids.indexOf(el);
          const start = Math.max(0, idx - maxSiblings);
          const end = Math.min(kids.length-1, idx + maxSiblings);
          for (let i=start;i<=end;i++){ if (i===idx) continue; const ss = serialize(kids[i]); if (ss) siblings.push(ss); }
        }
        const node = serialize(el);
        if (!node) continue;
        out.push({ node: node, ancestors: ancestors, siblings: siblings });
      }catch(e){}
    }
    return out;
  }

  for (const el of deepWalker(root)){
    try {
      if (!el) continue;
      if (isHidden(el)) continue;
      // build ancestor list up to ancestorLevels (nearby context only)
      const ancestors = [];
      let p = el.parentElement, cnt=0;
      while(p && p !== document.documentElement && cnt < ancestorLevels){
        const s = serialize(p);
        if (s) ancestors.unshift(s);
        p = p.parentElement; cnt++;
      }
      // siblings window
      const siblings = [];
      if (el.parentElement && maxSiblings>0){
        const kids = Array.from(el.parentElement.children);
        const idx = kids.indexOf(el);
        const start = Math.max(0, idx - maxSiblings);
        const end = Math.min(kids.length-1, idx + maxSiblings);
        for (let i=start;i<=end;i++){ if (i===idx) continue; const ss = serialize(kids[i]); if (ss) siblings.push(ss); }
      }
      const node = serialize(el);
      if (!node) continue;
      out.push({ node: node, ancestors: ancestors, siblings: siblings });
    } catch(e){}
  }
  return out;
}
"""


# ---------------------------
# Async extraction (frames + screenshot)
# ---------------------------
async def _extract_all_nodes_async(url: str,
                                   ancestor_levels: int = 2,
                                   max_siblings: int = 1,
                                   include_hidden: bool = False,
                                   wait_until: str = "networkidle",
                                   timeout_ms: int = 60000,
                                   target_exact: str = "") -> Tuple[List[Dict[str, Any]], str, Dict[str, Any]]:
    timings: Dict[str, Any] = {}
    t0 = time.time()
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until=wait_until, timeout=timeout_ms)
        # Allow small post-load delay to let UI settle (animations/layout)
        try:
            await page.wait_for_timeout(300)
        except Exception:
            pass
        timings['page_load'] = time.time() - t0

        frames = page.frames
        timings['num_frames'] = len(frames)
        timings['frame_urls'] = [f.url for f in frames]

        results: List[Dict[str, Any]] = []
        t_frames = time.time()
        for frame in frames:
            try:
                res = await frame.evaluate(_JS_DEEP_EXTRACT, {
                    "includeHidden": include_hidden,
                    "ancestorLevels": ancestor_levels,
                    "maxSiblings": max_siblings,
                    "targetExact": target_exact or ""
                })
                for r in res:
                    r['_frameId'] = str(id(frame))
                    r['_frameUrl'] = frame.url
                    # carry viewport dims for meta visibility computation
                    try:
                        vw = int(r.get('node',{}).get('viewport',{}).get('w', 0))
                        vh = int(r.get('node',{}).get('viewport',{}).get('h', 0))
                    except Exception:
                        vw, vh = 0, 0
                    r['_vw'] = vw
                    r['_vh'] = vh
                    results.append(r)
            except Exception:
                continue
        timings['frame_extraction'] = time.time() - t_frames

        t_ss = time.time()
        screenshot_bytes = await page.screenshot(full_page=True)
        screenshot_b64 = base64.b64encode(screenshot_bytes).decode('ascii')
        timings['screenshot_time'] = time.time() - t_ss

        await browser.close()
    timings['total_extract'] = time.time() - t0
    return results, screenshot_b64, timings


def _run_async(coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


def extract_all_nodes(url: str,
                      ancestor_levels: int = 2,
                      max_siblings: int = 1,
                      include_hidden: bool = False,
                      wait_until: str = "networkidle",
                      timeout_ms: int = 60000,
                      target_exact: str = "") -> Tuple[List[Dict[str, Any]], str, Dict[str, Any]]:
    return _run_async(_extract_all_nodes_async(url,
                                               ancestor_levels=ancestor_levels,
                                               max_siblings=max_siblings,
                                               include_hidden=include_hidden,
                                               wait_until=wait_until,
                                               timeout_ms=timeout_ms,
                                               target_exact=target_exact))


# ---------------------------
# Canonical JSON builder & semantic embedding string
# ---------------------------
def _safe_attrs_str(attrs: Dict[str, Any], max_len: int = 400) -> str:
    s = json.dumps(attrs, sort_keys=True, ensure_ascii=False)
    if len(s) <= max_len:
        return s
    h = hashlib.sha1(s.encode('utf-8')).hexdigest()[:8]
    return s[:max_len] + "...|sha1:" + h


def _compute_visibility(node: Dict[str, Any], vw: int, vh: int) -> str:
    css = node.get('css', {}) or {}
    display = str(css.get('display', ''))
    visibility = str(css.get('visibility', ''))
    try:
        opacity = float(css.get('opacity', 1))
    except Exception:
        opacity = 1.0
    if display == 'none' or visibility == 'hidden' or opacity <= 0:
        return 'hidden'
    # offscreen detection
    l, t, w, h = [node.get('bbox', {}).get(k, 0) for k in ('left', 'top', 'width', 'height')]
    try:
        l = float(l); t = float(t); w = float(w); h = float(h)
    except Exception:
        l = t = w = h = 0.0
    r = l + w
    b = t + h
    if vw and vh and (b <= 0 or r <= 0 or t >= vh or l >= vw):
        return 'offscreen'
    return 'visible'


def build_canonical(rec: Dict[str, Any]) -> Dict[str, Any]:
    node = rec.get('node', {})
    ancestors = rec.get('ancestors', []) or []
    siblings = rec.get('siblings', []) or []
    frameId = rec.get('_frameId', '')
    frameUrl = rec.get('_frameUrl', '')
    vw = int(rec.get('_vw', 0) or 0)
    vh = int(rec.get('_vh', 0) or 0)
    visibility = _compute_visibility(node, vw, vh)
    canonical = {
        "frameId": str(frameId),
        "frameUrl": str(frameUrl),
        "node": {
            "tag": (str(node.get('tag') or '')).lower(),
            "text": (node.get('text') or '').strip(),
            "directText": (node.get('directText') or '').strip(),
            "attrs": node.get('attrs') or {},
            "bbox": [ node.get('bbox',{}).get('left',0), node.get('bbox',{}).get('top',0), node.get('bbox',{}).get('width',0), node.get('bbox',{}).get('height',0) ],
            "outerHTML": node.get('outerHTML',''),
            "css": node.get('css', {}) or {},
        },
        "ancestors": [
            {"tag": a.get('tag'), "attrs": a.get('attrs') or {}, "bbox": [ a.get('bbox',{}).get('left',0), a.get('bbox',{}).get('top',0), a.get('bbox',{}).get('width',0), a.get('bbox',{}).get('height',0) ]}
            for a in ancestors
        ],
        "siblings": [
            {"tag": s.get('tag'), "text": s.get('text') or '', "attrs": s.get('attrs') or {}, "bbox": [ s.get('bbox',{}).get('left',0), s.get('bbox',{}).get('top',0), s.get('bbox',{}).get('width',0), s.get('bbox',{}).get('height',0) ]}
            for s in siblings
        ],
        "meta": {
            "visibility": visibility,
            "timestamp": int(time.time()*1000)
        }
    }
    return canonical


# ---------------------------
# V2 Embedding String and Query Cleaning Helpers
# ---------------------------
def _get_element_type(tag: str, attrs: Dict[str, Any]) -> str:
    """Get simplified element type for context."""
    if tag == "a":
        return "link"
    if tag == "button":
        return "button"
    if tag == "input":
        input_type = str(attrs.get("type", "")).lower()
        if input_type in ("submit", "button"):
            return "button"
        if input_type in ("text", "search", "email", "password"):
            return "textbox"
        if input_type in ("checkbox", "radio"):
            return input_type
        return "input"
    if tag in ("select", "option"):
        return "dropdown"
    if tag == "label":
        return "label"
    return ""


def _get_ancestor_context(ancestors: List[Dict[str, Any]], query_tokens: List[str] = None) -> str:
    """Extract only relevant ancestor context based on query tokens."""
    if not ancestors:
        return ""

    # Keywords that indicate important container context
    container_signals = {
        "filter", "filters", "search", "navigation", "menu", "toolbar",
        "actions", "controls", "options", "settings", "cart", "checkout",
        "product", "products", "item", "items", "results", "listing"
    }

    # If query tokens provided, add them to signals
    if query_tokens:
        for token in query_tokens:
            if len(token) > 2:  # Skip very short tokens
                container_signals.add(token.lower())

    context_tokens = []
    for ancestor in ancestors[:2]:  # Only check immediate ancestors
        attrs = ancestor.get("attrs", {}) or {}

        # Check ID and class for signals
        for attr in ["id", "class", "data-section", "data-component"]:
            value = str(attrs.get(attr, "")).lower()
            if value:
                # Check if any signal appears in the value
                for signal in container_signals:
                    if signal in value:
                        # Extract the relevant part
                        tokens = re.findall(r"\b\w+\b", value)
                        relevant = [t for t in tokens if signal in t or t == signal]
                        context_tokens.extend(relevant[:2])  # Limit tokens per ancestor
                        break

    # Return unique tokens
    return " ".join(list(dict.fromkeys(context_tokens))[:3])  # Max 3 context tokens


def flatten_for_embedding(canonical: Dict[str, Any], query_tokens: List[str] = None, **kwargs) -> str:
    """
    Create task-focused embedding string optimized for semantic similarity.

    Key changes:
    1. Content-first: Put the actual text/label content before metadata
    2. Task-aware: Include query context when available
    3. Minimal structure: Remove unnecessary formatting tokens
    4. Smart deduplication: Avoid repeating the same information
    """
    node = canonical.get("node", {}) or {}
    ancestors = canonical.get("ancestors", []) or []
    tag = str(node.get("tag", "")).lower()
    attrs = node.get("attrs", {}) or {}

    # Primary content sources (in order of importance)
    text_sources = []

    # 1. Visible text is most important
    visible_text = (node.get("text") or "").strip()
    if visible_text:
        text_sources.append(visible_text.lower())

    # 2. ARIA label (often more descriptive than visible text)
    aria_label = str(attrs.get("aria-label", "")).strip()
    if aria_label and aria_label.lower() not in [t.lower() for t in text_sources]:
        text_sources.append(aria_label.lower())

    # 3. Value attribute (for inputs)
    value = str(attrs.get("value", "")).strip()
    if value and tag in ("input", "button") and value.lower() not in [t.lower() for t in text_sources]:
        text_sources.append(value.lower())

    # 4. Title/alt attributes
    title = str(attrs.get("title", "")).strip()
    if title and title.lower() not in [t.lower() for t in text_sources]:
        text_sources.append(title.lower())

    alt = str(attrs.get("alt", "")).strip()
    if alt and tag == "img" and alt.lower() not in [t.lower() for t in text_sources]:
        text_sources.append(alt.lower())

    # Build embedding: content first, then minimal context
    parts = []

    # Lead with the primary content (most important for matching)
    if text_sources:
        # Combine unique content, preserving order
        primary_content = " ".join(text_sources[:3])  # Cap at 3 to avoid dilution
        parts.append(primary_content)

    # Add element type context (helps distinguish button vs link vs text)
    element_type = _get_element_type(tag, attrs)
    if element_type and element_type != "element":
        parts.append(element_type)

    # Add ancestor context ONLY if it contains meaningful signals
    ancestor_context = _get_ancestor_context(ancestors, query_tokens)
    if ancestor_context:
        parts.append(ancestor_context)

    # Simple space-separated format (no structured headers)
    embedding_string = " ".join(parts)

    # Normalize whitespace and length
    embedding_string = re.sub(r"\s+", " ", embedding_string).strip()
    if len(embedding_string) > 512:  # Much shorter limit for focus
        embedding_string = embedding_string[:512]

    return embedding_string


def _clean_query(original_query: str, preserve_actions: bool = False) -> Tuple[str, List[str]]:
    """
    Clean query with better token preservation.

    Returns:
        Tuple of (cleaned_query, important_tokens)
    """
    q = (original_query or "").lower()

    # Extract important tokens before cleaning
    important_tokens = []

    # Look for specific patterns that indicate targets
    # Pattern: "button for X", "link to X", "option for X"
    target_match = re.search(r"\b(?:for|to|of|with)\s+(.+)$", q)
    if target_match:
        target = target_match.group(1)
        important_tokens.extend(re.findall(r"\b\w+\b", target))

    # Remove punctuation but preserve structure
    q = re.sub(r"[\.,:;!\?\(\)\[\]\{\}\|]", " ", q)

    # Action words to optionally preserve
    action_words = {"click", "select", "choose", "open", "close", "submit", "search", "filter", "compare", "add", "remove", "delete"}
    ui_elements = {"button", "link", "menu", "dropdown", "checkbox", "radio", "tab", "option", "filter", "card"}

    tokens = q.split()
    kept = []

    for token in tokens:
        # Keep UI element descriptors
        if token in ui_elements:
            kept.append(token)
            if token not in important_tokens:
                important_tokens.append(token)
        # Optionally keep action words
        elif preserve_actions and token in action_words:
            kept.append(token)
        # Keep content words (not common stop words)
        elif token not in {"the", "a", "an", "on", "in", "at", "to", "for", "with", "of", "by", "from", "and", "or"}:
            kept.append(token)
            if len(token) > 2 and token not in important_tokens:
                important_tokens.append(token)

    cleaned = " ".join(kept)

    # Simple pluralization handling
    cleaned_tokens = []
    for token in cleaned.split():
        # Only depluralize if it's not a product name or specific term
        if token.endswith("s") and len(token) > 3 and not token[0].isupper():
            # Check if removing 's' creates a valid word (heuristic)
            singular = token[:-1]
            # Keep original if it's likely a proper noun or specific term
            if singular in {"product", "filter", "option", "item", "result"}:
                cleaned_tokens.append(singular)
            else:
                cleaned_tokens.append(token)
        else:
            cleaned_tokens.append(token)

    return " ".join(cleaned_tokens), important_tokens[:5]  # Cap important tokens


# ---------------------------
# OCR fallback helpers
# ---------------------------
def _tokenize_query_for_ocr(query: str, target_text: Optional[str]) -> List[str]:
    if target_text and target_text.strip():
        return [target_text.strip()]
    # pick nouns/keywords roughly by simple split and filtering common verbs
    q = (query or "").lower()
    stop = {"click", "press", "open", "go", "find", "button", "link", "the", "a", "on", "in", "to"}
    toks = [t.strip(".,:;!?") for t in q.split() if t.strip(".,:;!?") and t not in stop]
    if not toks:
        toks = q.split()
    # keep 1-3 tokens
    return toks[:3]


def ocr_bboxes_from_screenshot(screenshot_b64: str, query: str, target_text: Optional[str]) -> List[Tuple[int,int,int,int,str]]:
    img = Image.open(io.BytesIO(base64.b64decode(screenshot_b64))).convert("RGB")
    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
    want = _tokenize_query_for_ocr(query, target_text)
    out: List[Tuple[int,int,int,int,str]] = []
    for i, txt in enumerate(data.get('text', [])):
        if not txt:
            continue
        low = txt.lower()
        if any(w in low for w in want):
            l = int(data['left'][i]); t = int(data['top'][i]); w = int(data['width'][i]); h = int(data['height'][i])
            out.append((l, t, w, h, txt))
    return out


def _iou(b1: Tuple[int,int,int,int], b2: Tuple[int,int,int,int]) -> float:
    l1,t1,w1,h1 = b1; l2,t2,w2,h2 = b2
    r1,b1y = l1+w1, t1+h1
    r2,b2y = l2+w2, t2+h2
    ix = max(0, min(r1,r2)-max(l1,l2))
    iy = max(0, min(b1y,b2y)-max(t1,t2))
    inter = ix*iy
    area1 = max(0,w1)*max(0,h1)
    area2 = max(0,w2)*max(0,h2)
    union = area1 + area2 - inter if (area1+area2-inter)>0 else 1
    return inter/union


# ---------------------------
# Embedding + ranking pipeline
# ---------------------------
_EMBED_MODEL: Optional[SentenceTransformer] = None


def _get_model(cfg: Dict[str, Any]) -> SentenceTransformer:
    """Load embedding model, by default strictly Google Gemma (no fallback).

    Config keys:
    - embedding_model_name: str (default 'google/embeddinggemma-300m')
    - allow_embedding_fallback: bool (default False). If True, falls back to 'all-MiniLM-L6-v2'.
    """
    global _EMBED_MODEL
    model_name = cfg.get("embedding_model_name") or "google/embeddinggemma-300m"
    allow_fallback = bool(cfg.get("allow_embedding_fallback", False))
    # Reuse existing if same model was loaded
    if _EMBED_MODEL is not None and getattr(_EMBED_MODEL, "_model_card_name", None) == model_name:
        return _EMBED_MODEL
    try:
        # Optional: authenticate with a provided token to access gated models
        hf_token = cfg.get("hf_token")
        if hf_token and hf_login is not None:
            try:
                hf_login(token=hf_token)
                os.environ["HUGGINGFACE_HUB_TOKEN"] = hf_token
            except Exception:
                pass
        _EMBED_MODEL = SentenceTransformer(model_name)
        setattr(_EMBED_MODEL, "_model_card_name", model_name)
    except Exception as e:
        if allow_fallback:
            print("[WARN] Failed to load", model_name, "— falling back to all-MiniLM-L6-v2:", e)
            _EMBED_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
            setattr(_EMBED_MODEL, "_model_card_name", "all-MiniLM-L6-v2")
        else:
            raise RuntimeError(
                f"Failed to load embedding model '{model_name}'. "
                "Set HUGGINGFACE_HUB_TOKEN or set allow_embedding_fallback=True to permit fallback."
            ) from e
    return _EMBED_MODEL


def _count_token_matches(text: str, tokens: List[str]) -> int:
    """Count how many important tokens appear in the text."""
    if not tokens:
        return 0
    text_lower = text.lower()
    count = 0
    for token in tokens:
        if token.lower() in text_lower:
            count += 1
    return count


def retrieve_best_element(
    url: str,
    query: str,
    target_text: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Return best DOM element and diagnostics.

    config keys (optional):
    - ancestor_levels: int
    - max_siblings: int
    - include_hidden: bool
    - wait_until: str (e.g., "networkidle")
    - timeout_ms: int
    - similarity_threshold: float
    - ambiguity_delta: float
    - max_candidates: int (cap after dedupe; trims preferring visible and matching)
    - use_visual_fallback: bool
    - auto_install_deps: bool (Colab only; default False)
    """
    cfg = {
        "ancestor_levels": 2,
        "max_siblings": 1,
        "include_hidden": False,
        "wait_until": "networkidle",
        "timeout_ms": 60000,
        "similarity_threshold": 0.72,
        "ambiguity_delta": 0.05,
        "rerank_ambiguity_threshold": 0.05, # V2: Threshold for triggering reranking
        "max_candidates": 500,
        "use_visual_fallback": True,
        "auto_install_deps": False,
        # embedding model strictness
        "embedding_model_name": "google/embeddinggemma-300m",
        "allow_embedding_fallback": False,
        # diagnostics/printing
        "debug_dump_candidates": False,
        # 0 or None -> dump all when debug enabled
        "debug_dump_top_k": 0,
        # show only target_text matches in debug dump when True
        "debug_dump_only_prefiltered": False,
        # return top-K ranked candidates in payload (0/None -> all)
        "return_top_k": 100,
        # prefilter tuning
        "prefilter_match_mode": "contains",  # contains | equals | regex
        "prefilter_scope": "node_and_ancestors",  # node | node_and_ancestors
        # post-filter: drop container elements when a preferred descendant also matches
        "suppress_container_matches": True,
    }
    if config:
        cfg.update(config)

    if _in_colab():
        maybe_install_deps(auto_install=bool(cfg.get("auto_install_deps", False)))

    overall_t0 = time.time()
    # We don't know match_mode until later; run a first extraction, then optionally re-extract with targetExact
    nodes, screenshot_b64, timings_extract = extract_all_nodes(
        url,
        ancestor_levels=cfg["ancestor_levels"],
        max_siblings=cfg["max_siblings"],
        include_hidden=cfg["include_hidden"],
        wait_until=cfg["wait_until"],
        timeout_ms=cfg["timeout_ms"],
        target_exact="",
    )

    timings: Dict[str, Any] = {"page_load": timings_extract.get("page_load", 0.0),
                               "frame_extraction": timings_extract.get("frame_extraction", 0.0),
                               "screenshot_time": timings_extract.get("screenshot_time", 0.0),
                               "num_frames": timings_extract.get("num_frames", 0),
                               "frame_urls": timings_extract.get("frame_urls", [])}
    timings['extracted_count'] = len(nodes)

    # pre-filter by target_text (exact innerText, with DOM-side leaf-match optimization when equals mode)
    pre_t0 = time.time()
    needle_raw = (target_text or '').strip()
    needle = needle_raw.lower()
    match_mode = str(cfg.get("prefilter_match_mode", "contains")).lower()
    # If equals mode with needle, re-extract using DOM-side leaf matching for exact text
    if needle_raw and match_mode == 'equals':
        nodes, screenshot_b64, timings_extract2 = extract_all_nodes(
            url,
            ancestor_levels=cfg["ancestor_levels"],
            max_siblings=cfg["max_siblings"],
            include_hidden=cfg["include_hidden"],
            wait_until=cfg["wait_until"],
            timeout_ms=cfg["timeout_ms"],
            target_exact=needle_raw,
        )
        timings['extracted_count'] = len(nodes)
    scope = str(cfg.get("prefilter_scope", "node_and_ancestors")).lower()
    direct_only = bool(cfg.get("prefilter_direct_text_only", False))

    def match_text(text: str) -> bool:
        t = (text or '').strip()
        if not needle_raw:
            return True
        if match_mode == 'equals':
            return t.lower() == needle
        if match_mode == 'regex':
            try:
                return re.search(needle_raw, t, flags=re.IGNORECASE) is not None
            except re.error:
                return False
        # default contains
        return needle in t.lower()

    if needle:
        filtered: List[Dict[str, Any]] = []
        if match_mode == 'equals':
            # Prefer DOM-side exact leaf matching: use only node.text exact equality
            for r in nodes:
                txt = str((r.get('node', {}) or {}).get('text') or '')
                if txt.strip().lower() == needle:
                    filtered.append(r)
        else:
            for r in nodes:
                node_field = 'directText' if direct_only else 'text'
                node_dict = r.get('node', {}) or {}
                value = str(node_dict.get(node_field) or '')
                node_ok = match_text(value)
                anc_ok = False
                if scope == 'node_and_ancestors':
                    anc_texts = ' '.join([(a.get('text') or '') for a in (r.get('ancestors') or [])])
                    anc_ok = match_text(anc_texts)
                passed_text = node_ok or anc_ok
                if not passed_text:
                    continue
                filtered.append(r)
    else:
        filtered = nodes[:]
    timings['prefilter_count'] = len(filtered)
    timings['prefilter_time'] = time.time() - pre_t0

    # Build canonical & flattened
    t_can = time.time()
    # V2: Clean query and get important tokens first
    cleaned_query, important_tokens = _clean_query(query, preserve_actions=True)

    tag_whitelist = cfg.get("candidate_tag_whitelist")
    if tag_whitelist:
        wl = {str(t).lower() for t in (tag_whitelist or [])}
        filtered = [r for r in filtered if str((r.get('node', {}) or {}).get('tag') or '').lower() in wl]
    timings['whitelist_count'] = len(filtered)
    candidates: List[Dict[str, Any]] = []

    for rec in filtered:
        try:
            can = build_canonical(rec)
            # V2: Pass important tokens to embedding function
            flat = flatten_for_embedding(can, query_tokens=important_tokens)
            token_matches = _count_token_matches(flat, important_tokens)
            candidates.append({
                "canonical": can,
                "flat": flat,
                "raw": rec,
                "important_token_matches": token_matches
            })
        except Exception:
            continue
    timings['canonical_count'] = len(candidates)
    timings['canonical_build'] = time.time() - t_can

    # dedupe deterministic
    t_du = time.time()
    seen = set(); dedup: List[Dict[str, Any]] = []
    for c in candidates:
        can = c['canonical']
        tag = can['node']['tag'] or ''
        text = (can['node']['text'] or '')[:200]
        direct_text = (can['node'].get('directText') or '')[:200]
        attrs_key = _safe_attrs_str(can['node'].get('attrs',{}), 200)
        # Ignore bbox in dedupe key to avoid duplicate 0x0 clones counting twice
        key = (
            tag,
            text,
            direct_text,
            attrs_key,
        )
        if key in seen:
            continue
        seen.add(key)
        dedup.append(c)
    timings['dedup_count'] = len(dedup)
    timings['dedupe_time'] = time.time() - t_du

    # cap candidates deterministically without heuristic preferences
    max_candidates = int(cfg['max_candidates'])
    if len(dedup) > max_candidates:
        dedup = dedup[:max_candidates]
        timings['capped_to'] = max_candidates

    # Post-filter: suppress container nodes
    if dedup and bool(cfg.get("suppress_container_matches", True)):
        container_tags = {"li", "ul", "ol", "div", "section", "nav", "header", "footer", "article", "main", "aside", "span"}
        preferred_tags = {"a", "button", "input", "select", "textarea", "summary", "label"}
        drop_indexes: set = set()
        node_outer_by_idx = {i: (c.get('raw', {}).get('node', {}) or {}).get('outerHTML', '') for i, c in enumerate(dedup)}
        ancestors_outer_sets: Dict[int, set] = {}
        for i, c in enumerate(dedup):
            anc_list = (c.get('raw', {}).get('ancestors') or [])
            ancestors_outer_sets[i] = { (a or {}).get('outerHTML','') for a in anc_list if isinstance(a, dict) }
        preferred_outers = { node_outer_by_idx.get(i) for i, c in enumerate(dedup)
                             if (c.get('canonical', {}).get('node', {}).get('tag') or '') in preferred_tags }
        preferred_outers.discard(None)
        for i, c in enumerate(dedup):
            tag_i = (c.get('canonical', {}).get('node', {}).get('tag') or '')
            if tag_i in preferred_tags:
                continue
            anc_outers_i = ancestors_outer_sets.get(i) or set()
            if any(p in anc_outers_i for p in preferred_outers):
                drop_indexes.add(i)
        if drop_indexes:
            dedup = [c for k, c in enumerate(dedup) if k not in drop_indexes]
            timings['postfilter_container_dropped'] = len(drop_indexes)

    if not dedup:
        result = {"best_index": None, "best_canonical": None, "best_canonical_str": None, "best_score": 0.0, "scores": [], "fallback_used": False, "fallback_info": None, "diagnostics": {"timings": timings, "num_candidates": 0, "top5": []}, "total_time_s": time.time()-overall_t0}
        if cfg.get("debug_dump_candidates"):
            print("[DEBUG] No candidates after processing.")
        return result

    # embeddings
    t_emb = time.time()
    model = _get_model(cfg)
    cand_texts = [d['flat'] for d in dedup]
    q_emb = model.encode([cleaned_query], convert_to_tensor=True)
    cand_emb = model.encode(cand_texts, convert_to_tensor=True)
    sims_tensor = util.cos_sim(q_emb, cand_emb)[0]
    sims = sims_tensor.detach().cpu().numpy()
    timings['embedding_time'] = time.time() - t_emb

    # V2: Enhanced scoring with reranking
    rerank_threshold = float(cfg.get("rerank_ambiguity_threshold", 0.05))
    order = list(np.argsort(-sims))
    
    if len(order) > 1:
        top_score = sims[order[0]]
        # Check if top candidates are ambiguous
        if (top_score - sims[order[1]]) < rerank_threshold:
            # Gather candidates for reranking
            rerank_candidates_indices = [idx for idx in order[:10] if sims[idx] >= (top_score - rerank_threshold)]
            
            if len(rerank_candidates_indices) > 1 and important_tokens:
                reranked_scores = []
                for idx in rerank_candidates_indices:
                    base_score = float(sims[idx])
                    token_bonus = dedup[idx].get("important_token_matches", 0) * 0.01  # Small boost per token
                    reranked_scores.append((idx, base_score + token_bonus))
                
                # Sort by the enhanced score
                reranked_scores.sort(key=lambda x: x[1], reverse=True)
                # Rebuild the final sorted order
                best_indices_reranked = [item[0] for item in reranked_scores]
                remaining_indices = [idx for idx in order if idx not in best_indices_reranked]
                order = best_indices_reranked + remaining_indices

    best_idx = int(order[0]) if order else -1
    best_score = float(sims[best_idx]) if best_idx != -1 else 0.0
    second_score = float(sims[order[1]]) if len(order) > 1 else 0.0

    top5_scores = [float(sims[i]) for i in order[:5]]

    diagnostics = {
        "timings": timings,
        "num_candidates": len(dedup),
        "top5": top5_scores,
        "best_score": best_score,
        "second_score": second_score,
    }

    if cfg.get("debug_dump_candidates"):
        dump_k = int(cfg.get("debug_dump_top_k") or 0)
        limit = dump_k if dump_k and dump_k > 0 else len(order)
        only_pref = bool(cfg.get("debug_dump_only_prefiltered", False))
        printed = 0
        print(f"[DEBUG] Dumping top {limit} candidates (of {len(order)})" + (" — only matches" if only_pref and needle else ""))
        for rank, idx in enumerate(order[:limit], start=1):
            c = dedup[idx]
            if only_pref and needle:
                node_text = (c['canonical']['node'].get('text') or '').lower()
                anc_texts = ' '.join([(a.get('text') or '') for a in (c.get('raw',{}).get('ancestors') or [])]).lower()
                if (needle not in node_text) and (needle not in anc_texts):
                    continue
            print("== Candidate #", rank, "==")
            try:
                print("embedding_string:")
                print(c['flat'])
            except Exception: pass
            try:
                print("canonical_json:")
                print(json.dumps(c['canonical'], indent=2))
            except Exception: pass
            print("similarity:", float(sims[idx]))
            print("important_token_matches:", c.get("important_token_matches", 0))
            print("----")
            printed += 1
        if only_pref and needle:
            print(f"[DEBUG] Printed {printed} candidates matching '{needle}'.")

    # fallback (strict gates per spec: low score or ambiguous top-2)
    use_visual_fallback = bool(cfg['use_visual_fallback'])
    similarity_threshold = float(cfg['similarity_threshold'])
    ambiguity_delta = float(cfg['ambiguity_delta'])
    fallback_used = False
    fallback_info: Optional[Dict[str, Any]] = None

    trigger_fallback = False
    if best_score < similarity_threshold:
        trigger_fallback = True
        fallback_reason = 'low_score'
    elif (best_score - second_score) < ambiguity_delta:
        trigger_fallback = True
        fallback_reason = 'ambiguous_top_two'
    else:
        fallback_reason = None

    if use_visual_fallback and trigger_fallback:
        t_fb = time.time()
        fallback_used = True
        ocr_matches = ocr_bboxes_from_screenshot(screenshot_b64, query, target_text)
        best_iou = 0.0
        best_idx_by_ocr: Optional[int] = None
        for (l,t,w,h,txt) in ocr_matches:
            for ci, d in enumerate(dedup):
                cb = d['canonical']['node']['bbox']
                iouv = _iou((l,t,w,h), (int(cb[0]), int(cb[1]), int(cb[2]), int(cb[3])))
                if iouv > best_iou:
                    best_iou = iouv; best_idx_by_ocr = ci
        iou_cutoff = float(cfg.get('ocr_iou_cutoff', 0.3))
        if best_idx_by_ocr is not None and best_iou >= iou_cutoff:
            best_idx = int(best_idx_by_ocr)
            best_score = float(sims[best_idx])
        fallback_info = {
            "reason": fallback_reason,
            "ocr_matches": ocr_matches[:20],
            "selected_by_ocr_iou": best_iou if best_iou >= iou_cutoff else None,
        }
        diagnostics['fallback_time'] = time.time() - t_fb

    return_k = int(cfg.get("return_top_k") or 0)
    ranked = [
        {
            "rank": int(i+1),
            "score": float(sims[j]),
            "canonical": dedup[j]['canonical'],
            "embedding_string": dedup[j]['flat'],
        }
        for i, j in enumerate(order)
    ]
    if return_k and return_k > 0:
        ranked = ranked[:return_k]

    top5_details = []
    for i, j in enumerate(order[:5]):
        cnode = dedup[j]['canonical']['node']
        top5_details.append({
            "rank": int(i+1),
            "score": float(sims[j]),
            "tag": cnode.get("tag"),
            "text": cnode.get("text"),
            "embedding_string": dedup[j]['flat'],
        })
    diagnostics.update({
        "gap": float(best_score - second_score),
        "top5_candidates": top5_details,
        "counts": {
            "extracted": int(timings.get("extracted_count", 0)),
            "prefiltered": int(timings.get("prefilter_count", 0)),
            "canonical": int(timings.get("canonical_count", 0)),
            "deduped": int(timings.get("dedup_count", 0)),
        },
        "total_time_s": float(time.time() - overall_t0),
        "best_summary": {
            "tag": dedup[best_idx]['canonical']['node'].get('tag'),
            "text": dedup[best_idx]['canonical']['node'].get('text'),
        } if best_idx != -1 else {}
    })

    result = {
        "best_index": best_idx if best_idx != -1 else None,
        "best_canonical": dedup[best_idx]['canonical'] if best_idx != -1 else None,
        "best_canonical_str": dedup[best_idx]['flat'] if best_idx != -1 else None,
        "best_score": best_score,
        "scores": [float(s) for s in sims.tolist()],
        "ranked": ranked,
        "fallback_used": fallback_used,
        "fallback_info": fallback_info,
        "diagnostics": diagnostics,
        "total_time_s": time.time() - overall_t0,
    }
    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="UI Element Locator using Gemma embeddings")
    parser.add_argument("--url", required=True, help="Page URL to load")
    parser.add_argument("--query", required=True, help="Natural language query")
    parser.add_argument("--text", dest="target_text", default="", help="Optional target text to prefilter, e.g. 'Apple'")
    parser.add_argument("--hf-token", dest="hf_token", default=os.environ.get("HUGGINGFACE_HUB_TOKEN", ""), help="Hugging Face token for Gemma model")
    parser.add_argument("--no-visual-fallback", action="store_true", help="Disable OCR/Pix2Struct visual fallback")
    parser.add_argument("--similarity-threshold", type=float, default=0.72)
    parser.add_argument("--ambiguity-delta", type=float, default=0.05)
    parser.add_argument("--ancestor-levels", type=int, default=2)
    parser.add_argument("--max-siblings", type=int, default=1)
    parser.add_argument("--include-hidden", action="store_true")
    parser.add_argument("--return-top-k", type=int, default=0, help="Return top K ranked candidates in output (0 = all)")
    parser.add_argument("--max-candidates", type=int, default=500, help="Maximum candidates to keep after dedupe (increase to print all matches)")
    parser.add_argument("--prefilter-mode", choices=["contains","equals","regex"], default="contains")
    parser.add_argument("--prefilter-scope", choices=["node","node_and_ancestors"], default="node_and_ancestors")
    parser.add_argument("--prefilter-direct-text-only", action="store_true", help="If set, prefilter uses node.directText instead of node.text")
    parser.add_argument("--debug", action="store_true", help="Print debug candidate dumps")
    parser.add_argument("--wait-until", choices=["load","domcontentloaded","networkidle","commit"], default="networkidle")
    parser.add_argument("--timeout-ms", type=int, default=60000)
    parser.add_argument("--whitelist-tags", dest="whitelist_tags", default="", help="Comma-separated list of HTML tags to include as candidates (lowercase), e.g. 'label,a'")

    args = parser.parse_args()

    cfg = {
        "ancestor_levels": int(args.ancestor_levels),
        "max_siblings": int(args.max_siblings),
        "include_hidden": bool(args.include_hidden),
        "similarity_threshold": float(args.similarity_threshold),
        "ambiguity_delta": float(args.ambiguity_delta),
        "use_visual_fallback": (not args.no_visual_fallback),
        "embedding_model_name": "google/embeddinggemma-300m",
        "allow_embedding_fallback": False,
        "hf_token": args.hf_token or os.environ.get("HUGGINGFACE_HUB_TOKEN"),
        "debug_dump_candidates": bool(args.debug),
        "debug_dump_only_prefiltered": True,
        "debug_dump_top_k": 0,
        "return_top_k": int(args.return_top_k or 0),
        "max_candidates": int(args.max_candidates or 500),
        "prefilter_match_mode": str(args.prefilter_mode),
        "prefilter_scope": str(args.prefilter_scope),
        "prefilter_direct_text_only": bool(args.prefilter_direct_text_only),
        "wait_until": str(args.wait_until),
        "timeout_ms": int(args.timeout_ms),
        "candidate_tag_whitelist": [t.strip().lower() for t in (args.whitelist_tags.split(",") if args.whitelist_tags else []) if t.strip()],
    }

    out = retrieve_best_element(args.url, args.query, target_text=(args.target_text or None), config=cfg)

    # Always print each matching candidate (those considered after prefilter/dedupe) with embedding string, canonical JSON, and score
    ranked = out.get("ranked") or []
    print("\n=== Matching candidates (after prefilter & dedupe) ===")
    for item in ranked:
        try:
            print(f"# Rank {item['rank']} | score={item['score']:.4f}")
            print("embedding_string:")
            print(item.get("embedding_string") or "")
            print("canonical_json:")
            print(json.dumps(item.get("canonical"), indent=2))
            print("----")
        except Exception:
            continue

    # Summary
    print("\n=== Summary ===")
    print(json.dumps({
        "best_index": out.get("best_index"),
        "best_score": out.get("best_score"),
        "best_tag": out.get("best_canonical", {}).get("node", {}).get("tag"),
        "best_text": out.get("best_canonical", {}).get("node", {}).get("text"),
        "fallback_used": out.get("fallback_used"),
        "gap": out.get("diagnostics", {}).get("gap"),
        "counts": out.get("diagnostics", {}).get("counts"),
        "timings": out.get("diagnostics", {}).get("timings"),
        "total_time_s": out.get("diagnostics", {}).get("total_time_s"),
    }, indent=2))
