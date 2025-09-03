from __future__ import annotations
from typing import Dict, Any, List, Optional
import numpy as np

from .browser.snapshot import snapshot_sync
from .embeddings.text_embedder import TextEmbedder
from .embeddings.markuplm_embedder import MarkupLMEmbedder
from .embeddings.normalization import element_to_text
from .hashing import element_dom_hash, frame_hash, page_signature
from .frames import FrameManager
from .db import VectorIndex
from .intent.parser import parse_intent
from .reranker import finalize_ranking
from .promotion import PromotionDB
from .executor import run_action

class HERAgent:
    """
    English → Intent → Snapshot/Deltas → Retrieval → Rerank → (Promotion) → Execute
    """

    def __init__(self, models_root: str = "src/her/models"):
        # Embedders (offline)
        self.text_emb = TextEmbedder(f"{models_root}/e5-small-onnx")
        self.elem_emb = MarkupLMEmbedder(f"{models_root}/markuplm-base")

        self.frames = FrameManager()
        self.promo = PromotionDB()
        self.active_url: Optional[str] = None

    # -------- data plane --------
    def _index_frame(self, frame_url: str, items: List[Dict[str, Any]]) -> str:
        fh = self.frames.ensure(frame_url, items)
        idx = self.frames.get_index(fh)
        # delta upsert
        idx.upsert(items, embedder=self.elem_emb)
        return fh

    def _snapshot_all(self, url: str, **opts) -> List[Dict]:
        items = snapshot_sync(url, **opts)
        return items

    # -------- control plane --------
    def run_step(self, url: str, query: str, topk: int = 10) -> Dict[str, Any]:
        """
        Main entrypoint: returns selectors / execution plan.
        """
        self.active_url = url
        intent = parse_intent(query)

        # Snapshot & per-frame indexing (group by frame_url)
        items = self._snapshot_all(url, include_iframes=True, include_shadow_dom=True, auto_scroll=True)
        by_frame = {}
        for it in items:
            furl = it.get("frame_url") or url
            by_frame.setdefault(furl, []).append(it)

        # Build/Update frame indexes
        for furl, els in by_frame.items():
            self._index_frame(furl, els)

        # --- Promotion fast path ---
        promo = self.promo.get(url, self.frames.active or "", intent.label_tokens or [])
        if promo:
            return {
                "action": intent.action,
                "selector": promo.primary_selector,
                "alternates": promo.alternates,
                "source": "promotion",
                "confidence": 0.95,
            }

        # --- Retrieval: text → shortlist per frame ---
        q = self.text_emb.batch_encode([intent.target])[0]
        # search in active frame first
        try:
            idx_active = self.frames.get_index()
            cand = idx_active.search(q, topk)
        except Exception:
            cand = []

        # if not enough candidates, widen to all frames
        if len(cand) < max(3, topk//2):
            cand = self.frames.search_all_frames(q, topk=topk*2)

        # --- Rerank (hybrid bonuses & tie-breakers) ---
        ranked = finalize_ranking(cand, intent)

        if not ranked:
            return {"error": "ElementNotFound", "message": "No matching elements", "intent": intent.__dict__}

        # Build final answer
        best = ranked[0]
        meta = best["meta"]
        selector = meta.get("xpath") or ""  # prefer XPath from snapshot
        out = {
            "action": intent.action,
            "selector": selector,
            "frame_hash": frame_hash(meta.get("frame_url") or url, [meta]),
            "score": best["score"],
            "confidence": float(min(1.0, max(0.0, best["score"]))),
            "reason": "hybrid rerank",
            "alternates": [r["meta"].get("xpath") for r in ranked[1:4] if r["meta"].get("xpath")],
            "intent": intent.__dict__,
        }

        # store promotion (light)
        self.promo.put(url, out["frame_hash"], intent.label_tokens or [], selector, out["alternates"])
        return out

    def execute(self, url: str, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Run the action using Playwright."""
        if "selector" not in plan:
            return {"error": "NoSelector", "message": "Nothing to execute."}
        frame_hint = plan.get("frame_hash")  # we pass URL substring to match frame; minimal
        try:
            run_action(url, plan["action"], plan["selector"], value=plan["intent"].get("value"), frame_url_hint=None)
            return {"ok": True, "executed": plan}
        except Exception as e:
            return {"ok": False, "error": type(e).__name__, "message": str(e), "plan": plan}
