from __future__ import annotations
import hashlib, time
from typing import Any, Optional
class Session:
    def __init__(self, page: Any, delta_threshold: int=50) -> None:
        self.page = page; self.delta_threshold = delta_threshold
        self._last_dom_hash: Optional[str] = None; self._last_url: Optional[str] = None; self._indexed_at: float = 0.0
    def _compute_dom_hash(self) -> str:
        dom = self.page.content(); return hashlib.sha1(dom.encode('utf-8')).hexdigest()
    def needs_reindex(self) -> bool:
        try: h = self._compute_dom_hash(); return self._last_dom_hash != h
        except Exception: return True
    def reindex_if_needed(self) -> bool:
        try:
            h = self._compute_dom_hash(); u = self.page.url
            if self._last_dom_hash is None or h != self._last_dom_hash or u != self._last_url:
                self._last_dom_hash, self._last_url = h, u; self._indexed_at = time.time(); return True
            return False
        except Exception: return True
    def url_changed(self) -> bool:
        try: u = self.page.url; return self._last_url is None or u != self._last_url
        except Exception: return True
    def reset(self) -> None:
        self._last_dom_hash = None; self._last_url=None; self._indexed_at=0.0
__all__=['Session']
