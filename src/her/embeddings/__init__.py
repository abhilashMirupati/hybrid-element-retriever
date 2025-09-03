"""Embeddings package exports with safe, optional heavy imports."""
from . import _resolve

# Hard deps
from .query_embedder import QueryEmbedder
from .element_embedder import ElementEmbedder

# Optional deps: make import safe if onnxruntime/transformers missing
try:
    from .text_embedder import TextEmbedder  # MiniLM/E5 (ONNX)
except Exception:  # pragma: no cover
    TextEmbedder = None  # type: ignore

try:
    from .markuplm_embedder import MarkupLMEmbedder  # Transformers
except Exception:  # pragma: no cover
    MarkupLMEmbedder = None  # type: ignore

__all__ = [
    "_resolve",
    "QueryEmbedder",
    "ElementEmbedder",
    "TextEmbedder",
    "MarkupLMEmbedder",
]
