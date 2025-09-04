# Alias to current FAISS store
from .faiss_store import (
    FaissStore,        # if you expose a class
    build_faiss_index, # or your builder funcs
    upsert_vectors,
    search_vectors,
)
__all__ = ["FaissStore", "build_faiss_index", "upsert_vectors", "search_vectors"]
