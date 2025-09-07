from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from her.embeddings._resolve import preflight_require_models
from her.embeddings.text_embedder import TextEmbedder
from her.embeddings.element_embedder import \
    ElementEmbedder  # 768-d deterministic fallback
from her.hashing import element_dom_hash
from her.vectordb.faiss_store import InMemoryVectorStore
from her.vectordb.sqlite_cache import SQLiteKV

# Optional heavy embedder (if present locally)
try:
    from her.embeddings.markuplm_embedder import MarkupLMEmbedder  # 768-d
    _MARKUP_IMPORT_OK = True
except Exception:
    _MARKUP_IMPORT_OK = False

# Promotions (Step 6)
from her.promotion_adapter import lookup_promotion

log = logging.getLogger("her.pipeline")


def _l2norm(v: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    n = np.linalg.norm(v, axis=-1, keepdims=True)
    n = np.maximum(n, eps)
    return v / n


def _cos(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom <= 1e-12:
        return 0.0
    return float(np.dot(a, b) / denom)


class HybridPipeline:
    _Q_DIM = 384   # Query (MiniLM dimension)
    _E_DIM = 768   # Element (MarkupLM dimension)

    def __init__(self, models_root: Optional[Path] = None) -> None:
        # Fail-fast: require models installed
        preflight_require_models(models_root)
        self._models_root = Path(models_root) if models_root else None

        # Embedders - separate for hybrid approach
        model_root = str((self._models_root or Path("src/her/models").resolve()) / "e5-small-onnx")
        self.text_embedder = TextEmbedder(model_root=model_root)  # 384-d for queries
        self.element_embedder = self._make_element_embedder()  # 768-d for elements

        # Persistent cache
        cache_dir = os.getenv("HER_CACHE_DIR") or str(Path(".her_cache").resolve())
        Path(cache_dir).mkdir(parents=True, exist_ok=True)
        self._db_path = str(Path(cache_dir) / "embeddings.db")
        self.kv = SQLiteKV(self._db_path, max_size_mb=400)

        # Per-frame stores - separate for each stage
        self._mini_stores: Dict[str, InMemoryVectorStore] = {}  # 384-d for MiniLM shortlist
        self._markup_stores: Dict[str, InMemoryVectorStore] = {}  # 768-d for MarkupLM rerank
        self._meta: Dict[str, List[Dict[str, Any]]] = {}

        log.info("HybridPipeline ready | cache=%s | MiniLM=%dd | MarkupLM=%dd", 
                self._db_path, self._Q_DIM, self._E_DIM)

    def _make_element_embedder(self):
        # Require MarkupLM now that models are preflighted
        if not _MARKUP_IMPORT_OK:
            raise RuntimeError("Transformers MarkupLM is not available. Install transformers and run model installer.")
        model_dir: Optional[str] = None
        if self._models_root:
            candidate = Path(self._models_root) / "markuplm-base"
            if candidate.exists():
                model_dir = str(candidate)
        else:
            default = Path("src/her/models/markuplm-base")
            if default.exists():
                model_dir = str(default)
        if not model_dir:
            raise RuntimeError("MarkupLM model directory not found. Set HER_MODELS_DIR and run install_models.")
        emb = MarkupLMEmbedder(model_dir=model_dir)  # type: ignore[arg-type]
        log.info("Element embedder: MarkupLM @ %s", model_dir)
        return emb

    def _get_mini_store(self, frame_hash: str) -> InMemoryVectorStore:
        st = self._mini_stores.get(frame_hash)
        if st is None:
            st = InMemoryVectorStore(dim=self._Q_DIM)  # 384-d for MiniLM
            self._mini_stores[frame_hash] = st
        return st

    def _get_markup_store(self, frame_hash: str) -> InMemoryVectorStore:
        st = self._markup_stores.get(frame_hash)
        if st is None:
            st = InMemoryVectorStore(dim=self._E_DIM)  # 768-d for MarkupLM
            self._markup_stores[frame_hash] = st
        return st

    def _reset_stores(self, frame_hash: str) -> None:
        self._mini_stores.pop(frame_hash, None)
        self._markup_stores.pop(frame_hash, None)
        self._meta.pop(frame_hash, None)

    def _prepare_elements(self, elements: List[Dict[str, Any]]) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
        """Prepare elements for hybrid search - creates both MiniLM and MarkupLM embeddings."""
        if not isinstance(elements, list):
            raise ValueError("elements must be a list of element descriptors")

        by_frame: Dict[str, List[Tuple[int, Dict[str, Any]]]] = {}
        for idx, el in enumerate(elements):
            meta = el.get("meta") or {}
            fh = meta.get("frame_hash")
            if not fh:
                raise ValueError("Each element must include meta.frame_hash (wired in Step 3).")
            by_frame.setdefault(fh, []).append((idx, el))

        all_meta: List[Dict[str, Any]] = []

        for fh, batch in by_frame.items():
            self._reset_stores(fh)
            mini_store = self._get_mini_store(fh)  # 384-d for MiniLM shortlist
            markup_store = self._get_markup_store(fh)  # 768-d for MarkupLM rerank
            frame_meta: List[Dict[str, Any]] = []

            hashes: List[str] = []
            descs: List[Dict[str, Any]] = []
            for _, el in batch:
                h = element_dom_hash(el)
                hashes.append(h)
                descs.append(el)

            # Check cache for both MiniLM and MarkupLM embeddings
            cached_map = self.kv.batch_get_embeddings(hashes) if hashes else {}
            missing_mini: List[Tuple[str, Dict[str, Any]]] = []
            missing_markup: List[Tuple[str, Dict[str, Any]]] = []
            mini_vecs: List[np.ndarray] = []
            markup_vecs: List[np.ndarray] = []

            for h, el in zip(hashes, descs):
                v = cached_map.get(h)
                if v is not None:
                    arr = np.array(v, dtype=np.float32)
                    if arr.shape == (self._Q_DIM,):  # MiniLM cached
                        mini_vecs.append(arr)
                    elif arr.shape == (self._E_DIM,):  # MarkupLM cached
                        markup_vecs.append(arr)
                    else:
                        missing_mini.append((h, el))
                        missing_markup.append((h, el))
                else:
                    missing_mini.append((h, el))
                    missing_markup.append((h, el))

            # Generate missing MiniLM embeddings (384-d)
            if missing_mini:
                missing_descs = [el for (_, el) in missing_mini]
                # Use text content for MiniLM
                texts = [el.get("text", "") for el in missing_descs]
                new_mini_arr: np.ndarray = self.text_embedder.batch_encode_texts(texts)
                assert new_mini_arr.shape[1] == self._Q_DIM, f"MiniLM should output {self._Q_DIM}d, got {new_mini_arr.shape[1]}d"
                
                # Cache MiniLM embeddings
                mini_to_put = {h: new_mini_arr[i].astype(np.float32).tolist() 
                              for i, (h, _) in enumerate(missing_mini)}
                self.kv.batch_put_embeddings(mini_to_put, model_name="minilm")
                
                for i in range(new_mini_arr.shape[0]):
                    mini_vecs.append(new_mini_arr[i].astype(np.float32, copy=False))

            # Generate missing MarkupLM embeddings (768-d)
            if missing_markup:
                missing_descs = [el for (_, el) in missing_markup]
                new_markup_arr: np.ndarray = self.element_embedder.batch_encode(missing_descs)
                if new_markup_arr.ndim == 1:
                    new_markup_arr = new_markup_arr.reshape(1, -1)
                assert new_markup_arr.shape[1] == self._E_DIM, f"MarkupLM should output {self._E_DIM}d, got {new_markup_arr.shape[1]}d"
                
                # Cache MarkupLM embeddings
                markup_to_put = {h: new_markup_arr[i].astype(np.float32).tolist() 
                                for i, (h, _) in enumerate(missing_markup)}
                self.kv.batch_put_embeddings(markup_to_put, model_name="markuplm")
                
                for i in range(new_markup_arr.shape[0]):
                    markup_vecs.append(new_markup_arr[i].astype(np.float32, copy=False))

            # Add vectors to respective stores
            for i, (arr, el, h) in enumerate(zip(mini_vecs, descs, hashes)):
                # Support both 'attrs' and 'attributes' for compatibility
                attrs = el.get("attrs") or el.get("attributes") or {}
                
                meta = {
                    "hash": h,
                    "xpath": el.get("xpath") or "",
                    "tag": (el.get("tag") or "").lower(),
                    "role": (attrs.get("role") or "").lower(),
                    "visible": bool(el.get("visible")),
                    "frame_url": el.get("frame_url") or (el.get("meta") or {}).get("frame_url") or "",
                    "frame_hash": (el.get("meta") or {}).get("frame_hash", ""),
                    "text": el.get("text") or "",
                    "attributes": attrs,
                }
                
                # Add to MiniLM store (384-d)
                mini_store.add_vector(arr.astype(np.float32).tolist(), meta)
                
                # Add to MarkupLM store (768-d) - use corresponding MarkupLM vector
                if i < len(markup_vecs):
                    markup_store.add_vector(markup_vecs[i].astype(np.float32).tolist(), meta)
                
                frame_meta.append(meta)

            all_meta.extend(frame_meta)

        # Return MarkupLM vectors for final ranking (768-d)
        all_markup_vecs: List[np.ndarray] = []
        for fh in by_frame.keys():
            markup_store = self._markup_stores.get(fh)
            if markup_store:
                all_markup_vecs.extend([np.array(v, dtype=np.float32) for v in markup_store.vectors])
        
        E = np.vstack(all_markup_vecs).astype(np.float32, copy=False) if all_markup_vecs else np.zeros((0, self._E_DIM), dtype=np.float32)
        return E, all_meta

    def embed_query(self, text: str) -> np.ndarray:
        if not isinstance(text, str) or not text.strip():
            raise ValueError("query text must be a non-empty string")
        # Use MiniLM for query embedding (384-dim) - no padding needed
        q = self.text_embedder.encode_one(text)
        assert q.shape[0] == self._Q_DIM, f"Query should be {self._Q_DIM}d, got {q.shape[0]}d"
        return _l2norm(q)

    def _embed_query_markup(self, text: str) -> np.ndarray:
        """Embed query using MarkupLM for reranking (768-d)."""
        if not isinstance(text, str) or not text.strip():
            raise ValueError("query text must be a non-empty string")
        # Create a dummy element for MarkupLM embedding
        dummy_element = {"text": text, "tag": "query", "attributes": {}}
        q = self.element_embedder.encode(dummy_element)
        assert q.shape[0] == self._E_DIM, f"MarkupLM query should be {self._E_DIM}d, got {q.shape[0]}d"
        return _l2norm(q)

    def embed_elements(self, elements: List[Dict[str, Any]]) -> np.ndarray:
        E, _ = self._prepare_elements(elements)
        return E

    def query(
        self,
        query: str,
        elements: List[Dict[str, Any]],
        top_k: int = 20,
        *,
        page_sig: Optional[str] = None,
        frame_hash: Optional[str] = None,
        label_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        print(f"\n🔍 STEP 1: MiniLM Shortlist (384-d)")
        print(f"Query: '{query}'")
        print(f"Total elements available: {len(elements)}")
        
        if not isinstance(elements, list):
            raise ValueError("elements must be a list")
        if len(elements) == 0:
            print("❌ No elements provided")
            return {"results": [], "strategy": "hybrid-delta", "confidence": 0.0}

        # Prepare elements (creates both MiniLM and MarkupLM embeddings)
        E, meta = self._prepare_elements(elements)
        if E.size == 0:
            print("❌ No elements after preparation")
            return {"results": [], "strategy": "hybrid-delta", "confidence": 0.0}
        
        print(f"✅ Prepared {len(meta)} elements with both MiniLM and MarkupLM embeddings")
        
        # STEP 1: MiniLM shortlist (384-d)
        q_mini = self.embed_query(query)  # 384-d query
        print(f"✅ Query embedded with MiniLM, vector shape: {q_mini.shape}")
        
        # Search using MiniLM stores for shortlisting
        mini_hits: List[Tuple[float, Dict[str, Any]]] = []
        for fh, mini_store in self._mini_stores.items():
            k = max(10, int(top_k * 2))  # Get more candidates for reranking
            raw = mini_store.search(q_mini.tolist(), k=k)
            for idx, _dist, md in raw:
                vec = np.array(mini_store.vectors[idx], dtype=np.float32)
                score = _cos(q_mini, vec)
                mini_hits.append((score, md))

        print(f"🔍 MiniLM found {len(mini_hits)} candidates")
        print(f"🔍 Top {min(5, len(mini_hits))} MiniLM candidates:")
        for i, (score, meta) in enumerate(mini_hits[:5]):
            print(f"  {i+1}. Score: {score:.3f} | Tag: {meta.get('tag', '')} | Text: '{meta.get('text', '')[:50]}...'")

        if not mini_hits:
            print("❌ No hits from MiniLM shortlist")
            return {"results": [], "strategy": "hybrid-delta", "confidence": 0.0}

        # STEP 2: MarkupLM rerank (768-d)
        print(f"\n🎯 STEP 2: MarkupLM Rerank (768-d)")
        
        # Get top candidates from MiniLM shortlist
        mini_hits.sort(key=lambda x: x[0], reverse=True)
        shortlist = mini_hits[:min(20, len(mini_hits))]  # Top 20 for reranking
        
        print(f"🔍 Reranking {len(shortlist)} candidates with MarkupLM")
        
        # Re-embed query and shortlist with MarkupLM
        q_markup = self._embed_query_markup(query)  # 768-d query
        shortlist_elements = [meta for (_, meta) in shortlist]
        shortlist_embeddings = self.element_embedder.batch_encode(shortlist_elements)  # 768-d
        
        # Compute cosine similarity in 768-d space
        markup_scores: List[Tuple[float, Dict[str, Any]]] = []
        for i, (mini_score, meta) in enumerate(shortlist):
            if i < shortlist_embeddings.shape[0]:
                markup_vec = shortlist_embeddings[i]
                markup_score = _cos(q_markup, markup_vec)
                markup_scores.append((markup_score, meta))
        
        print(f"✅ MarkupLM reranking completed")
        print(f"🔍 Top {min(3, len(markup_scores))} MarkupLM candidates:")
        for i, (score, meta) in enumerate(markup_scores[:3]):
            print(f"  {i+1}. Score: {score:.3f} | Tag: {meta.get('tag', '')} | Text: '{meta.get('text', '')[:50]}...'")

        # Check for promotions
        promo_top: Optional[Dict[str, Any]] = None
        if page_sig and frame_hash and label_key:
            sel = lookup_promotion(self.kv, page_sig=page_sig, frame_hash=frame_hash, label_key=label_key)
            if sel:
                promo_top = {
                    "selector": sel,
                    "score": 1.0,
                    "reasons": ["promotion-hit"],
                    "meta": {"frame_hash": frame_hash, "promoted": True},
                }

        if not markup_scores and not promo_top:
            print("❌ No hits after MarkupLM reranking")
            return {"results": [], "strategy": "hybrid-delta", "confidence": 0.0}

        # Apply heuristics to final scores
        def _tag_bias(tag: str) -> float:
            tag = (tag or "").lower()
            if tag == "input":  return 0.08  # Highest priority for inputs
            if tag == "textarea": return 0.07  # High priority for textareas
            if tag == "a":      return 0.06  # High priority for links (navigation)
            if tag == "button": return 0.05  # High priority for buttons
            if tag == "select": return 0.03  # Medium priority for selects
            return 0.0

        def _role_bonus(role: str) -> float:
            role = (role or "").lower()
            if role in ("button", "link", "tab", "menuitem"):
                return 0.02  # Increased
            return 0.0
        
        def _clickable_bonus(meta: Dict[str, Any]) -> float:
            """Give bonus to elements that are likely clickable or interactive"""
            tag = (meta.get("tag") or "").lower()
            attrs = meta.get("attributes", {})

            # Special bonus for links with href (navigation elements)
            if tag == "a" and attrs.get("href"):
                return 0.5  # Maximum bonus for navigation links

            # Check for clickable indicators
            clickable_indicators = [
                "onclick", "href", "data-href", "data-link", "data-click",
                "data-action", "data-testid", "role", "tabindex"
            ]

            # If element has clickable attributes, give bonus
            if any(attr in attrs for attr in clickable_indicators):
                return 0.3  # High bonus for clickable attributes

            # If it's a known interactive tag
            if tag in ("button", "a", "input", "select", "textarea"):
                return 0.25  # Good bonus for interactive tags

            # If it has a role that suggests interactivity
            role = attrs.get("role", "").lower()
            if role in ("button", "link", "tab", "menuitem", "option", "textbox", "combobox"):
                return 0.2  # Medium bonus for interactive roles

            # Check for clickable classes
            classes = attrs.get("class", "").lower()
            clickable_classes = ["button", "btn", "link", "clickable", "action", "tile__clickable", "input", "search"]
            if any(cls in classes for cls in clickable_classes):
                return 0.15  # Small bonus for clickable classes

            return 0.0

        # Apply heuristics to MarkupLM scores
        ranked: List[Tuple[float, Dict[str, Any], List[str]]] = []
        for base_score, md in markup_scores:
            reasons: List[str] = [f"markup_cosine={base_score:.3f}"]
            b = _tag_bias(md.get("tag", "")) + _role_bonus(md.get("role", ""))
            
            # Add clickable bonus
            clickable_bonus = _clickable_bonus(md)
            if clickable_bonus > 0:
                b += clickable_bonus
                reasons.append(f"+clickable={clickable_bonus:.3f}")
            
            if b:
                reasons.append(f"+bias={b:.3f}")
            ranked.append((base_score + b, md, reasons))

        ranked.sort(key=lambda t: t[0], reverse=True)
        ranked = ranked[:top_k]

        print(f"\n🎯 STEP 3: Final Heuristic Scoring")
        print(f"🔍 Applied heuristics to {len(ranked)} MarkupLM candidates")
        print(f"Top {min(3, len(ranked))} final candidates:")
        for i, (score, md, reasons) in enumerate(ranked[:3]):
            print(f"  {i+1}. Final Score: {score:.3f} | Tag: {md.get('tag', '')} | Text: '{md.get('text', '')[:50]}...'")
            print(f"      XPath: {md.get('xpath', '')[:100]}...")
            print(f"      Reasons: {reasons}")

        results = []
        # Only add promotion if it's actually a good match
        if promo_top is not None:
            # Check if promoted element is clickable
            promo_meta = promo_top.get("meta", {})
            if _clickable_bonus(promo_meta) > 0 or promo_meta.get("tag", "").lower() in ("button", "a", "input", "select"):
                results.append(promo_top)
                print(f"✅ Using promoted element: {promo_top.get('selector', '')}")
            else:
                # If promotion is not clickable, don't use it
                print(f"❌ Promoted element not clickable, skipping")

        for score, md, reasons in ranked:
            sel = md.get("xpath") or ""
            results.append({
                "selector": sel,
                "score": float(score),
                "reasons": reasons,
                "meta": md,
            })

        head_score = 1.0 if promo_top is not None else (ranked[0][0] if ranked else 0.0)
        confidence = max(0.0, min(1.0, float(head_score)))

        return {
            "results": results[:top_k],
            "strategy": "hybrid-minilm-markuplm+promotion" if promo_top else "hybrid-minilm-markuplm",
            "confidence": confidence,
        }
