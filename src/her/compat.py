"""Compatibility shims for legacy tests.

This module provides:

- HERPipeline: a thin wrapper around the modern HybridPipeline, exposing
  legacy method names expected by older tests. It is intentionally minimal and
  should be considered temporary for migration.

- resolve_model_paths(): a stable, JSON-serializable helper returning the
  resolved model metadata and paths for both text-embedding and
  element-embedding tasks. It handles ResolverError gracefully.

These shims ensure legacy imports continue to function while the new
HybridPipeline remains the primary API. This module may be removed once
downstream consumers migrate.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .embeddings import _resolve


@dataclass
class _CompatResult:
    element: Optional[Dict[str, Any]]
    xpath: Optional[str]
    confidence: float
    strategy: str
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "element": self.element,
            "xpath": self.xpath or "",
            "confidence": float(self.confidence),
            "strategy": str(self.strategy),
            "metadata": dict(self.metadata or {}),
        }


class HERPipeline:
    """Legacy wrapper delegating to HybridPipeline.

    Notes:
    - Accepts a `config` object for legacy call sites but does not rely on it.
    - Provides a `process(query, dom)` method that forwards to HybridPipeline.
    - Exposes private methods expected by tests for patching.
    """

    def __init__(self, config: Optional[Any] = None, **kwargs: Any) -> None:
        # Ignore legacy config fields; HybridPipeline manages its own options
        # Import here to avoid circular import during module initialization
        from .pipeline import HybridPipeline  # local import
        self._pipe = HybridPipeline()

    # --- Legacy surface expected by tests ---------------------------------
    def process(self, query: str, dom: Dict[str, Any]) -> Dict[str, Any]:
        result = self._pipe.query(query, dom_snapshot=dom)
        # Ensure deterministic, JSON-serializable structure
        cr = _CompatResult(
            element=result.get("element"),
            xpath=result.get("xpath"),
            confidence=float(result.get("confidence", 0.0)),
            strategy=str(result.get("strategy", "fusion")),
            metadata=dict(result.get("metadata", {})),
        )
        return cr.to_dict()

    # The following methods are present so tests can patch them. Implement
    # simple defaults; behavior is defined by tests when patched.
    def _get_dom_snapshot(self, dom: Dict[str, Any]) -> Dict[str, Any]:
        return dom

    def _embed_query(self, query: str) -> Any:
        return [[0.0] * 384]

    def _rerank_with_markuplm(self, query: str, candidates: Any) -> Any:
        return candidates

    def _is_cold_start(self) -> bool:
        return False

    def _embed_element(self, element: Dict[str, Any]) -> Any:
        return [[0.0] * 768]


def resolve_model_paths() -> Dict[str, Dict[str, Any]]:
    """Return resolved model metadata and paths for both tasks.

    Structure:
        {
          "text-embedding": {"id": str|None, "onnx": str|None, "tokenizer": str|None},
          "element-embedding": {"id": str|None, "onnx": str|None, "tokenizer": str|None}
        }

    All values are JSON-serializable and deterministic. Missing items are None.
    """
    out: Dict[str, Dict[str, Any]] = {
        "text-embedding": {"id": None, "onnx": None, "tokenizer": None},
        "element-embedding": {"id": None, "onnx": None, "tokenizer": None},
    }

    try:
        mp = _resolve.resolve_text_embedding()
        out["text-embedding"]["id"] = mp.id
        out["text-embedding"]["onnx"] = str(mp.onnx)
        out["text-embedding"]["tokenizer"] = str(mp.tokenizer)
    except Exception:
        # Graceful fallback
        pass

    try:
        mp = _resolve.resolve_element_embedding()
        out["element-embedding"]["id"] = mp.id
        out["element-embedding"]["onnx"] = str(mp.onnx)
        out["element-embedding"]["tokenizer"] = str(mp.tokenizer)
    except Exception:
        # Graceful fallback
        pass

    return out

