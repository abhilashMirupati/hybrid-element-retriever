# Alias to current FAISS store
from .faiss_store import InMemoryVectorStore as FaissStore, FAISSStore

# Create aliases for the methods that exist
def build_faiss_index(dim=768):
    """Build a new FAISS index."""
    return InMemoryVectorStore(dim=dim)

def search_vectors(store, query, k=5, threshold=None):
    """Search vectors in the store."""
    return store.search(query, k=k, threshold=threshold)

def upsert_vectors(store, vectors, metadata=None):
    """Add vectors to the store."""
    if isinstance(vectors, list) and len(vectors) > 0:
        return [store.add(vector, metadata) for vector in vectors]
    else:
        return store.add(vectors, metadata)

__all__ = ["FaissStore", "FAISSStore", "build_faiss_index", "upsert_vectors", "search_vectors"]
