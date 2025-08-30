"""Embeddings package exports and resolver re-exports."""

from . import _resolve  # re-export submodule for callers/tests
from .text_embedder import TextEmbedder
from .query_embedder import QueryEmbedder
from .element_embedder import ElementEmbedder

__all__ = [
    "_resolve",
    "TextEmbedder",
    "QueryEmbedder",
    "ElementEmbedder",
]