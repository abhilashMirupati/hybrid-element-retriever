"""Embeddings package exports and resolver re-exports."""

from . import _resolve  # re-export submodule for callers/tests
from .text_embedder import TextEmbedder
from .query_embedder import QueryEmbedder
from .element_embedder import ElementEmbedder
try:
    from .markuplm_embedder import MarkupLMEmbedder  # type: ignore
except Exception:
    MarkupLMEmbedder = None  # type: ignore

__all__ = [
    "_resolve",
    "TextEmbedder",
    "QueryEmbedder",
    "ElementEmbedder",
    "MarkupLMEmbedder",
]