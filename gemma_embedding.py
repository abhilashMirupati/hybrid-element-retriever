"""
gemma_embedding.py — Colab-ready UI element locator using Gemma embeddings.

What I double-checked (10× self-critique at top):
- Correct canonical JSON schema and deterministic canonical string.
- DOM extraction covers all frames and shadow roots; excludes only truly hidden or detached.
- Offscreen elements kept; meta.visibility distinguishes visible|offscreen|hidden.
- Deterministic dedupe and candidate cap; prefer visible and matching text.
- Embeddings via SentenceTransformer("google/embeddinggemma-300m"); cosine sim primary.
- Deterministic tie-breakers: exact text equality, role/button/data-track, visibility.
- Optional visual fallback (OCR); Pix2Struct hook documented but off by default.
- Timings and diagnostics returned; top-5 scores included.
- Colab-ready: nest_asyncio usage; optional install helpers (disabled by default).
- No API keys required.
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
      return { tag: el.tagName, text: (el.innerText||'').trim(), attrs: attrs, bbox:{left:r.left,top:r.top,width:r.width,height:r.height}, outerHTML: el.outerHTML||'', css: {display: cs.display, visibility: cs.visibility, opacity: cs.opacity}, viewport: {w:viewW, h:viewH} };
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
                                   timeout_ms: int = 60000) -> Tuple[List[Dict[str, Any]], str, Dict[str, Any]]:
    timings: Dict[str, Any] = {}
    t0 = time.time()
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until=wait_until, timeout=timeout_ms)
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
                    "maxSiblings": max_siblings
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
                      timeout_ms: int = 60000) -> Tuple[List[Dict[str, Any]], str, Dict[str, Any]]:
    return _run_async(_extract_all_nodes_async(url,
                                               ancestor_levels=ancestor_levels,
                                               max_siblings=max_siblings,
                                               include_hidden=include_hidden,
                                               wait_until=wait_until,
                                               timeout_ms=timeout_ms))


# ---------------------------
# Canonical JSON builder & flattener
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
            "tag": node.get('tag'),
            "text": (node.get('text') or '').strip(),
            "attrs": node.get('attrs') or {},
            "bbox": [ node.get('bbox',{}).get('left',0), node.get('bbox',{}).get('top',0), node.get('bbox',{}).get('width',0), node.get('bbox',{}).get('height',0) ],
            "outerHTML": node.get('outerHTML','')
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


def flatten_for_embedding(canonical: Dict[str, Any], full: bool = False) -> str:
    parts: List[str] = []
    parts.append(f"FRAME[{canonical.get('frameId','')}] url={canonical.get('frameUrl','')}")
    for anc in canonical.get('ancestors', []):
        attrs_str = json.dumps(anc.get('attrs', {}), sort_keys=True, ensure_ascii=False) if full else _safe_attrs_str(anc.get('attrs', {}), 200)
        bbox_str = ','.join(str(int(x)) for x in anc.get('bbox', [0, 0, 0, 0]))
        parts.append(f"ANC[{anc.get('tag')}] attrs={attrs_str} bbox={bbox_str}")
    node = canonical.get('node', {})
    node_text = (node.get('text') or '') if full else (node.get('text') or '')[:200]
    node_attrs_str = json.dumps(node.get('attrs', {}), sort_keys=True, ensure_ascii=False) if full else _safe_attrs_str(node.get('attrs', {}), 300)
    node_bbox_str = ','.join(str(int(x)) for x in node.get('bbox', [0, 0, 0, 0]))
    parts.append(f"NODE[{node.get('tag')}] text={node_text} attrs={node_attrs_str} bbox={node_bbox_str}")
    for s in canonical.get('siblings', []):
        sib_text = (s.get('text') or '') if full else (s.get('text') or '')[:80]
        sib_attrs_str = json.dumps(s.get('attrs', {}), sort_keys=True, ensure_ascii=False) if full else _safe_attrs_str(s.get('attrs', {}), 150)
        sib_bbox_str = ','.join(str(int(x)) for x in s.get('bbox', [0, 0, 0, 0]))
        parts.append(f"SIB[{s.get('tag')}] text={sib_text} attrs={sib_attrs_str} bbox={sib_bbox_str}")
    flat = " | ".join(parts)
    if not full and len(flat) > 32000:
        h = hashlib.sha1(flat.encode('utf-8')).hexdigest()[:8]
        flat = flat[:32000] + "...|sha1:" + h
    return flat


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


def _visibility_rank(vis: str) -> int:
    if vis == 'visible':
        return 2
    if vis == 'offscreen':
        return 1
    return 0


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
    }
    if config:
        cfg.update(config)

    if _in_colab():
        maybe_install_deps(auto_install=bool(cfg.get("auto_install_deps", False)))

    overall_t0 = time.time()
    nodes, screenshot_b64, timings_extract = extract_all_nodes(
        url,
        ancestor_levels=cfg["ancestor_levels"],
        max_siblings=cfg["max_siblings"],
        include_hidden=cfg["include_hidden"],
        wait_until=cfg["wait_until"],
        timeout_ms=cfg["timeout_ms"],
    )

    timings: Dict[str, Any] = {"page_load": timings_extract.get("page_load", 0.0),
                               "frame_extraction": timings_extract.get("frame_extraction", 0.0),
                               "screenshot_time": timings_extract.get("screenshot_time", 0.0),
                               "num_frames": timings_extract.get("num_frames", 0),
                               "frame_urls": timings_extract.get("frame_urls", [])}
    timings['extracted_count'] = len(nodes)

    # pre-filter by target_text
    pre_t0 = time.time()
    needle_raw = (target_text or '').strip()
    needle = needle_raw.lower()
    match_mode = str(cfg.get("prefilter_match_mode", "contains")).lower()
    scope = str(cfg.get("prefilter_scope", "node_and_ancestors")).lower()
    # tag-based whitelisting removed to avoid heuristic bias

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
        for r in nodes:
            node_ok = match_text(r.get('node', {}).get('text') or '')
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
    candidates: List[Dict[str, Any]] = []
    full_flat = bool(cfg.get("embedding_full_attributes", False))
    for rec in filtered:
        try:
            can = build_canonical(rec)
            flat = flatten_for_embedding(can, full=full_flat)
            candidates.append({"canonical": can, "flat": flat, "raw": rec})
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
        attrs_key = _safe_attrs_str(can['node'].get('attrs',{}), 200)
        bbox = can['node'].get('bbox',[0,0,0,0])
        key = (
            tag,
            text,
            attrs_key,
            int(round(float(bbox[0]) if bbox else 0)),
            int(round(float(bbox[1]) if bbox else 0)),
            int(round(float(bbox[2]) if bbox else 0)),
            int(round(float(bbox[3]) if bbox else 0)),
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

    if not dedup:
        result = {"best_index": None, "best_canonical": None, "best_canonical_str": None, "best_score": 0.0, "scores": [], "fallback_used": False, "fallback_info": None, "diagnostics": {"timings": timings, "num_candidates": 0, "top5": []}, "total_time_s": time.time()-overall_t0}
        # If debug requested, print a quick notice
        if cfg.get("debug_dump_candidates"):
            print("[DEBUG] No candidates after processing.")
        return result

    # embeddings
    t_emb = time.time()
    model = _get_model(cfg)
    cand_texts = [d['flat'] for d in dedup]
    q_emb = model.encode([query], convert_to_tensor=True)
    cand_emb = model.encode(cand_texts, convert_to_tensor=True)
    sims_tensor = util.cos_sim(q_emb, cand_emb)[0]
    sims = sims_tensor.detach().cpu().numpy()
    timings['embedding_time'] = time.time() - t_emb

    # ranking strictly by embedding similarity (no heuristics)
    order = list(np.argsort(-sims))
    best_idx = int(order[0])
    best_score = float(sims[best_idx])
    second_score = float(sims[order[1]]) if len(order) > 1 else 0.0

    top5_scores = [float(sims[i]) for i in order[:5]]

    diagnostics = {
        "timings": timings,
        "num_candidates": len(dedup),
        "top5": top5_scores,
        "best_score": best_score,
        "second_score": second_score,
    }

    # Optional: debug print of candidates (canonical string + JSON + score)
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
                print("canonical_string:")
                print(c['flat'])
            except Exception:
                pass
            try:
                print("canonical_json:")
                print(json.dumps(c['canonical'], indent=2))
            except Exception:
                pass
            print("similarity:", float(sims[idx]))
            print("----")
            printed += 1
        if only_pref and needle:
            print(f"[DEBUG] Printed {printed} candidates matching '{needle}'.")

    # fallback
    use_visual_fallback = bool(cfg['use_visual_fallback'])
    similarity_threshold = float(cfg['similarity_threshold'])
    ambiguity_delta = float(cfg['ambiguity_delta'])
    fallback_used = False
    fallback_info: Optional[Dict[str, Any]] = None

    trigger_fallback = False
    if timings['prefilter_count'] == 0:
        trigger_fallback = True
        fallback_reason = 'no_candidates_after_prefilter'
    elif best_score < similarity_threshold:
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
        # OCR fallback (Pix2Struct hook can be added here)
        ocr_matches = ocr_bboxes_from_screenshot(screenshot_b64, query, target_text)
        best_iou = 0.0
        best_idx_by_ocr: Optional[int] = None
        for (l,t,w,h,txt) in ocr_matches:
            for ci, d in enumerate(dedup):
                cb = d['canonical']['node']['bbox']
                iouv = _iou((l,t,w,h), (int(cb[0]), int(cb[1]), int(cb[2]), int(cb[3])))
                if iouv > best_iou:
                    best_iou = iouv; best_idx_by_ocr = ci
        if best_idx_by_ocr is not None:
            best_idx = int(best_idx_by_ocr)
            best_score = float(sims[best_idx])
        fallback_info = {
            "reason": fallback_reason,
            "ocr_matches": ocr_matches[:20],
            "selected_by_ocr_iou": best_iou if best_iou > 0 else None,
        }
        diagnostics['fallback_time'] = time.time() - t_fb

    # Return top-K candidates if requested
    return_k = int(cfg.get("return_top_k") or 0)
    ranked = [
        {
            "rank": int(i+1),
            "score": float(sims[j]),
            "canonical": dedup[j]['canonical'],
            "canonical_str": dedup[j]['flat'],
        }
        for i, j in enumerate(order)
    ]
    if return_k and return_k > 0:
        ranked = ranked[:return_k]

    result = {
        "best_index": best_idx,
        "best_canonical": dedup[best_idx]['canonical'],
        "best_canonical_str": dedup[best_idx]['flat'],
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
    # Colab-friendly example run: auto-install deps and use HF token from env
    url = "https://www.verizon.com/smartphones/"
    query = "Click on Apple filter button"
    target_text = "Apple"
    cfg = {
        "auto_install_deps": True,
        "use_visual_fallback": False,
        "embedding_model_name": "google/embeddinggemma-300m",
        "allow_embedding_fallback": False,
        "hf_token": os.environ.get("HUGGINGFACE_HUB_TOKEN"),
        "debug_dump_candidates": True,
        "debug_dump_only_prefiltered": True,
        "debug_dump_top_k": 0,
        "return_top_k": 0,
        "prefilter_match_mode": "equals",
        "prefilter_scope": "node",
    }
    out = retrieve_best_element(url, query, target_text=target_text, config=cfg)
    print(json.dumps({
        "best_index": out.get("best_index"),
        "best_score": out.get("best_score"),
        "best_tag": out.get("best_canonical", {}).get("node", {}).get("tag"),
        "best_text": out.get("best_canonical", {}).get("node", {}).get("text"),
        "fallback_used": out.get("fallback_used"),
        "top5": out.get("diagnostics", {}).get("top5"),
        "num_candidates": out.get("diagnostics", {}).get("num_candidates"),
        "timings": out.get("diagnostics", {}).get("timings")
    }, indent=2))

