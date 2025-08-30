# Minimal exports to avoid heavy imports at package import time
from . import _resolve  # re-export submodule access
from .text_embedder import TextEmbedder as QueryEmbedder

__all__ = [
    '_resolve',
    'QueryEmbedder',
]
from .query_embedder import QueryEmbedder
from .element_embedder import ElementEmbedder

__all__ = [
    'ONNXModelResolver', 'get_query_resolver', 'get_element_resolver',
    'QueryEmbedder', 'ElementEmbedder'
]