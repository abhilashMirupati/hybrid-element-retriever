# src/her/vectordb/__init__.py
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from .sqlite_cache import SQLiteKV

__all__ = ["get_default_kv", "SQLiteKV"]


_singleton: Optional[SQLiteKV] = None


def get_default_kv(db_path: Optional[str] = None, max_size_mb: int = 400) -> SQLiteKV:
    """
    Singleton accessor for a shared SQLiteKV instance.

    Priority for DB location:
    1) explicit db_path arg
    2) $HER_CACHE_DIR/embeddings.db
    3) ./.her_cache/embeddings.db
    """
    global _singleton
    if _singleton is not None:
        return _singleton

    if db_path is None:
        cache_dir = os.getenv("HER_CACHE_DIR") or str(Path(".her_cache").resolve())
        Path(cache_dir).mkdir(parents=True, exist_ok=True)
        db_path = str(Path(cache_dir) / "embeddings.db")

    _singleton = SQLiteKV(db_path=db_path, max_size_mb=max_size_mb)
    return _singleton
