# Alias to current FAISS store
try:
    from .faiss_store import InMemoryVectorStore as FaissStore, FAISSStore
except ImportError as e:
    # Handle missing dependencies gracefully
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"FAISS dependencies not available: {e}")
    
    # Create dummy classes for when dependencies are missing
    class FaissStore:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("FAISS dependencies not available. Install with: pip install faiss-cpu numpy")
    
    class FAISSStore(FaissStore):
        pass

# Create aliases for the methods that exist
def build_faiss_index(dim=768):
    """Build a new FAISS index."""
    return FaissStore(dim=dim)

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
