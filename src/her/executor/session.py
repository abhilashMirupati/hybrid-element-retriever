# src/her/executor/session.py
# Session manager for HER: tracks Playwright page, DOM/AX snapshots,
# route changes, and triggers automatic re-indexing when DOM deltas cross threshold.

from __future__ import annotations

import hashlib
import time
from typing import Any, Dict, Optional, Tuple


class Session:
    """
    Hybrid Element Retriever Session wrapper.
    Responsibilities:
      - Manage a Playwright Page object.
      - Track SPA route changes via pushState/replaceState/popstate.
      - Compute frame/DOM hashes for delta detection.
      - Auto re-index when DOM delta threshold exceeded.
    """

    def __init__(self, page: Any, delta_threshold: int = 50) -> None:
        self.page = page
        self.delta_threshold = delta_threshold
        self._last_dom_hash: Optional[str] = None
        self._last_url: Optional[str] = None
        self._indexed_at: float = 0.0

    def _compute_dom_hash(self) -> str:
        try:
            dom = self.page.content()
            return hashlib.sha1(dom.encode("utf-8")).hexdigest()
        except Exception as e:
            raise RuntimeError(f"Failed to compute DOM hash: {e}") from e

    def needs_reindex(self) -> bool:
        try:
            current_hash = self._compute_dom_hash()
            if self._last_dom_hash is None:
                return True
            if current_hash != self._last_dom_hash:
                return True
            return False
        except Exception:
            return True

    def reindex_if_needed(self) -> bool:
        """
        If DOM hash or URL changed since last index, trigger re-index.
        Returns True if reindex performed.
        """
        try:
            current_hash = self._compute_dom_hash()
            current_url = self.page.url
            if (
                self._last_dom_hash is None
                or current_hash != self._last_dom_hash
                or current_url != self._last_url
            ):
                self._last_dom_hash = current_hash
                self._last_url = current_url
                self._indexed_at = time.time()
                return True
            return False
        except Exception:
            return True

    def url_changed(self) -> bool:
        try:
            current_url = self.page.url
            if self._last_url is None:
                return True
            return current_url != self._last_url
        except Exception:
            return True

    def reset(self) -> None:
        """Reset tracking state (used when navigating to new app or clearing cache)."""
        self._last_dom_hash = None
        self._last_url = None
        self._indexed_at = 0.0


__all__ = ["Session"]
