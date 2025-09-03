from __future__ import annotations
import time
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from ..utils.context import make_context_key
from .promotion import PromotionStore, PromotionRecord

log = logging.getLogger(__name__)


@dataclass
class VerifyResult:
    """Minimal verify contract (kept inline for decoupling)."""
    ok: bool
    unique: bool = True


@dataclass
class SelfHealResult:
    ok: bool
    strategy: Optional[str] = None
    selector: Optional[str] = None
    reason: str = ""
    verification: Optional[Dict[str, Any]] = None
    used_context: Optional[str] = None
    confidence_boost: float = 0.0


class SelfHealer:
    """
    Self-healing flow:
      1) Build context key (url + optional dom hash + extra_context)
      2) Pull top promoted selectors for that context (TTL/decay filtered)
      3) Verify in rank order; on success -> promote & return (cache-hit)
      4) On failure -> slight demotion; continue
      5) Callers can then proceed with live ranking/generation
    """

    def __init__(
        self,
        store: PromotionStore,
        verify_fn: Any,  # callable(page, selector, *, strategy, require_unique) -> VerifyResult
        require_unique: bool = True,
        max_candidates: int = 3,
        min_score: float = 0.0,
        cache_hit_confidence_boost: float = 0.05,
    ) -> None:
        self.store = store
        self.verify_fn = verify_fn
        self.require_unique = require_unique
        self.max_candidates = int(max_candidates)
        self.min_score = float(min_score)
        self.cache_hit_confidence_boost = float(cache_hit_confidence_boost)

    @staticmethod
    def split_locator(locator: str) -> Tuple[str, str]:
        """Return (strategy, selector) from 'css=...'/'xpath=...' or raw."""
        if locator.startswith("css="):
            return "css", locator[4:]
        if locator.startswith("xpath="):
            return "xpath", locator[6:]
        # Heuristic: XPath if starts with // or /(…
        if locator.startswith("//") or locator.startswith("(/"):
            return "xpath", locator
        return "css", locator

    def try_cached(
        self,
        page: Any,
        query: str,
        context_url: str,
        dom_hash: Optional[str] = None,
        extra_context: Optional[Dict[str, Any]] = None,
    ) -> SelfHealResult:
        ctx = make_context_key(context_url, dom_hash, extra_context)
        now = time.time()

        candidates = self.store.top_for_context(
            context=ctx,
            limit=self.max_candidates,
            min_score=self.min_score,
            now=now,
        )
        if not candidates:
            return SelfHealResult(ok=False, reason="no-cached-candidates", used_context=ctx)

        for rec in candidates:
            strategy, selector = SelfHealer.split_locator(rec.locator)
            try:
                v = self.verify_fn(page, selector, strategy=strategy, require_unique=self.require_unique)
            except Exception as e:
                log.debug("verify_fn error for %s (%s): %s", rec.locator, strategy, e)
                v = None

            ok = bool(getattr(v, "ok", False))
            unique_ok = True if not self.require_unique else bool(getattr(v, "unique", False))

            if ok and unique_ok:
                self.store.record_success(locator=rec.locator, context=ctx, boost=0.10)
                return SelfHealResult(
                    ok=True,
                    strategy=strategy,
                    selector=selector,
                    reason="cache-hit",
                    verification=getattr(v, "__dict__", None),
                    used_context=ctx,
                    confidence_boost=self.cache_hit_confidence_boost,
                )

            # demote a little and continue
            self.store.record_failure(locator=rec.locator, context=ctx, penalty=0.05)

        return SelfHealResult(ok=False, reason="candidates-failed", used_context=ctx)

    def record_success(
        self,
        context_url: str,
        selector: str,
        dom_hash: Optional[str] = None,
        extra_context: Optional[Dict[str, Any]] = None,
        boost: float = 0.10,
    ) -> PromotionRecord:
        ctx = make_context_key(context_url, dom_hash, extra_context)
        return self.store.record_success(locator=selector, context=ctx, boost=boost)

    def record_failure(
        self,
        context_url: str,
        selector: str,
        dom_hash: Optional[str] = None,
        extra_context: Optional[Dict[str, Any]] = None,
        penalty: float = 0.05,
    ) -> PromotionRecord:
        ctx = make_context_key(context_url, dom_hash, extra_context)
        return self.store.record_failure(locator=selector, context=ctx, penalty=penalty)
