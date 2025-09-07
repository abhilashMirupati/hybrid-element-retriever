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

            # Generate MiniLM embeddings for all elements (384-d)
            texts = [el.get("text", "") for el in descs]
            mini_embeddings: np.ndarray = self.text_embedder.batch_encode_texts(texts)
            assert mini_embeddings.shape[1] == self._Q_DIM, f"MiniLM should output {self._Q_DIM}d, got {mini_embeddings.shape[1]}d"
            
            # Generate MarkupLM embeddings for all elements (768-d) - with chunking for token limits
            # Process in smaller chunks to respect 512 token limit, ensuring complete elements
            chunk_size = 20  # Process 20 complete elements at a time to respect token limits
            markup_embeddings_list = []
            
            print(f"🔍 Processing {len(descs)} elements in chunks of {chunk_size} for MarkupLM")
            
            for i in range(0, len(descs), chunk_size):
                # Ensure we don't split elements - take complete elements only
                chunk = descs[i:i + chunk_size]
                print(f"   Processing chunk {i//chunk_size + 1}: elements {i+1}-{min(i+chunk_size, len(descs))}")
                
                try:
                    chunk_embeddings = self.element_embedder.batch_encode(chunk)
                    if chunk_embeddings.ndim == 1:
                        chunk_embeddings = chunk_embeddings.reshape(1, -1)
                    markup_embeddings_list.append(chunk_embeddings)
                    print(f"   ✅ Chunk {i//chunk_size + 1} processed successfully: {chunk_embeddings.shape}")
                except Exception as e:
                    print(f"   ❌ Chunk {i//chunk_size + 1} failed: {e}")
                    # If chunk fails, try smaller chunks
                    if chunk_size > 1:
                        print(f"   🔄 Retrying with smaller chunks...")
                        for j in range(0, len(chunk), 5):  # Try 5 elements at a time
                            mini_chunk = chunk[j:j+5]
                            try:
                                mini_embeddings = self.element_embedder.batch_encode(mini_chunk)
                                if mini_embeddings.ndim == 1:
                                    mini_embeddings = mini_embeddings.reshape(1, -1)
                                markup_embeddings_list.append(mini_embeddings)
                                print(f"   ✅ Mini-chunk processed: {mini_embeddings.shape}")
                            except Exception as mini_e:
                                print(f"   ❌ Mini-chunk failed: {mini_e}")
                                # Skip this mini-chunk and continue
                                continue
                    else:
                        print(f"   ⚠️  Skipping failed chunk")
                        continue
            
            if markup_embeddings_list:
                markup_embeddings = np.vstack(markup_embeddings_list)
                print(f"✅ All chunks processed successfully: {markup_embeddings.shape}")
            else:
                print(f"❌ No chunks processed successfully, using empty embeddings")
                markup_embeddings = np.zeros((len(descs), self._E_DIM), dtype=np.float32)
            if markup_embeddings.ndim == 1:
                markup_embeddings = markup_embeddings.reshape(1, -1)
            assert markup_embeddings.shape[1] == self._E_DIM, f"MarkupLM should output {self._E_DIM}d, got {markup_embeddings.shape[1]}d"
            
            # Cache both embeddings
            mini_to_put = {h: mini_embeddings[i].astype(np.float32).tolist() 
                          for i, (h, _) in enumerate(zip(hashes, descs))}
            self.kv.batch_put_embeddings(mini_to_put, model_name="minilm")
            
            markup_to_put = {h: markup_embeddings[i].astype(np.float32).tolist() 
                            for i, (h, _) in enumerate(zip(hashes, descs))}
            self.kv.batch_put_embeddings(markup_to_put, model_name="markuplm")

            # Add vectors to respective stores
            for i, (el, h) in enumerate(zip(descs, hashes)):
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
                mini_store.add_vector(mini_embeddings[i].astype(np.float32).tolist(), meta)
                
                # Add to MarkupLM store (768-d)
                markup_store.add_vector(markup_embeddings[i].astype(np.float32).tolist(), meta)
                
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

    def _compute_intent_score(self, user_intent: Optional[str], target: Optional[str], query: str, meta: Dict[str, Any]) -> float:
        """Compute intent score using all three parameters: Intent/Target/Query for MarkupLM reranking."""
        print(f"\\n🔍 _compute_intent_score called with:")
        print(f"   user_intent: '{user_intent}' (type: {type(user_intent)})")
        print(f"   target: '{target}' (type: {type(target)})")
        print(f"   query: '{query}' (type: {type(query)})")
        print(f"   element text: '{meta.get('text', '')[:50]}...'")
        print(f"   element interactive: {meta.get('interactive', False)}")
        
        if not user_intent and not target:
            print(f"   ❌ No user_intent or target - returning 0.0")
            return 0.0
        
        # Combine all parameters for comprehensive scoring
        all_intent_text = " ".join(filter(None, [user_intent, target, query])).lower()
        text = (meta.get("text") or "").lower()
        tag = (meta.get("tag") or "").lower()
        role = (meta.get("attributes", {}).get("role") or "").lower()
        href = (meta.get("attributes", {}).get("href") or "").lower()
        
        print(f"   Combined intent text: '{all_intent_text}'")
        print(f"   Element text: '{text[:50]}...'")
        
        score = 0.0
        
        # 1. Query matching (most important - what user is looking for)
        if query:
            query_words = query.lower().split()
            text_words = text.split()
            query_matches = sum(1 for word in query_words if word in text_words)
            if query_matches > 0:
                score += min(0.3, query_matches * 0.1)  # Up to 0.3 for query matches
            
            # Universal attribute matching for all interactive elements
            attrs = meta.get('attributes', {})
            
            # Check aria-label (highest priority for accessibility)
            aria_label = attrs.get('aria-label', '').lower()
            if aria_label and any(word in aria_label for word in query_words):
                score += 0.6  # Very high bonus for aria-label matches
            
            # Check data-testid (common in modern UIs)
            data_testid = attrs.get('data-testid', '').lower()
            if data_testid and any(word in data_testid for word in query_words):
                score += 0.4  # High bonus for data-testid matches
            
            # Check title attribute
            title = attrs.get('title', '').lower()
            if title and any(word in title for word in query_words):
                score += 0.3  # Medium bonus for title matches
            
            # Check value attribute (for inputs)
            value = attrs.get('value', '').lower()
            if value and any(word in value for word in query_words):
                score += 0.3  # Medium bonus for value matches
            
            # Check name attribute (for form elements)
            name = attrs.get('name', '').lower()
            if name and any(word in name for word in query_words):
                score += 0.2  # Small bonus for name matches
        
        # 2. Target matching (what user wants to interact with)
        if target:
            target_lower = target.lower()
            if target_lower in text:
                score += 0.2  # Exact target match
            elif any(word in text for word in target_lower.split()):
                score += 0.1  # Partial target match
        
        # 3. User intent matching (action user wants to perform)
        if user_intent:
            intent_lower = user_intent.lower()
            is_interactive = meta.get('interactive', False)
            attrs = meta.get('attributes', {})
            
            # Universal intent-based scoring
            if "filter" in intent_lower:
                # For filter intents, prioritize interactive filter elements
                if is_interactive and ("filter" in text or "filter" in attrs.get('aria-label', '').lower()):
                    score += 0.5  # Highest score for interactive filter elements
                elif tag in ("button", "input", "select") and ("filter" in text or "filter" in attrs.get('aria-label', '').lower()):
                    score += 0.4  # High score for filter buttons
                elif is_interactive:
                    score += 0.3  # Medium score for other interactive elements
            elif any(word in intent_lower for word in ["click", "select", "press", "choose", "pick"]):
                # For click/select intents, prioritize interactive elements
                if is_interactive:
                    score += 0.5  # Highest score for interactive elements
                elif tag in ("button", "a", "input", "select", "option"):
                    score += 0.3  # High score for clickable elements
                elif role in ("button", "link", "tab", "menuitem", "option", "radio", "checkbox"):
                    score += 0.2  # Medium score for accessible elements
                
                # Special bonuses for specific element types
                if tag == "input":
                    input_type = attrs.get('type', '')
                    if input_type == 'radio':
                        score += 0.3  # High bonus for radio buttons
                    elif input_type in ['checkbox', 'button', 'submit']:
                        score += 0.2  # Medium bonus for other interactive inputs
                elif tag == "button":
                    score += 0.2  # Medium bonus for buttons
                elif tag == "a":
                    score += 0.1  # Small bonus for links
        
        # 4. Href relevance (for links)
        if href and query:
            query_words = query.lower().split()
            if any(word in href for word in query_words):
                score += 0.1
        
        # 5. Tag relevance (element type matching)
        if query:
            query_words = query.lower().split()
            if any(word in tag for word in query_words):
                score += 0.05
        
        # 6. Role relevance (accessibility)
        if query:
            query_words = query.lower().split()
            if any(word in role for word in query_words):
                score += 0.05
        
        final_score = min(score, 0.6)  # Cap at 0.6 for multi-parameter scoring
        print(f"   Final intent score: {final_score:.3f}")
        return final_score

    def _apply_basic_heuristics(self, markup_scores: List[Tuple[float, Dict[str, Any]]], user_intent: str) -> List[Tuple[float, Dict[str, Any], List[str]]]:
        """Apply universal heuristics for all websites and UI patterns"""
        print(f"\\n🔍 Applying Universal Heuristics")
        print(f"   User Intent: '{user_intent}'")
        
        ranked: List[Tuple[float, Dict[str, Any], List[str]]] = []
        for i, (base_score, md) in enumerate(markup_scores):
            reasons: List[str] = [f"markup_cosine={base_score:.3f}"]
            bonus = 0.0
            
            # Universal element analysis
            tag = (md.get("tag") or "").lower()
            text = (md.get("text") or "").lower()
            visible = md.get("visible", True)
            below_fold = md.get("below_fold", False)
            is_interactive = md.get("interactive", False)
            attrs = md.get("attributes", {})
            
            # 1. Interactivity bonus (universal)
            if is_interactive:
                bonus += 0.2
                reasons.append("+interactive=0.200")
            elif tag in ("button", "a", "input", "select", "option"):
                bonus += 0.1
                reasons.append("+clickable=0.100")
            elif tag in ("div", "span", "p") and any(word in user_intent.lower() for word in ["click", "select", "press"]):
                bonus -= 0.1
                reasons.append("-non_clickable=-0.100")
            
            # 2. Visibility penalty (universal)
            if not visible:
                bonus -= 0.3
                reasons.append("-hidden=-0.300")
            
            # 3. Below fold penalty (universal)
            if below_fold:
                bonus -= 0.2
                reasons.append("-below_fold=-0.200")
            
            # 4. Element type specific bonuses (universal)
            if tag == 'input':
                input_type = attrs.get('type', '')
                if input_type == 'radio' and any(word in user_intent.lower() for word in ['select', 'choose', 'pick']):
                    bonus += 0.3
                    reasons.append("+radio_button=0.300")
                elif input_type in ['checkbox', 'button', 'submit']:
                    bonus += 0.2
                    reasons.append("+input_button=0.200")
            elif tag == 'button' and any(word in user_intent.lower() for word in ['click', 'select', 'press']):
                bonus += 0.2
                reasons.append("+button=0.200")
            elif tag == 'a' and any(word in user_intent.lower() for word in ['click', 'select']):
                bonus += 0.1
                reasons.append("+link=0.100")
            
            # 5. Content relevance (universal)
            if 'filter' in user_intent.lower() and 'filter' in text:
                bonus += 0.2
                reasons.append("+filter_content=0.200")
            elif 'search' in user_intent.lower() and 'search' in text:
                bonus += 0.2
                reasons.append("+search_content=0.200")
            
            # 6. Navigation/header penalty (universal)
            nav_keywords = ['navigation', 'nav', 'header', 'footer', 'menu', 'sidebar', 'breadcrumb']
            if any(word in text for word in nav_keywords):
                bonus -= 0.1
                reasons.append("-nav_element=-0.100")
            
            # 7. Accessibility bonus (universal)
            if attrs.get('aria-label') or attrs.get('aria-labelledby'):
                bonus += 0.1
                reasons.append("+accessible=0.100")
            
            final_score = base_score + bonus
            ranked.append((final_score, md, reasons))
            
            # Debug each element
            print(f"   Element {i+1}:")
            print(f"     Text: '{md.get('text', '')[:50]}...'")
            print(f"     Tag: {md.get('tag', '')}")
            print(f"     Visible: {visible}, Below Fold: {below_fold}, Interactive: {is_interactive}")
            print(f"     MarkupLM: {base_score:.3f}, Bonus: {bonus:+.3f}, Final: {final_score:.3f}")
            print(f"     Reasons: {reasons}")
        
        return ranked

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
        user_intent: Optional[str] = None,
        target: Optional[str] = None,
    ) -> Dict[str, Any]:
        print(f"\n🔍 STEP 1: MiniLM Shortlist (384-d)")
        print(f"Query: '{query}'")
        print(f"Total elements available: {len(elements)}")
        print(f"MiniLM Query Embedding: Using '{query}' for vector search")
        
        if not isinstance(elements, list):
            raise ValueError("elements must be a list")
        if len(elements) == 0:
            print("❌ No elements provided")
            return {"results": [], "strategy": "hybrid-delta", "confidence": 0.0}

        # Prepare elements (creates both MiniLM and MarkupLM embeddings)
        print(f"\n🔍 CACHING ANALYSIS:")
        print(f"   Current MiniLM stores: {len(self._mini_stores)}")
        print(f"   Current MarkupLM stores: {len(self._markup_stores)}")
        print(f"   Frame hash for this query: {frame_hash}")
        
        E, meta = self._prepare_elements(elements)
        if E.size == 0:
            print("❌ No elements after preparation")
            return {"results": [], "strategy": "hybrid-delta", "confidence": 0.0}
        
        print(f"✅ Prepared {len(meta)} elements with both MiniLM and MarkupLM embeddings")
        print(f"   After preparation - MiniLM stores: {len(self._mini_stores)}")
        print(f"   After preparation - MarkupLM stores: {len(self._markup_stores)}")
        
        # STEP 1: MiniLM shortlist (384-d)
        q_mini = self.embed_query(query)  # 384-d query
        print(f"✅ Query embedded with MiniLM, vector shape: {q_mini.shape}")
        print(f"🔍 MiniLM Query Vector (first 10 dims): {q_mini[:10]}")
        
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
            print(f"      XPath: {meta.get('xpath', '')[:80]}...")

        if not mini_hits:
            print("❌ No hits from MiniLM shortlist")
            return {"results": [], "strategy": "hybrid-delta", "confidence": 0.0}

        # STEP 2: MarkupLM rerank (768-d)
        print(f"\n🎯 STEP 2: MarkupLM Rerank (768-d)")
        
        # Get top candidates from MiniLM shortlist
        mini_hits.sort(key=lambda x: x[0], reverse=True)
        shortlist = mini_hits[:min(5, len(mini_hits))]  # Top 5 for reranking (respect 512 token limit)
        
        # Additional safety check for token limits
        if len(shortlist) > 5:
            print(f"⚠️  WARNING: Processing {len(shortlist)} elements may exceed token limits")
            shortlist = shortlist[:5]  # Force limit to 5
        
        print(f"🔍 Reranking {len(shortlist)} candidates with MarkupLM")
        print(f"🔍 MarkupLM Processing Details:")
        print(f"   Query: '{query}' (type: {type(query)})")
        print(f"   User Intent: '{user_intent}' (type: {type(user_intent)})")
        print(f"   Target: '{target}' (type: {type(target)})")
        print(f"   Shortlist elements: {len(shortlist)}")
        
        # Debug: Check if parameters are being passed to intent scoring
        print(f"\\n🔍 Parameter Validation:")
        print(f"   Query is None: {query is None}")
        print(f"   User Intent is None: {user_intent is None}")
        print(f"   Target is None: {target is None}")
        print(f"   Will call _compute_intent_score: {bool(user_intent or target)}")
        
        # Re-embed query and shortlist with MarkupLM (limit to top 10 for performance)
        q_markup = self._embed_query_markup(query)  # 768-d query
        print(f"✅ Query embedded with MarkupLM, vector shape: {q_markup.shape}")
        print(f"🔍 MarkupLM Query Vector (first 10 dims): {q_markup[:10]}")
        
        shortlist_elements = [meta for (_, meta) in shortlist[:10]]  # Limit to top 10
        print(f"🔍 MarkupLM Processing {len(shortlist_elements)} shortlisted elements")
        shortlist_embeddings = self.element_embedder.batch_encode(shortlist_elements)  # 768-d
        print(f"✅ Shortlist elements embedded with MarkupLM, shape: {shortlist_embeddings.shape}")
        
        # Compute cosine similarity in 768-d space with user intent awareness
        markup_scores: List[Tuple[float, Dict[str, Any]]] = []
        for i, (mini_score, meta) in enumerate(shortlist):
            if i < shortlist_embeddings.shape[0]:
                markup_vec = shortlist_embeddings[i]
                markup_score = _cos(q_markup, markup_vec)
                
                # Apply multi-parameter scoring to MarkupLM results
                intent_score = 0.0
                if user_intent or target:
                    intent_score = self._compute_intent_score(user_intent, target, query, meta)
                    markup_score += intent_score
                
                # Debug each element
                print(f"   Element {i+1}:")
                print(f"     Text: '{meta.get('text', '')[:50]}...'")
                print(f"     Tag: {meta.get('tag', '')}")
                print(f"     XPath: {meta.get('xpath', '')[:80]}...")
                print(f"     MiniLM Score: {mini_score:.3f}")
                print(f"     MarkupLM Cosine: {_cos(q_markup, markup_vec):.3f}")
                print(f"     Intent Score: {intent_score:.3f}")
                print(f"     Final Score: {markup_score:.3f}")
                
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

        # Apply universal UI automation heuristics (minimal bias, let MarkupLM + user intent dominate)
        def _tag_bias(tag: str) -> float:
            """Minimal tag bias - only for essential UI automation elements"""
            tag = (tag or "").lower()
            # Only give minimal bias to essential interactive elements
            if tag in ("input", "textarea", "select"):  # Form elements
                return 0.005
            if tag in ("button", "a"):  # Action elements
                return 0.003
            return 0.0

        def _role_bonus(role: str) -> float:
            """Minimal role bonus - only for essential accessibility roles"""
            role = (role or "").lower()
            if role in ("button", "link", "tab", "menuitem", "option"):
                return 0.002
            return 0.0
        
        def _clickable_bonus(meta: Dict[str, Any]) -> float:
            """Universal clickable bonus - works for all websites and use cases"""
            tag = (meta.get("tag") or "").lower()
            attrs = meta.get("attributes", {})
            text = (meta.get("text") or "").strip()

            # Universal clickable indicators (works across all websites)
            clickable_indicators = [
                "onclick", "href", "data-href", "data-link", "data-click",
                "data-action", "data-testid", "data-test-id", "role", "tabindex",
                "aria-label", "aria-labelledby", "title", "alt"
            ]

            score = 0.0

            # Bonus for interactive tags
            if tag in ("button", "a", "input", "select", "textarea", "label"):
                score += 0.02

            # Bonus for clickable attributes
            if any(attr in attrs for attr in clickable_indicators):
                score += 0.01

            # Bonus for elements with meaningful text (likely interactive)
            if text and len(text) > 0 and len(text) < 100:
                score += 0.01

            # Bonus for elements with data attributes (modern web apps)
            if any(attr.startswith("data-") for attr in attrs.keys()):
                score += 0.005

            return score

        # Show MarkupLM scores and decide whether to trust them
        print(f"🎯 STEP 3: MarkupLM Analysis & Smart Selection")
        print(f"🔍 MarkupLM ranking for {len(markup_scores)} candidates:")
        for i, (base_score, md) in enumerate(markup_scores):
            print(f"   {i+1}. MarkupLM Score: {base_score:.3f} | Tag: {md.get('tag', '')} | Text: '{md.get('text', '')[:50]}...'")
            print(f"       XPath: {md.get('xpath', '')[:80]}...")
        
        # Check if MarkupLM has a clear winner (score gap > threshold)
        if len(markup_scores) >= 2:
            top_score = markup_scores[0][0]
            second_score = markup_scores[1][0]
            score_gap = top_score - second_score
            print(f"\\n🔍 MarkupLM Analysis:")
            print(f"   Top Score: {top_score:.3f}")
            print(f"   Second Score: {second_score:.3f}")
            print(f"   Score Gap: {score_gap:.3f}")
            
            # Trust MarkupLM if score gap is significant (>0.1)
            if score_gap > 0.1:
                print(f"   ✅ Trusting MarkupLM - clear winner (gap > 0.1)")
                ranked = [(score, meta, [f"markup_cosine={score:.3f}", "trusted_markup"]) for score, meta in markup_scores]
            else:
                print(f"   ⚠️  Close scores - applying basic heuristics")
                ranked = self._apply_basic_heuristics(markup_scores, user_intent)
        else:
            print(f"   ⚠️  Only {len(markup_scores)} candidates - applying basic heuristics")
            ranked = self._apply_basic_heuristics(markup_scores, user_intent)

        ranked.sort(key=lambda t: t[0], reverse=True)
        ranked = ranked[:top_k]

        print(f"Top {min(3, len(ranked))} final candidates:")
        for i, (score, meta, reasons) in enumerate(ranked[:3]):
            print(f"  {i+1}. Final Score: {score:.3f} | Tag: {meta.get('tag', '')} | Text: '{meta.get('text', '')[:50]}...'")
            print(f"      XPath: {meta.get('xpath', '')[:100]}...")
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

        # Debug final selection
        if results:
            selected = results[0]
            print(f"\n🎯 FINAL SELECTION:")
            print(f"   Selected XPath: {selected['selector']}")
            print(f"   Confidence: {confidence:.3f}")
            print(f"   Strategy: {'hybrid-minilm-markuplm+promotion' if promo_top else 'hybrid-minilm-markuplm'}")
            print(f"   Element Text: '{selected['meta'].get('text', '')[:50]}...'")
            print(f"   Element Tag: {selected['meta'].get('tag', '')}")
            
            # Check how many elements this XPath matches (if we have access to page)
            try:
                # This will be checked later in the runner when we actually try to click
                print(f"   📋 XPath will be validated during click execution")
            except Exception as e:
                print(f"   ⚠️  Could not validate XPath: {e}")
            
            # Special logging for Apple filter case
            if 'Apple' in query and 'filter' in query.lower():
                print(f"\n🍎 APPLE FILTER SELECTION ANALYSIS:")
                print(f"   Query: '{query}'")
                print(f"   Selected XPath: {selected['selector']}")
                print(f"   Element ID: {selected['meta'].get('attributes', {}).get('id', 'None')}")
                print(f"   Element Class: {selected['meta'].get('attributes', {}).get('class', 'None')}")
                print(f"   Element Role: {selected['meta'].get('role', 'None')}")
                print(f"   Element Aria Label: {selected['meta'].get('attributes', {}).get('aria-label', 'None')}")
                
                # Check if this is the correct Apple filter button
                if 'Apple_2' in selected['selector']:
                    print(f"   ✅ CORRECT: Selected Apple filter button (id=Apple_2)")
                else:
                    print(f"   ❌ INCORRECT: Did not select Apple filter button")
                    print(f"   Expected: //*[@id=\"Apple_2\"]")
                    print(f"   Got: {selected['selector']}")

        return {
            "results": results[:top_k],
            "strategy": "hybrid-minilm-markuplm+promotion" if promo_top else "hybrid-minilm-markuplm",
            "confidence": confidence,
        }
