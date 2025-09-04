from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import numpy as np

from ..vectordb.two_tier_cache import TwoTierCache


class Session:
    """Track DOM and route changes per page with SPA listeners and cache stats."""

    def __init__(self, page: Any, delta_threshold: int = 50, cache_dir: Optional[str] = None, max_memory_items: int = 4096) -> None:
        self.page = page
        self.delta_threshold = int(delta_threshold)
        self._last_dom_hash: Optional[str] = None
        self._last_url: Optional[str] = None
        self._indexed_at: float = 0.0
        self.route_changed: bool = False
        root = Path(cache_dir) if cache_dir else (Path.home() / '.cache' / 'her')
        self.cache = TwoTierCache(root, max_memory_items=max_memory_items)
        self._install_spa_hooks()

    def _install_spa_hooks(self) -> None:
        try:
            if hasattr(self.page, 'evaluate'):
                self.page.evaluate(
                    """
(() => {
  try {
    const w = window;
    if (w.__her_spa_hooks_installed__) return;
    w.__her_spa_hooks_installed__ = true;
    w.__her_route_changed__ = false;
    const origPush = history.pushState;
    const origReplace = history.replaceState;
    history.pushState = function(){ w.__her_route_changed__ = true; return origPush.apply(this, arguments); };
    history.replaceState = function(){ w.__her_route_changed__ = true; return origReplace.apply(this, arguments); };
    window.addEventListener('popstate', () => { w.__her_route_changed__ = true; }, { capture: true });
  } catch (e) {}
})();
"""
                )
        except Exception:
            # Non-fatal
            pass

    def _compute_dom_hash(self) -> str:
        try:
            dom = self.page.content()
        except Exception:
            dom = ""
        return hashlib.sha1(dom.encode('utf-8')).hexdigest()

    def _check_route_changed(self) -> bool:
        try:
            if hasattr(self.page, 'evaluate'):
                changed = bool(self.page.evaluate('window.__her_route_changed__ === true'))
                if changed:
                    # reset the flag in page context
                    self.page.evaluate('window.__her_route_changed__ = false')
                return changed
        except Exception:
            return False
        return False

    def needs_reindex(self) -> bool:
        try:
            return self._last_dom_hash != self._compute_dom_hash() or self._check_route_changed()
        except Exception:
            return True

    def reindex_if_needed(self) -> bool:
        try:
            current_hash = self._compute_dom_hash()
            current_url = getattr(self.page, 'url', None)
            route_changed = self._check_route_changed()
            changed = (
                self._last_dom_hash is None
                or current_hash != self._last_dom_hash
                or current_url != self._last_url
                or route_changed
            )
            if changed:
                self._last_dom_hash, self._last_url = current_hash, current_url
                self._indexed_at = time.time()
                self.route_changed = route_changed or (current_url != self._last_url)
                return True
            return False
        except Exception:
            return True

    def url_changed(self) -> bool:
        try:
            u = getattr(self.page, 'url', None)
            return self._last_url is None or u != self._last_url
        except Exception:
            return True

    def reset(self) -> None:
        self._last_dom_hash = None
        self._last_url = None
        self._indexed_at = 0.0
        self.route_changed = False

    def stats(self) -> dict:
        try:
            return self.cache.stats()
        except Exception:
            return {}


__all__ = ['Session']


@dataclass
class SessionManager:
    auto_index: bool = True
    reindex_on_change: bool = True
    cache_dir: Optional[str] = None
    max_memory_items: int = 4096

    def create_session(self, session_id: str, page: Any) -> Session:
        return Session(page, cache_dir=self.cache_dir, max_memory_items=self.max_memory_items)

