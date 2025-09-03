"""
High-level natural-language action executor for the Hybrid Element
Retriever (HER) framework.

The `HerAgent` class coordinates the major components of HER to
provide a single entry point for turning plain-English commands into
robust element selectors, optional interactions, and promotion of
successful selectors.  It maintains per-frame DOM hashes and
incrementally updates an in-memory vector index to avoid
re-embedding unchanged elements.  The agent performs a two-stage
retrieval (intent shortlist via MiniLM followed by hybrid scoring
with MarkupLM and heuristic bonuses) and returns the best
matching element along with the selector, confidence and reasons.

This module can be used both in offline mode (without a Playwright
browser) and in online mode where a Playwright `page` is supplied.
In offline mode, the agent will still return a ranked selector but
will skip interaction and promotion.  When a page is provided and
Playwright is installed, the agent will verify and optionally click
the element, then record the outcome for self-healing.

Example usage:

    from her.runtime.agent import HerAgent
    from her.pipeline import HybridPipeline

    pipeline = HybridPipeline(models_root="/path/to/models")
    agent = HerAgent(pipeline=pipeline)

    # Without a page (offline ranking)
    pick = agent.run_step(page=None, step="click login button", elements=some_element_list)
    print(pick.selector, pick.confidence)

    # With Playwright page
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("https://example.com")
        pick = agent.run_step(page, "click login button")
        # pick.selector is the chosen XPath/CSS
        browser.close()

The agent stores promotion data (successful selectors) in a
`PromotionStore` so that repeated actions can bypass retrieval
entirely.  See the `SelfHealer` class for details.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from ..pipeline import HybridPipeline
from ..recovery.promotion import PromotionStore
from ..recovery.self_heal import SelfHealer, VerifyResult
from ..utils.context import make_context_key

try:
    from playwright.sync_api import Page, Frame  # type: ignore
    from playwright.sync_api import TimeoutError as PWTimeout  # type: ignore
    PLAYWRIGHT_AVAILABLE = True
except Exception:  # pragma: no cover
    Page = Any  # type: ignore
    Frame = Any  # type: ignore
    class PWTimeout(Exception):  # type: ignore
        pass
    PLAYWRIGHT_AVAILABLE = False

log = logging.getLogger(__name__)


def _sha1(s: str) -> str:
    """Compute a SHA-1 digest of the input string as a hex digest."""
    return hashlib.sha1(s.encode("utf-8", errors="ignore")).hexdigest()


def _normalize_space(s: str) -> str:
    """Collapse all whitespace to single spaces and strip ends."""
    return re.sub(r"\s+", " ", (s or "").strip())


def _abs_xpath_for(el) -> str:
    """
    Compute an absolute XPath for a Playwright element.  When run in the
    browser context, this walks up the DOM and builds a stable path.
    If Playwright is not available or the element does not support
    evaluation, this returns an empty string.
    """
    try:
        return el.evaluate(
            """(node) => {
                function idx(n){let i=1;for(let k=n;k.previousSibling;k=k.previousSibling){if(k.nodeName===n.nodeName) i++}return i}
                function xp(n){if(!n||!n.tagName)return '';const tag=n.tagName.toLowerCase();const i=idx(n);const seg=`/${tag}[${i}]`;return n.parentElement? xp(n.parentElement)+seg : seg;}
                return xp(node);
            }"""
        )
    except Exception:
        return ""


def _bbox_of(el) -> Dict[str, float]:
    """Return the bounding-box (width/height) for a Playwright element."""
    try:
        box = el.bounding_box()
        if box is None:
            return {"width": 0.0, "height": 0.0}
        return {"width": float(box["width"]), "height": float(box["height"])}
    except Exception:
        return {"width": 0.0, "height": 0.0}


def _collect_clickables(frame: Frame) -> List[Dict[str, Any]]:
    """
    Collect visible elements that could be candidates for user interactions.
    This restricts to links, buttons, and other roles that are typically
    actionable.  Only elements with visible text or a href are kept.
    """
    # Provide generous limit per frame to avoid blowing up memory
    locator = frame.locator("a, button, [role='link'], [role='button'], input[type=submit], [tabindex]")
    count = min(locator.count(), 800)
    out: List[Dict[str, Any]] = []
    for i in range(count):
        el = locator.nth(i)
        try:
            if not el.is_visible():
                continue
        except Exception:
            continue
        try:
            tag = el.evaluate("n => n.tagName.toLowerCase()")  # type: ignore
        except Exception:
            tag = ""
        try:
            role = (el.get_attribute("role") or "").lower()  # type: ignore
        except Exception:
            role = ""
        href = ""
        if tag == "a":
            try:
                href = el.get_attribute("href") or ""
            except Exception:
                href = ""
        try:
            text = _normalize_space(el.inner_text())  # type: ignore
        except Exception:
            text = ""
        if not text and not href:
            continue
        out.append({
            "tag": tag,
            "role": role,
            "href": href,
            "visible": True,
            "bbox": _bbox_of(el),
            "xpath": _abs_xpath_for(el),
            "text": text,
        })
    return out


def _all_frames(page: Page) -> List[Frame]:
    """Return all frames in the page (including main)."""
    try:
        return list(page.frames)
    except Exception:
        return []


@dataclass
class RankedPick:
    """Result returned by HerAgent.run_step: best selector and metadata."""
    selector: str
    strategy: str
    confidence: float
    reason: str
    element: Dict[str, Any]


class _DeltaIndex:
    """
    Simple in-memory index for per-frame element vectors.  It stores
    element dicts keyed by a stable hash and associated vectors.  The
    index supports incremental updates: new elements or changed ones
    replace existing entries, while unchanged entries are left
    untouched.  This allows us to merge embeddings across multiple
    snapshots without re-embedding the entire page.
    """
    def __init__(self, dim: int) -> None:
        self.dim = int(dim)
        self._elts: Dict[str, Dict[str, Any]] = {}
        self._vecs: Dict[str, np.ndarray] = {}

    @staticmethod
    def key_of(el: Dict[str, Any]) -> str:
        mat = "|".join([
            (el.get("tag") or "").lower(),
            (el.get("role") or "").lower(),
            _normalize_space(el.get("text") or ""),
            (el.get("href") or ""),
            el.get("xpath") or "",
        ])
        return _sha1(mat)

    def upsert(self, elements: List[Dict[str, Any]], vecs: np.ndarray) -> Tuple[int, int]:
        added = 0
        updated = 0
        for i, el in enumerate(elements):
            k = self.key_of(el)
            v = vecs[i].astype(np.float32, copy=False)
            if k in self._elts:
                self._elts[k] = el
                self._vecs[k] = v
                updated += 1
            else:
                self._elts[k] = el
                self._vecs[k] = v
                added += 1
        return added, updated

    def ids(self) -> List[str]:
        return list(self._elts.keys())

    def elements(self) -> List[Dict[str, Any]]:
        return [self._elts[k] for k in self.ids()]

    def vectors(self) -> np.ndarray:
        if not self._vecs:
            return np.zeros((0, self.dim), dtype=np.float32)
        mat = np.vstack([self._vecs[k] for k in self.ids()]).astype(np.float32, copy=False)
        # If shapes mismatch, pad/truncate to expected dim
        if mat.ndim != 2 or mat.shape[1] != self.dim:
            fixed = np.zeros((mat.shape[0], self.dim), dtype=np.float32)
            k = min(self.dim, mat.shape[1] if mat.ndim == 2 else self.dim)
            if k:
                fixed[:, :k] = mat[:, :k]
            return fixed
        return mat


class HerAgent:
    """
    Orchestrator for HER.  Maintains per-frame delta indexes, performs
    intent parsing and ranking, runs optional interactions, and
    integrates with the self-healing promotion cache.  Use
    `run_step()` to handle a natural-language step.
    """
    def __init__(
        self,
        pipeline: Optional[HybridPipeline] = None,
        models_root: Optional[str] = None,
        promotions_db: Optional[str] = None,
        cache_hit_confidence_boost: float = 0.05,
    ) -> None:
        # Use provided pipeline or create a new one
        self.pipeline: HybridPipeline = pipeline or HybridPipeline(models_root=None if models_root is None else models_root)
        self._text_dim = self.pipeline._text_dim()
        self._elem_dim = self.pipeline._elem_dim()
        # Per-frame DOM hashes
        self._frame_hash: Dict[str, str] = {}
        # Per-frame vector indexes
        self._frame_index: Dict[str, _DeltaIndex] = {}
        # Promotion store
        store = PromotionStore(
            path=None if promotions_db is None else promotions_db,
            use_sqlite=promotions_db is not None,
        )
        self.healer = SelfHealer(
            store=store,
            verify_fn=self._verify_stub,
            require_unique=True,
            max_candidates=3,
            min_score=0.0,
            cache_hit_confidence_boost=cache_hit_confidence_boost,
        )

    # ---------- verification callback ----------
    def _verify_stub(self, page: Optional[Page], selector: str, *, strategy: str, require_unique: bool = True) -> VerifyResult:
        """
        Verify that a selector points to a visible (and optionally unique) element on the page.  In offline mode (no page
        or Playwright unavailable), this always returns ok.  For online mode, this uses Playwright to check visibility and
        uniqueness.  Errors are treated as failures.
        """
        if not PLAYWRIGHT_AVAILABLE or page is None:
            return VerifyResult(ok=True, unique=True)
        try:
            loc = page.locator(f"{strategy}={selector}") if strategy in ("xpath", "css") else page.locator(selector)
            # Check visibility
            visible = loc.first.is_visible(timeout=1500)
            if not visible:
                return VerifyResult(ok=False, unique=False)
            if require_unique:
                count = loc.count()
                return VerifyResult(ok=(count == 1), unique=(count == 1))
            return VerifyResult(ok=True, unique=True)
        except Exception:
            return VerifyResult(ok=False, unique=False)

    # ---------- index maintenance ----------
    def _page_dom_hash(self, frame: Frame) -> str:
        """Compute a SHA-1 hash of the frame's HTML content."""
        try:
            html = frame.content()
        except Exception:
            html = ""
        return _sha1(html)

    def _ensure_index_for(self, frame_id: str) -> _DeltaIndex:
        if frame_id not in self._frame_index:
            self._frame_index[frame_id] = _DeltaIndex(dim=self._elem_dim)
        return self._frame_index[frame_id]

    def _refresh_frame_index(self, frame: Frame) -> Tuple[int, int, bool]:
        """
        Check if a frame's DOM has changed by hashing its HTML.  If it has
        changed, recollect clickables and embed them.  Returns (added,
        updated, changed) and a boolean flag indicating whether the
        frame hash changed.
        """
        fid = frame.url or f"frame:{id(frame)}"
        new_hash = self._page_dom_hash(frame)
        old_hash = self._frame_hash.get(fid)
        changed = (new_hash != old_hash)
        if not changed:
            return (0, 0, False)
        elements = _collect_clickables(frame)
        E = self.pipeline.embed_elements(elements)
        idx = self._ensure_index_for(fid)
        added, updated = idx.upsert(elements, E)
        self._frame_hash[fid] = new_hash
        return (added, updated, True)

    def _ensure_all_indexes(self, page: Page) -> None:
        if not PLAYWRIGHT_AVAILABLE or page is None:
            return
        for fr in _all_frames(page):
            self._refresh_frame_index(fr)

    # ---------- selection helpers ----------
    @staticmethod
    def _best_selector_for(el: Dict[str, Any]) -> Tuple[str, str]:
        """
        Choose a selector for the element.  Prefers xpath if present.  If
        no xpath, tries to derive a CSS selector based on href or text.
        """
        xp = el.get("xpath") or ""
        if xp:
            return ("xpath", xp)
        href = el.get("href") or ""
        txt = _normalize_space(el.get("text") or "")
        if href:
            base = href.split("?")[0].split("#")[0]
            return ("css", f"a[href*='{base}']")
        if txt:
            safe = re.escape(txt[:80])
            return ("css", f":is(a,button,[role='button'],[role='link']):has-text('{safe}')")
        return ("css", ":is(a,button,[role='button'],[role='link'])")

    # ---------- main entry ----------
    def run_step(
        self,
        page: Optional[Page],
        step: str,
        *,
        url: Optional[str] = None,
        dom_hash_hint: Optional[str] = None,
        click: bool = False,
        shortlist_k: int = 12,
        top_k: int = 5,
        extra_context: Optional[Dict[str, Any]] = None,
        elements: Optional[List[Dict[str, Any]]] = None,
    ) -> RankedPick:
        """
        Execute a natural-language step.  If a Playwright page is
        provided, the agent updates its per-frame index by hashing and
        re-embedding only changed frames.  If a list of element
        dictionaries is provided, the agent uses those elements instead
        (useful for offline or custom snapshots).  The agent first
        consults the self-heal cache and returns a cached selector if
        available.  Otherwise it performs a two-stage retrieval: intent
        shortlist via cosine similarity and deep hybrid re-ranking.

        Args:
            page: Playwright page or None.  If None, `elements` must be
                provided.
            step: The user command, e.g. "click login button".
            url: Optional explicit URL to use when generating context
                keys for promotion.  If not provided, uses page.url.
            dom_hash_hint: Optional DOM hash for context.  Useful when
                calling offline to disambiguate sessions.
            click: If True and a page is provided, the agent will
                attempt to click the selected element and record the
                result in the promotion DB.
            shortlist_k: Number of top candidates from the intent
                shortlist to send to the deep ranking phase.
            top_k: Number of results to return from the deep ranking
                phase (only the first is used for selection).
            extra_context: Additional context for promotion cache keys.
            elements: Optional list of element dicts to rank
                (alternative to providing a Playwright page).  Each
                element must contain fields recognized by the
                HybridPipeline (tag, role, href, visible, bbox, xpath,
                text).

        Returns:
            RankedPick: Contains the best selector, strategy, confidence,
                explanation and element metadata.  If click=True and the
                page is available, the element will be clicked and the
                promotion cache updated.
        """

        # 0) Self-heal: check promotion DB for a cached selector
        ctx_url = url or (page.url if (PLAYWRIGHT_AVAILABLE and page is not None) else "")
        heal_res = self.healer.try_cached(
            page=page,
            query=step,
            context_url=ctx_url,
            dom_hash=dom_hash_hint,
            extra_context=extra_context,
        )
        if heal_res.ok and heal_res.strategy and heal_res.selector:
            sel = f"{heal_res.strategy}={heal_res.selector}" if heal_res.strategy in ("xpath", "css") else heal_res.selector
            return RankedPick(
                selector=sel,
                strategy=heal_res.strategy,
                confidence=min(1.0, 0.85 + heal_res.confidence_boost),
                reason="cache-hit",
                element={"selector": sel},
            )

        # 1) Build the pool of candidate elements
        elements_pool: List[Dict[str, Any]] = []
        if elements is not None and elements:
            # Use provided elements (offline mode)
            elements_pool = elements
        elif PLAYWRIGHT_AVAILABLE and page is not None:
            # Refresh per-frame indexes (delta embedding)
            self._ensure_all_indexes(page)
            # Flatten all frames' elements into a single list
            for idx in self._frame_index.values():
                elements_pool.extend(idx.elements())
        else:
            # No elements to rank
            return RankedPick(selector="", strategy="css", confidence=0.0, reason="no-elements", element={})

        if not elements_pool:
            return RankedPick(selector="", strategy="css", confidence=0.0, reason="no-elements", element={})

        # 2) Intent shortlist: embed query and compute cosine similarity
        q_vec = self.pipeline.embed_query(step)
        all_vecs = None
        if elements is not None and elements:
            all_vecs = self.pipeline.embed_elements(elements_pool)
        else:
            # When using delta index, gather vectors from all indexes
            mats = []
            for idx in self._frame_index.values():
                vec = idx.vectors()
                if vec.size:
                    mats.append(vec)
            all_vecs = np.vstack(mats) if mats else np.zeros((0, self._elem_dim), dtype=np.float32)

        if all_vecs.size == 0:
            return RankedPick(selector="", strategy="css", confidence=0.0, reason="no-vectors", element={})
        # Compute cosine for all elements
        base_scores = np.array([
            0.0 if (np.linalg.norm(q_vec) == 0.0 or np.linalg.norm(all_vecs[i]) == 0.0) else float(np.dot(q_vec[:min(len(q_vec), len(all_vecs[i]))], all_vecs[i][:min(len(q_vec), len(all_vecs[i]))]) / (np.linalg.norm(q_vec) * np.linalg.norm(all_vecs[i])))
            for i in range(all_vecs.shape[0])
        ], dtype=np.float32)
        # Pick top-N by cosine
        shortlist_indices = list(np.argsort(-base_scores))[: max(1, shortlist_k)]
        shortlist = [elements_pool[int(i)] for i in shortlist_indices]

        # 3) Deep re-rank using HybridPipeline (with bonuses/tie-breakers)
        rerank = self.pipeline.query(step, shortlist, top_k=max(1, top_k))
        if not rerank.get("results"):
            return RankedPick(selector="", strategy="css", confidence=0.0, reason="no-results", element={})
        best_el = rerank["results"][0]["element"]
        reason = rerank["results"][0].get("reason", "hybrid")
        confidence = float(rerank.get("confidence", 0.0))
        strategy, selector = self._best_selector_for(best_el)

        # 4) Verification and optional click
        if PLAYWRIGHT_AVAILABLE and page is not None:
            try:
                loc = page.locator(f"{strategy}={selector}") if strategy in ("xpath", "css") else page.locator(selector)
                if loc.first.is_visible(timeout=2500):
                    if click:
                        # attempt click
                        loc.first.click(timeout=8000)
                        try:
                            page.wait_for_load_state("networkidle", timeout=6000)
                        except Exception:
                            pass
                        # record success in promotion store
                        self.healer.record_success(context_url=ctx_url, selector=f"{strategy}={selector}")
                else:
                    self.healer.record_failure(context_url=ctx_url, selector=f"{strategy}={selector}")
            except Exception:
                self.healer.record_failure(context_url=ctx_url, selector=f"{strategy}={selector}")

        return RankedPick(
            selector=f"{strategy}={selector}",
            strategy=strategy,
            confidence=confidence,
            reason=reason,
            element=best_el,
        )
