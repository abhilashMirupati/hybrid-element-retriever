"""Vector store implementation that works with or without FAISS/numpy."""

import math
from typing import List, Optional, Tuple, Union

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None  # type: ignore

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    faiss = None  # type: ignore


class InMemoryVectorStore:
    """In-memory vector store with FAISS acceleration when available."""
    
    def __init__(self, dim: int = 768):
        """Initialize vector store.
        
        Args:
            dim: Dimension of vectors
        """
        self.dim = dim
        self.vectors: List[List[float]] = []
        self.metadata: List[dict] = []
        
        # Use FAISS if available
        if FAISS_AVAILABLE and NUMPY_AVAILABLE:
            self.index = faiss.IndexFlatL2(dim)
            self.use_faiss = True
        else:
            self.index = None
            self.use_faiss = False
    
    # Backwards-compat: some call sites expect add_vector()
    def add_vector(self, vector: Union[List[float], 'np.ndarray'], metadata: dict = None) -> int:
        return self.add(vector, metadata)
    
    def add(self, vector: Union[List[float], 'np.ndarray'], metadata: dict = None) -> int:
        """Add vector to store.
        
        Args:
            vector: Vector to add
            metadata: Optional metadata
            
        Returns:
            Index of added vector
        """
        # Convert to list for storage
        if NUMPY_AVAILABLE and isinstance(vector, np.ndarray):
            vec_list = vector.tolist()
        else:
            vec_list = list(vector) if hasattr(vector, '__iter__') else [vector]
        
        # Pad or truncate to match dimension
        if len(vec_list) < self.dim:
            vec_list = vec_list + [0.0] * (self.dim - len(vec_list))
        elif len(vec_list) > self.dim:
            vec_list = vec_list[:self.dim]
        
        idx = len(self.vectors)
        self.vectors.append(vec_list)
        self.metadata.append(metadata or {})
        
        # Add to FAISS index if available
        if self.use_faiss:
            vec_array = np.array([vec_list], dtype='float32')
            self.index.add(vec_array)
        
        return idx
    
    def search(
        self,
        query: Union[List[float], 'np.ndarray'],
        k: int = 5,
        threshold: float = None
    ) -> List[Tuple[int, float, dict]]:
        """Search for similar vectors.
        
        Args:
            query: Query vector
            k: Number of results
            threshold: Optional similarity threshold
            
        Returns:
            List of (index, distance, metadata) tuples
        """
        if len(self.vectors) == 0:
            return []
        
        # Convert query to appropriate format
        if NUMPY_AVAILABLE and isinstance(query, np.ndarray):
            query_list = query.tolist()
        else:
            query_list = list(query) if hasattr(query, '__iter__') else [query]
        
        # Pad or truncate query
        if len(query_list) < self.dim:
            query_list = query_list + [0.0] * (self.dim - len(query_list))
        elif len(query_list) > self.dim:
            query_list = query_list[:self.dim]
        
        if self.use_faiss:
            # Use FAISS for search
            query_array = np.array([query_list], dtype='float32')
            distances, indices = self.index.search(query_array, min(k, len(self.vectors)))
            
            results = []
            for i in range(len(indices[0])):
                idx = int(indices[0][i])
                if idx >= 0:  # FAISS returns -1 for not found
                    dist = float(distances[0][i])
                    if threshold is None or dist <= threshold:
                        results.append((idx, dist, self.metadata[idx]))
            
            return results
        else:
            # Pure Python search
            distances = []
            for i, vec in enumerate(self.vectors):
                dist = self._euclidean_distance(query_list, vec)
                distances.append((i, dist, self.metadata[i]))
            
            # Sort by distance
            distances.sort(key=lambda x: x[1])
            
            # Filter by threshold if provided
            if threshold is not None:
                distances = [(i, d, m) for i, d, m in distances if d <= threshold]
            
            return distances[:k]
    
    def _euclidean_distance(self, vec1: List[float], vec2: List[float]) -> float:
        """Compute Euclidean distance between vectors."""
        if len(vec1) != len(vec2):
            # Pad shorter vector
            max_len = max(len(vec1), len(vec2))
            vec1 = vec1 + [0.0] * (max_len - len(vec1))
            vec2 = vec2 + [0.0] * (max_len - len(vec2))
        
        sum_sq = sum((a - b) ** 2 for a, b in zip(vec1, vec2))
        return math.sqrt(sum_sq)
    
    def clear(self) -> None:
        """Clear all vectors."""
        self.vectors.clear()
        self.metadata.clear()
        
        if self.use_faiss:
            self.index.reset()
    
    def size(self) -> int:
        """Get number of vectors."""
        return len(self.vectors)
    
    def get(self, idx: int) -> Optional[Tuple[List[float], dict]]:
        """Get vector by index.
        
        Args:
            idx: Vector index
            
        Returns:
            Tuple of (vector, metadata) or None
        """
        if 0 <= idx < len(self.vectors):
            return (self.vectors[idx], self.metadata[idx])
        return None


# Compatibility alias expected by tests
class FAISSStore(InMemoryVectorStore):
    pass