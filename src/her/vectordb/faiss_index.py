# Alias to current FAISS store
from .faiss_store import FaissStore  # if you expose a class
from .faiss_store import build_faiss_index  # or your builder funcs
from .faiss_store import search_vectors, upsert_vectors

__all__ = ["FaissStore", "build_faiss_index", "upsert_vectors", "search_vectors"]
