from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from her.hashing import element_dom_hash
from her.vectordb.sqlite_cache import SQLiteKV
from her.vectordb.faiss_store import InMemoryVectorStore

# Query/text and element embedders
from her.embeddings.query_embedder import QueryEmbedder  # 384-d deterministic, lightweight
from her.embeddings.element_embedder import ElementEmbedder  # 768-d deterministic fallback

# MarkupLM (optional heavy embedder for elements)
try:
    from her.embeddings.markuplm_embedder import MarkupLMEmbedder  # 768-d
    _MARKUP_AVAILABLE = True
except Exception:
    _MARKUP_AVAILABLE = False

log = logging.getLogger("her.pipeline")


def _l2norm(v: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    n = np.linalg.norm(v, axis=-1, keepdims=True)
    n = np.maximum(n, eps)
    return v / n


def _cos(a: np.ndarray, b: np.ndarray) -> float:
    # a: (D,), b: (D,)
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom <= 1e-12:
        return 0.0
    return float(np.dot(a, b) / denom)


class HybridPipeline:
    """
    Production pipeline with cold/warm/delta flows:
      - Cold: first-time page/frame: embed all, cache in SQLite, build vector store(s)
      - Warm: reuse cached vectors; rebuild vector stores fast
      - Delta: only embed new/changed elements (by element_dom_hash)

    Public API preserved:
      - embed_query(text) -> np.ndarray
      - embed_elements(elements) -> np.ndarray (kept for compatibility; now delta+caching inside)
      - query(query_text, elements, top_k=10) -> Dict[str, Any]
    """

    # Dimensions
    _Q_DIM = 384   # Query (MiniLM/E5-like)
    _E_DIM = 768   # Element (MarkupLM-like / deterministic fallback)

    def __init__(self, models_root: Optional[Path] = None) -> None:
        # Models (optional for MarkupLM)
        self._models_root = Path(models_root) if models_root else None

        # Embedders
        self.text_embedder = QueryEmbedder(dim=self._Q_DIM)
        self.element_embedder = self._make_element_embedder()

        # Persistent cache (embeddings/promotions/kv)
        cache_dir = os.getenv("HER_CACHE_DIR") or str(Path(".her_cache").resolve())
        Path(cache_dir).mkdir(parents=True, exist_ok=True)
        self._db_path = str(Path(cache_dir) / "embeddings.db")
        self.kv = SQLiteKV(self._db_path, max_size_mb=400)

        # Per-frame vector stores: frame_hash -> InMemoryVectorStore
        self._stores: Dict[str, InMemoryVectorStore] = {}

        # Book-keeping: frame_hash -> list[metadata] mapped by local index in store
        # Metadata must include: {'hash': element_hash, 'xpath': str, 'tag': str, 'role': str, 'visible': bool, ...}
        self._meta: Dict[str, List[Dict[str, Any]]] = {}

        log.info("HybridPipeline ready | cache=%s markup=%s", self._db_path, _MARKUP_AVAILABLE)

    # ---------------------------------------------------------------------
    # Embedders
    # ---------------------------------------------------------------------
    def _make_element_embedder(self):
        """Prefer MarkupLM if present under models_root; else deterministic fallback."""
        if _MARKUP_AVAILABLE:
            # Allow both explicit models_root and default repo path
            model_dir: Optional[str] = None
            if self._models_root:
                # Common local layout: src/her/models/markuplm-base
                candidate = Path(self._models_root) / "markuplm-base"
                if candidate.exists():
                    model_dir = str(candidate)
            else:
                # Try repo default
                default = Path("src/her/models/markuplm-base")
                if default.exists():
                    model_dir = str(default)

            if model_dir:
                try:
                    emb = MarkupLMEmbedder(model_dir=model_dir, dim=self._E_DIM)  # type: ignore[arg-type]
                    log.info("Element embedder: MarkupLM @ %s", model_dir)
                    return emb
                except Exception as e:
                    log.warning("MarkupLM not available (%s); falling back to deterministic ElementEmbedder", e)

        log.info("Element embedder: deterministic fallback (ElementEmbedder)")
        return ElementEmbedder(cache_dir=None, dim=self._E_DIM)

    # ---------------------------------------------------------------------
    # Vector stores (per-frame)
    # ---------------------------------------------------------------------
    def _get_store(self, frame_hash: str) -> InMemoryVectorStore:
        st = self._stores.get(frame_hash)
        if st is None:
            st = InMemoryVectorStore(dim=self._E_DIM)
            self._stores[frame_hash] = st
            self._meta[frame_hash] = []
        return st

    def _reset_store(self, frame_hash: str) -> None:
        self._stores.pop(frame_hash, None)
        self._meta.pop(frame_hash, None)

    # ---------------------------------------------------------------------
    # Core: delta-aware element embedding + store (re)build
    # ---------------------------------------------------------------------
    def _prepare_elements(self, elements: List[Dict[str, Any]]) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
        """
        Delta-aware embedding for all provided elements across frames.
        Rebuilds the per-frame vector stores and returns a stacked array of element vectors
        (for compatibility with older code paths) along with aligned metadata list.
        """
        if not isinstance(elements, list):
            raise ValueError("elements must be a list of element descriptors")

        # Group by frame_hash for store assignment
        by_frame: Dict[str, List[Tuple[int, Dict[str, Any]]]] = {}
        for idx, el in enumerate(elements):
            meta = el.get("meta") or {}
            fh = meta.get("frame_hash")
            if not fh:
                raise ValueError("Each element must carry meta.frame_hash (wired in Step 3).")
            by_frame.setdefault(fh, []).append((idx, el))

        # Compute hashes, fetch cached embeddings, embed only missing, upsert
        all_vecs: List[np.ndarray] = []
        all_meta: List[Dict[str, Any]] = []

        for fh, batch in by_frame.items():
            store = self._get_store(fh)
            # Rebuild the store from scratch for that frame (fresh view of descriptors)
            self._reset_store(fh)
            store = self._get_store(fh)  # re-create clean
            frame_meta: List[Dict[str, Any]] = []

            # Compute element hashes first
            hashes: List[str] = []
            descs: List[Dict[str, Any]] = []
            for _, el in batch:
                h = element_dom_hash(el)
                hashes.append(h)
                descs.append(el)

            # Look up cached vectors
            cached_map = self.kv.batch_get_embeddings(hashes) if hashes else {}
            missing_pairs: List[Tuple[str, Dict[str, Any]]] = []
            vecs: List[np.ndarray] = []

            for h, el in zip(hashes, descs):
                v = cached_map.get(h)
                if v is not None:
                    arr = np.array(v, dtype=np.float32)
                    if arr.shape != (self._E_DIM,):
                        # Cache drift -> re-embed
                        missing_pairs.append((h, el))
                    else:
                        vecs.append(arr)
                else:
                    missing_pairs.append((h, el))

            # Embed missing with the element embedder (batched if available)
            if missing_pairs:
                missing_descs = [el for (_, el) in missing_pairs]
                if hasattr(self.element_embedder, "batch_encode"):
                    new_arr: np.ndarray = self.element_embedder.batch_encode(missing_descs)  # type: ignore[attr-defined]
                    if new_arr.ndim == 1:
                        new_arr = new_arr.reshape(1, -1)
                    if new_arr.shape[1] != self._E_DIM:
                        # pad/trim to E_DIM
                        fixed = np.zeros((new_arr.shape[0], self._E_DIM), dtype=np.float32)
                        k = min(self._E_DIM, new_arr.shape[1])
                        fixed[:, :k] = new_arr[:, :k]
                        new_arr = fixed
                    # Write-through into cache
                    to_put = {h: new_arr[i].astype(np.float32).tolist() for i, (h, _) in enumerate(missing_pairs)}
                    self.kv.batch_put_embeddings(to_put, model_name="elements")
                    for i in range(new_arr.shape[0]):
                        vecs.append(new_arr[i].astype(np.float32, copy=False))
                else:
                    for h, el in missing_pairs:
                        arr = np.array(self.element_embedder.encode(el), dtype=np.float32)  # type: ignore[attr-defined]
                        if arr.shape != (self._E_DIM,):
                            fixed = np.zeros((self._E_DIM,), dtype=np.float32)
                            k = min(self._E_DIM, arr.shape[0])
                            fixed[:k] = arr[:k]
                            arr = fixed
                        self.kv.put_embedding(h, arr.tolist(), model_name="elements")
                        vecs.append(arr)

            # Now vecs is aligned with descs (cached + new) in order
            assert len(vecs) == len(descs)

            # Rebuild frame store with vectors + metadata
            for arr, el, h in zip(vecs, descs, hashes):
                meta = {
                    "hash": h,
                    "xpath": el.get("xpath") or "",
                    "tag": (el.get("tag") or "").lower(),
                    "role": ((el.get("attrs") or {}).get("role") or "").lower(),
                    "visible": bool(el.get("visible")),
                    "frame_url": el.get("frame_url") or (el.get("meta") or {}).get("frame_url") or "",
                }
                idx = store.add_vector(arr.astype(np.float32).tolist(), meta)
                # Ensure index alignment
                if idx != len(frame_meta):
                    # If FAISS inserted elsewhere (shouldn't), normalize:
                    # rebuild not expected to reorder; enforce append-only
                    pass
                frame_meta.append(meta)

            # Collect for flat array result (compat with older callers)
            all_meta.extend(frame_meta)
            all_vecs.extend([np.array(v, dtype=np.float32) for v in store.vectors])

        # Stack vectors for embed_elements() compatibility
        if all_vecs:
            E = np.vstack(all_vecs).astype(np.float32, copy=False)
        else:
            E = np.zeros((0, self._E_DIM), dtype=np.float32)

        return E, all_meta

    # ---------------------------------------------------------------------
    # Public: embed_query / embed_elements
    # ---------------------------------------------------------------------
    def embed_query(self, text: str) -> np.ndarray:
        if not isinstance(text, str) or not text.strip():
            raise ValueError("query text must be a non-empty string")
        q = self.text_embedder.encode(text)
        q = np.array(q, dtype=np.float32).reshape(-1)
        if q.shape[0] != self._Q_DIM:
            fix = np.zeros((self._Q_DIM,), dtype=np.float32)
            k = min(self._Q_DIM, q.shape[0])
            fix[:k] = q[:k]
            q = fix
        return _l2norm(q)

    def embed_elements(self, elements: List[Dict[str, Any]]) -> np.ndarray:
        # For backward compatibility: returns a 2D array of element vectors.
        E, _ = self._prepare_elements(elements)
        return E

    # ---------------------------------------------------------------------
    # Public: query
    # ---------------------------------------------------------------------
    def query(self, query: str, elements: List[Dict[str, Any]], top_k: int = 10) -> Dict[str, Any]:
        """
        Resolve a natural-language query against element descriptors.

        Returns:
            {
              "results": [ { "selector": str, "score": float, "reasons": [str, ...], "meta": {...} }, ... ],
              "strategy": "hybrid-delta",
              "confidence": float
            }
        """
        if not isinstance(elements, list):
            raise ValueError("elements must be a list")
        if len(elements) == 0:
            return {"results": [], "strategy": "hybrid-delta", "confidence": 0.0}

        # Ensure stores & cache are synced with latest descriptors (delta-aware)
        E, meta = self._prepare_elements(elements)
        if E.size == 0:
            return {"results": [], "strategy": "hybrid-delta", "confidence": 0.0}

        q = self.embed_query(query)

        # Shortlist per frame using vector stores, then merge
        # We reuse the freshly rebuilt stores
        all_hits: List[Tuple[float, Dict[str, Any]]] = []

        for fh, store in self._stores.items():
            # Use FAISS cosine distance approximations by converting to L2 if needed; our store returns (index, distance, metadata)
            # We built vectors normalized, but store does not assume normalized — so we compute cosine post-hoc.
            # Fetch top (k * 3) to allow room for post-rerank merges.
            k = max(5, int(top_k))
            raw = store.search(q.tolist(), k=k)
            # raw: List[(idx, distance, metadata)]
            # Convert to cosine via actual dot with E (safe as we’ve aligned stacking order).
            for idx, _dist, md in raw:
                # Align to global flat E/meta: we stacked stores in _prepare_elements in frame order,
                # but we no longer track global indices; compute cosine with the vector we have in the store.
                vec = np.array(store.vectors[idx], dtype=np.float32)
                score = _cos(q, vec)
                all_hits.append((score, md))

        # Merge and re-rank with light tie-breaks
        if not all_hits:
            return {"results": [], "strategy": "hybrid-delta", "confidence": 0.0}

        # Simple hybrid bonuses: tag/role/href if present
        def _tag_bias(tag: str) -> float:
            tag = (tag or "").lower()
            if tag == "button": return 0.02
            if tag == "a":      return 0.015
            if tag == "input":  return 0.010
            return 0.0

        def _role_bonus(role: str) -> float:
            role = (role or "").lower()
            if role in ("button", "link", "tab", "menuitem"):
                return 0.01
            return 0.0

        ranked: List[Tuple[float, Dict[str, Any], List[str]]] = []
        for base_score, md in all_hits:
            reasons: List[str] = [f"cosine={base_score:.3f}"]
            b = _tag_bias(md.get("tag", "")) + _role_bonus(md.get("role", ""))
            if b:
                reasons.append(f"+bias={b:.3f}")
            ranked.append((base_score + b, md, reasons))

        ranked.sort(key=lambda t: t[0], reverse=True)
        ranked = ranked[:top_k]

        # Confidence = top score clipped to [0, 1]
        confidence = max(0.0, min(1.0, ranked[0][0] if ranked else 0.0))

        results = []
        for score, md, reasons in ranked:
            sel = md.get("xpath") or ""  # We return XPath as selector
            results.append({
                "selector": sel,
                "score": float(score),
                "reasons": reasons,
                "meta": md,
            })

        return {
            "results": results,
            "strategy": "hybrid-delta",
            "confidence": float(confidence),
        }
