from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np

from .db import VectorIndex
from .hashing import frame_hash as compute_fhash


@dataclass
class FrameStore:
    frame_hash: str
    index: VectorIndex

@dataclass
class FrameManager:
    frames: Dict[str, FrameStore] = field(default_factory=dict)
    active: Optional[str] = None

    def ensure(self, frame_url: str, items: List[dict]) -> str:
        fh = compute_fhash(frame_url, items)
        if fh not in self.frames:
            self.frames[fh] = FrameStore(frame_hash=fh, index=VectorIndex())
        if self.active is None:
            self.active = fh
        return fh

    def set_active(self, frame_hash: str) -> None:
        if frame_hash in self.frames:
            self.active = frame_hash

    def get_index(self, frame_hash: Optional[str] = None) -> VectorIndex:
        fh = frame_hash or self.active
        if fh is None or fh not in self.frames:
            raise RuntimeError("No active frame/index.")
        return self.frames[fh].index

    def search_all_frames(self, qvec: np.ndarray, topk: int = 10):
        results = []
        for fh, store in self.frames.items():
            res = store.index.search(qvec, topk)
            for r in res:
                r["frame_hash"] = fh
                results.append(r)
        results.sort(key=lambda x: -x["score"])
        return results[:topk]
