# src/her/promotion_adapter.py
from __future__ import annotations

"""
Promotion Adapter (SQLite-backed)

- Provides a stable way to compute label keys from parsed intent
- Looks up best promoted selector before retrieval
- Records success/failure after actions

Backed by: src/her/vectordb/sqlite_cache.py (promotions table)
"""

from typing import Iterable, Optional

from .vectordb.sqlite_cache import SQLiteKV


def compute_label_key(label_tokens: Iterable[str]) -> str:
    """
    Deterministic label key for promotions, insensitive to order/case.
    Example:
        ["Send", "message"] -> "label:message|send"
    """
    toks = sorted([t.strip().lower() for t in label_tokens if str(t).strip()])
    return "label:" + "|".join(toks)


def lookup_promotion(
    kv: SQLiteKV,
    page_sig: str,
    frame_hash: str,
    label_key: str,
) -> Optional[str]:
    """
    Return best selector for this page/frame/label if any, else None.
    """
    if not page_sig or not frame_hash or not label_key:
        return None
    return kv.get_promotion(page_sig=page_sig, frame_hash=frame_hash, label_key=label_key)


def record_success(
    kv: SQLiteKV,
    page_sig: str,
    frame_hash: str,
    label_key: str,
    selector: str,
) -> None:
    kv.record_promotion(
        page_sig=page_sig,
        frame_hash=frame_hash,
        label_key=label_key,
        selector=selector,
        success=True,
    )


def record_failure(
    kv: SQLiteKV,
    page_sig: str,
    frame_hash: str,
    label_key: str,
    selector: str,
) -> None:
    kv.record_promotion(
        page_sig=page_sig,
        frame_hash=frame_hash,
        label_key=label_key,
        selector=selector,
        success=False,
    )
