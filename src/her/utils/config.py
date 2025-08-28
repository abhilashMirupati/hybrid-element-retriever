from __future__ import annotations
from dataclasses import dataclass
@dataclass(frozen=True)
class Config:
    delta_threshold:int=50
    cache_capacity:int=2048
