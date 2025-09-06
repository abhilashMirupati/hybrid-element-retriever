"""Vector store implementation using FAISS (mandatory)."""
from typing import List, Optional, Tuple, Union
import numpy as np
try:
    import faiss  # type: ignore
except Exception as e:  # pragma: no cover
    raise RuntimeError("FAISS is required for vector retrieval. Install with `pip install faiss-cpu`.") from e

class InMemoryVectorStore:
    def __init__(self, dim: int = 768):
        self.dim = int(dim)
        self.index = faiss.IndexFlatIP(self.dim)  # cosine via IP + L2 norm
        self.vectors: List[List[float]] = []
        self.metadata: List[dict] = []

    def _normalize(self, x: np.ndarray) -> np.ndarray:
        n = np.linalg.norm(x, axis=-1, keepdims=True)
        n[n == 0] = 1.0
        return x / n

    def add_vector(self, vector: Union[List[float], np.ndarray], metadata: dict = None) -> int:
        return self.add(vector, metadata)

    def add(self, vector: Union[List[float], np.ndarray], metadata: dict = None) -> int:
        vec = np.array(vector, dtype="float32").reshape(1, -1)
        if vec.shape[1] != self.dim:
            fixed = np.zeros((1, self.dim), dtype="float32")
            k = min(self.dim, vec.shape[1])
            fixed[:, :k] = vec[:, :k]
            vec = fixed
        vec = self._normalize(vec)
        self.index.add(vec)
        self.vectors.append(vec.flatten().tolist())
        self.metadata.append(metadata or {})
        return len(self.vectors) - 1

    def search(self, query: Union[List[float], np.ndarray], k: int = 5, threshold: float = None) -> List[Tuple[int, float, dict]]:
        if len(self.vectors) == 0:
            return []
        q = np.array(query, dtype="float32").reshape(1, -1)
        if q.shape[1] != self.dim:
            fixed = np.zeros((1, self.dim), dtype="float32")
            kdim = min(self.dim, q.shape[1])
            fixed[:, :kdim] = q[:, :kdim]
            q = fixed
        q = self._normalize(q)
        D, I = self.index.search(q, min(k, len(self.vectors)))
        results: List[Tuple[int, float, dict]] = []
        for idx, score in zip(I[0], D[0]):
            if int(idx) < 0:
                continue
            if threshold is None or float(score) >= float(threshold):
                results.append((int(idx), float(score), self.metadata[int(idx)]))
        return results

    def clear(self) -> None:
        self.index.reset()
        self.vectors.clear()
        self.metadata.clear()

    def size(self) -> int:
        return len(self.vectors)

    def get(self, idx: int) -> Optional[Tuple[List[float], dict]]:
        if 0 <= idx < len(self.vectors):
            return (self.vectors[idx], self.metadata[idx])
        return None

class FAISSStore(InMemoryVectorStore):
    pass