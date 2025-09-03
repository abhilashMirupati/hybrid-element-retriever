from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
import time
from .hashing import page_signature

@dataclass
class PromoEntry:
    primary_selector: str
    alternates: List[str]
    updated_at: float
    hits: int = 0
    ttl_sec: int = 14 * 24 * 3600  # 14 days

    def is_fresh(self) -> bool:
        return (time.time() - self.updated_at) < self.ttl_sec

@dataclass
class PromotionDB:
    """
    In-memory promotion DB keyed by (page_sig, frame_hash, label_key).
    label_key = tuple(sorted(tokens)) to match intent target quickly.
    """
    store: Dict[Tuple[str, str, Tuple[str, ...]], PromoEntry] = field(default_factory=dict)

    @staticmethod
    def _label_key(label_tokens: List[str]) -> Tuple[str, ...]:
        return tuple(sorted([t.lower() for t in label_tokens if t]))

    def get(self, url: str, frame_hash: str, label_tokens: List[str]) -> Optional[PromoEntry]:
        key = (page_signature(url), frame_hash, self._label_key(label_tokens))
        ent = self.store.get(key)
        if ent and ent.is_fresh():
            ent.hits += 1
            return ent
        return None

    def put(self, url: str, frame_hash: str, label_tokens: List[str], primary: str, alternates: List[str]) -> None:
        key = (page_signature(url), frame_hash, self._label_key(label_tokens))
        self.store[key] = PromoEntry(primary_selector=primary, alternates=alternates, updated_at=time.time())
