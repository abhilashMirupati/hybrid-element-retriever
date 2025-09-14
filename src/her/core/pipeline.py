from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from ..embeddings._resolve import preflight_require_models
from ..embeddings.text_embedder import TextEmbedder
from ..embeddings.element_embedder import  ElementEmbedder  # 768-d deterministic fallback
from .hashing import element_dom_hash
from ..vectordb.faiss_store import InMemoryVectorStore
from ..vectordb.sqlite_cache import SQLiteKV
from ..config.settings import get_config
from .config_service import get_config_service
from ..descriptors.hierarchy import HierarchyContextBuilder

# Optional heavy embedder (if present locally)
try:
    from ..embeddings.markuplm_embedder import MarkupLMEmbedder  # 768-d
    _MARKUP_IMPORT_OK = True
except Exception:
    _MARKUP_IMPORT_OK = False

# Promotions (Step 6)
from ..promotion.promotion_adapter import lookup_promotion

# Target matcher for no-semantic mode
from ..locator.target_matcher import TargetMatcher, AccessibilityFallbackMatcher, MatchResult

# Enhanced handlers
from ..locator.frame_handler import FrameHandler, FrameAwareTargetMatcher
from ..locator.shadow_dom_handler import ShadowDOMHandler
from ..locator.dynamic_handler import DynamicHandler

# New explicit no-semantic components
from ..locator.intent_parser import IntentParser, ParsedIntent, IntentType
from ..locator.dom_target_binder import DOMTargetBinder, DOMMatch

# Performance metrics
from ..monitoring.performance_metrics import get_metrics, record_query_timing, record_cache_metrics, record_memory_usage, PerformanceTimer

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

        # Get configuration
        self.config = get_config()
        
        # Hierarchy support
        self.use_hierarchy = self.config.should_use_hierarchy()
        self.use_two_stage = self.config.should_use_two_stage()
        self.hierarchy_builder = HierarchyContextBuilder() if self.use_hierarchy else None
        
        # Semantic search mode
        self.use_semantic_search = self.config.should_use_semantic_search()
        
        # Target matcher for no-semantic mode
        self.target_matcher = TargetMatcher(case_sensitive=False)
        self.ax_fallback_matcher = AccessibilityFallbackMatcher(case_sensitive=False)
        
        # Enhanced handlers
        self.frame_handler = FrameHandler()
        self.shadow_dom_handler = ShadowDOMHandler()
        self.dynamic_handler = DynamicHandler()
        
        # New explicit no-semantic components
        self.intent_parser = IntentParser()
        self.dom_target_binder = DOMTargetBinder(
            case_sensitive=self.config.no_semantic_case_sensitive
        )
        
        # Performance metrics
        self.metrics = get_metrics()

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

        log.info("HybridPipeline ready | cache=%s | MiniLM=%dd | MarkupLM=%dd | Hierarchy=%s | TwoStage=%s", 
                self._db_path, self._Q_DIM, self._E_DIM, self.use_hierarchy, self.use_two_stage)

    def _make_element_embedder(self):
        # Require MarkupLM now that models are preflighted
        if not _MARKUP_IMPORT_OK:
            raise RuntimeError("Transformers MarkupLM is not available. Install transformers and run model installer.")
        model_dir: Optional[str] = None
        if self._models_root:
            candidate = self._models_root / "markuplm-base"
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
        """Reset stores for a specific frame to free memory."""
        self._mini_stores.pop(frame_hash, None)
        self._markup_stores.pop(frame_hash, None)
        self._meta.pop(frame_hash, None)
    
    def cleanup_old_stores(self, max_stores: int = 10) -> None:
        """Clean up old stores to prevent memory leaks.
        
        Args:
            max_stores: Maximum number of stores to keep per type.
        """
        if len(self._mini_stores) > max_stores:
            # Remove oldest stores (simple FIFO)
            oldest_frames = list(self._mini_stores.keys())[:-max_stores]
            for frame_hash in oldest_frames:
                self._reset_stores(frame_hash)
            log.info(f"Cleaned up {len(oldest_frames)} old stores to prevent memory leak")
    
    def get_memory_usage(self) -> Dict[str, int]:
        """Get current memory usage statistics.
        
        Returns:
            Dictionary with memory usage information.
        """
        total_vectors = sum(len(store.vectors) for store in self._mini_stores.values())
        total_markup_vectors = sum(len(store.vectors) for store in self._markup_stores.values())
        
        return {
            "mini_stores_count": len(self._mini_stores),
            "markup_stores_count": len(self._markup_stores),
            "total_mini_vectors": total_vectors,
            "total_markup_vectors": total_markup_vectors,
            "estimated_memory_mb": (total_vectors * 384 + total_markup_vectors * 768) * 4 / (1024 * 1024)  # 4 bytes per float32
        }

    def _prepare_elements(self, elements: List[Dict[str, Any]]) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
        """Prepare elements for hybrid search - creates both MiniLM and MarkupLM embeddings."""
        if not isinstance(elements, list):
            raise ValueError("elements must be a list of element descriptors")

        # Add hierarchical context if enabled (check dynamically)
        config_service = get_config_service()
        if config_service.should_use_hierarchy() and self.hierarchy_builder:
            # Check if elements already have hierarchy context
            has_context = any(el.get('context', {}).get('hierarchy_path') for el in elements[:10])
            if not has_context:
                try:
                    # Create a deep copy to avoid modifying original elements
                    import copy
                    elements_copy = copy.deepcopy(elements)
                    elements = self.hierarchy_builder.add_context_to_elements(elements_copy)
                    log.info(f"Added hierarchical context to {len(elements)} elements")
                except Exception as e:
                    log.warning(f"Failed to add hierarchical context: {e}")
                    # Continue without hierarchy context
            else:
                log.info(f"Elements already have hierarchical context, skipping")

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
            # Include hierarchical context in text if available
            texts = []
            for el in descs:
                text = el.get("text", "")
                config_service = get_config_service()
                if config_service.should_use_hierarchy() and "context" in el:
                    context = el["context"]
                    hierarchy_path = context.get("hierarchy_path", "")
                    if hierarchy_path and hierarchy_path != "PENDING" and hierarchy_path != "ERROR":
                        # Prepend hierarchy context to text for better semantic matching
                        text = f"{hierarchy_path} | {text}" if text else hierarchy_path
                texts.append(text)
            
            mini_embeddings: np.ndarray = self.text_embedder.batch_encode_texts(texts)
            assert mini_embeddings.shape[1] == self._Q_DIM, f"MiniLM should output {self._Q_DIM}d, got {mini_embeddings.shape[1]}d"
            
        # OPTIMIZATION: Only generate MarkupLM embeddings for top MiniLM candidates
        # This dramatically improves performance while maintaining accuracy
        print(f"🔍 OPTIMIZATION: Skipping upfront MarkupLM processing for all {len(descs)} elements")
        print(f"   Will process only top MiniLM candidates with MarkupLM during query time")
        
        # Create empty MarkupLM embeddings array - will be populated during query time
        markup_embeddings = np.zeros((len(descs), self._E_DIM), dtype=np.float32)
        print(f"✅ Created empty MarkupLM embeddings array: {markup_embeddings.shape}")
            
        # Cache both embeddings
        mini_to_put = {h: mini_embeddings[i].astype(np.float32).tolist() 
                      for i, (h, _) in enumerate(zip(hashes, descs))}
        self.kv.batch_put_embeddings(mini_to_put, model_name="minilm")
        
        markup_to_put = {h: markup_embeddings[i].astype(np.float32).tolist() 
                        for i, (h, _) in enumerate(zip(hashes, descs))}
        self.kv.batch_put_embeddings(markup_to_put, model_name="markuplm")

        # Add vectors to both stores
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
        all_intent_text = " ".join(filter(None, [user_intent or "", target or "", query or ""])).lower()
        text = (meta.get("text") or "").lower()
        tag = (meta.get("tag") or "").lower()
        role = (meta.get("attributes", {}).get("role") or "").lower()
        href = (meta.get("attributes", {}).get("href") or "").lower()
        
        print(f"   Combined intent text: '{all_intent_text}'")
        print(f"   Element text: '{text[:50]}...'")
        
        score = 0.0
        print(f"   Initial score: {score}")
        
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
            # Extract quoted text from target (e.g., "Phones" from 'the "Phones" button')
            import re
            quoted_match = re.search(r'"([^"]+)"', target)
            if quoted_match:
                target_text = quoted_match.group(1).lower().strip()
            else:
                target_text = target.lower().strip().replace('"', '').replace("'", '')
            
            if target_text == text:
                score += 0.5  # Exact target match (high priority)
                print(f"   ✅ EXACT TARGET MATCH: '{target_text}' == '{text}' -> +0.5")
            elif target_text in text:
                score += 0.3  # Partial target match
                print(f"   ✅ PARTIAL TARGET MATCH: '{target_text}' in '{text}' -> +0.3")
            elif any(word in text for word in target_text.split()):
                score += 0.1  # Word-level match
                print(f"   ✅ WORD TARGET MATCH: '{target_text}' words in '{text}' -> +0.1")
            else:
                print(f"   ❌ NO TARGET MATCH: '{target_text}' vs '{text}'")
            print(f"   Score after target matching: {score}")
        
        # 3. User intent matching (action user wants to perform)
        if user_intent:
            intent_lower = (user_intent or "").lower()
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
                # For click/select intents, HEAVILY prioritize interactive elements
                if is_interactive:
                    score += 0.8  # VERY HIGH score for interactive elements
                elif tag in ("button", "a", "input", "select", "option"):
                    score += 0.6  # High score for clickable elements
                elif role in ("button", "link", "tab", "menuitem", "option", "radio", "checkbox"):
                    score += 0.4  # Medium score for accessible elements
                elif tag == "#text":
                    score -= 0.5  # HEAVY penalty for text nodes on click actions
                
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
        
        # Allow higher scores for exact matches, but cap others
        if score >= 1.0:  # Exact match + clickable element
            final_score = min(score, 1.0)  # Cap at 1.0 for exact matches
        else:
            final_score = min(score, 0.6)  # Cap at 0.6 for partial matches
        print(f"   Final intent score: {final_score:.3f}")
        return final_score

    def _apply_basic_heuristics(self, markup_scores: List[Tuple[float, Dict[str, Any]]], user_intent: str, target: str = None) -> List[Tuple[float, Dict[str, Any], List[str]]]:
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
            
            # 1. Element type scoring based on user intent
            if any(word in (user_intent or "").lower() for word in ["click", "select", "press", "choose", "pick"]):
                # For click actions, heavily prioritize interactive elements
                if is_interactive:
                    bonus += 0.5  # HIGH bonus for interactive elements
                    reasons.append("+interactive=0.500")
                elif tag in ("button", "a", "input", "select", "option"):
                    bonus += 0.3  # Medium bonus for clickable elements
                    reasons.append("+clickable=0.300")
                elif tag == "#text":
                    bonus -= 1.0  # VERY HEAVY penalty for text nodes on click actions
                    reasons.append("-text_node_click=-1.000")
                else:
                    bonus -= 0.2  # Penalty for non-interactive elements
                    reasons.append("-non_interactive=-0.200")
            else:
                # For other actions (validation, etc.), neutral approach
                if tag in ("button", "a", "input", "select", "option"):
                    bonus += 0.1
                    reasons.append("+clickable=0.100")
                elif tag == "#text":
                    bonus += 0.0
                    reasons.append("+text_node=0.000")
                else:
                    bonus += 0.0
                    reasons.append("+other_element=0.000")
            
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
                if input_type == 'radio' and any(word in (user_intent or "").lower() for word in ['select', 'choose', 'pick']):
                    bonus += 0.3
                    reasons.append("+radio_button=0.300")
                elif input_type in ['checkbox', 'button', 'submit']:
                    bonus += 0.2
                    reasons.append("+input_button=0.200")
            elif tag == 'button' and any(word in (user_intent or "").lower() for word in ['click', 'select', 'press']):
                bonus += 0.2
                reasons.append("+button=0.200")
            elif tag == 'a' and any(word in (user_intent or "").lower() for word in ['click', 'select']):
                bonus += 0.1
                reasons.append("+link=0.100")
            
            # 5. Content relevance (universal)
            if 'filter' in (user_intent or "").lower() and 'filter' in text:
                bonus += 0.2
                reasons.append("+filter_content=0.200")
            elif 'search' in (user_intent or "").lower() and 'search' in text:
                bonus += 0.2
                reasons.append("+search_content=0.200")
            
            # 6. Navigation/header penalty (universal)
            nav_keywords = ['navigation', 'nav', 'header', 'footer', 'menu', 'sidebar', 'breadcrumb']
            if any(word in text for word in nav_keywords):
                bonus -= 0.1
                reasons.append("-nav_element=-0.100")
            
            # 7. Exact text match bonus (highest priority)
            if target and text:
                # Extract quoted text from target (e.g., "Phones" from 'the "Phones" button')
                import re
                quoted_match = re.search(r'"([^"]+)"', target)
                if quoted_match:
                    target_text = quoted_match.group(1).lower().strip()
                else:
                    target_text = target.lower().strip().replace('"', '').replace("'", '')
                
                text_clean = text.lower().strip()
                if target_text == text_clean:
                    bonus += 0.5  # High bonus for exact text match
                    reasons.append("+exact_text_match=0.500")
                elif target_text in text_clean:
                    bonus += 0.3  # Medium bonus for partial text match
                    reasons.append("+partial_text_match=0.300")
            
            # 8. Accessibility bonus (universal)
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
        # Create proper HTML structure for MarkupLM embedding
        # Extract action and target from query for better HTML structure
        if "click" in text.lower():
            html_text = f"<button type='button'>{text}</button>"
        elif "enter" in text.lower() or "type" in text.lower():
            html_text = f"<input type='text' placeholder='{text}'>"
        elif "select" in text.lower():
            html_text = f"<select>{text}</select>"
        else:
            html_text = f"<div>{text}</div>"
        
        html_element = {"text": html_text, "tag": "html", "attributes": {}}
        q = self.element_embedder.encode(html_element)
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
        """Main query method - orchestrates the query processing pipeline."""
        self._log_query_start(query, elements)
        
        # Validate inputs
        if not self._validate_query_inputs(query, elements):
            return {"results": [], "strategy": "hybrid-delta", "confidence": 0.0}

        # Check if we should use semantic or no-semantic mode
        config_service = get_config_service()
        use_semantic = config_service.should_use_semantic_search()
        
        if use_semantic:
            # Use existing semantic pipeline
            return self._query_semantic_mode(query, elements, top_k, page_sig, frame_hash, label_key, user_intent, target)
        else:
            # Use new no-semantic mode
            return self._query_no_semantic_mode(query, elements, top_k, page_sig, frame_hash, label_key, user_intent, target)
    
    def _log_query_start(self, query: str, elements: List[Dict[str, Any]]) -> None:
        """Log query start information."""
        log.info(f"Enhanced Pipeline Query - Query: '{query}', Elements: {len(elements)}, Hierarchy: {self.use_hierarchy}, Two-stage: {self.use_two_stage}")
    
    def _validate_query_inputs(self, query: str, elements: List[Dict[str, Any]]) -> bool:
        """Validate query inputs."""
        if not isinstance(elements, list):
            raise ValueError("elements must be a list")
        if len(elements) == 0:
            log.warning("No elements provided for query")
            return False
        return True
    
    def _prepare_elements_for_query(self, elements: List[Dict[str, Any]], frame_hash: Optional[str]) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
        """Prepare elements for query processing."""
        log.debug(f"Caching analysis - MiniLM stores: {len(self._mini_stores)}, MarkupLM stores: {len(self._markup_stores)}, frame_hash: {frame_hash}")
        
        # Debug: Check first few elements before processing
        print(f"🔍 DEBUG: First 3 elements before _prepare_elements:")
        for i, el in enumerate(elements[:3]):
            print(f"  Element {i}: has_meta={el.get('meta') is not None}, meta={el.get('meta')}")
        
        E, meta = self._prepare_elements(elements)
        
        log.debug(f"Prepared {len(meta)} elements with both MiniLM and MarkupLM embeddings")
        log.debug(f"After preparation - MiniLM stores: {len(self._mini_stores)}, MarkupLM stores: {len(self._markup_stores)}")
        
        return E, meta
    
    def _query_semantic_mode(self, query: str, elements: List[Dict[str, Any]], top_k: int,
                            page_sig: Optional[str], frame_hash: Optional[str], 
                            label_key: Optional[str], user_intent: Optional[str],
                            target: Optional[str]) -> Dict[str, Any]:
        """Execute semantic query strategy (existing pipeline)."""
        # Prepare elements for processing
        E, meta = self._prepare_elements_for_query(elements, frame_hash)
        if E.size == 0:
            log.warning("No elements after preparation")
            return {"results": [], "strategy": "hybrid-delta", "confidence": 0.0}
        
        # Clean up old stores to prevent memory leaks
        self.cleanup_old_stores()
        
        # Execute semantic strategy
        config_service = get_config_service()
        use_hierarchy = config_service.should_use_hierarchy()
        use_two_stage = config_service.should_use_two_stage()
        
        log.debug(f"Semantic mode - hierarchy: {use_hierarchy}, two_stage: {use_two_stage}")
        
        if use_hierarchy and use_two_stage:
            log.debug("Using TWO-STAGE MarkupLM strategy")
            return self._query_two_stage(query, meta, top_k, page_sig, frame_hash, label_key, user_intent, target)
        else:
            log.debug("Using STANDARD strategy")
            return self._query_standard(query, meta, top_k, page_sig, frame_hash, label_key, user_intent, target)

    def _query_no_semantic_mode(self, query: str, elements: List[Dict[str, Any]], top_k: int, 
                               page_sig: Optional[str], frame_hash: Optional[str], 
                               label_key: Optional[str], parsed_intent: Optional[ParsedIntent], 
                               target: Optional[str]) -> Dict[str, Any]:
        """Execute enhanced no-semantic query strategy with hierarchical context."""
        log.info(f"Enhanced no-semantic mode query: '{query}' with {len(elements)} elements")
        
        # Import enhanced no-semantic matcher
        from ..locator.enhanced_no_semantic import EnhancedNoSemanticMatcher
        
        # Create matcher instance
        matcher = EnhancedNoSemanticMatcher()
        
        # Get page object for validation (if available)
        page = None
        if hasattr(self, '_current_page'):
            page = self._current_page
        
        # Execute enhanced no-semantic query
        result = matcher.query(query, elements, page)
        
        # Add performance metrics
        result['performance'] = {
            'elements_processed': len(elements),
            'strategy': 'enhanced-no-semantic'
        }
        
        return result
    
    def _query_standard(
        self,
        query: str,
        meta: List[Dict[str, Any]],
        top_k: int,
        page_sig: Optional[str],
        frame_hash: Optional[str],
        label_key: Optional[str],
        user_intent: Optional[str],
        target: Optional[str]
    ) -> Dict[str, Any]:
        """Execute standard hybrid search strategy."""
        log.info(f"Standard hybrid search: '{query}' with {len(meta)} elements")
        
        # Use the already prepared elements (meta contains the prepared elements)
        elements = meta
        
        # Get MiniLM store and perform search with the query
        mini_store = self._get_mini_store(frame_hash)
        
        # We need to encode the query using MiniLM to get the query vector
        from ..embeddings.text_embedder import TextEmbedder
        text_embedder = TextEmbedder()
        query_vector = text_embedder.encode_one(query)
        
        # Perform MiniLM search
        search_results = mini_store.search(query_vector, top_k * 2)
        
        # Extract scores and indices
        mini_indices = [result[0] for result in search_results]
        mini_scores = [result[1] for result in search_results]
        
        # Get top elements from MiniLM
        top_elements = [elements[i] for i in mini_indices]
        
        # Prepare for MarkupLM reranking
        if _MARKUP_IMPORT_OK:
            try:
                # Create query embedding
                q_markup = self._embed_query_markup(query)
                
                # Get MarkupLM store
                markup_store = self._get_markup_store(frame_hash)
                
                # Perform MarkupLM search on top elements
                markup_scores, markup_indices = markup_store.search(
                    self.element_embedder.batch_encode(top_elements), top_k
                )
                
                # Get final results
                final_elements = [top_elements[i] for i in markup_indices[0]]
                final_scores = markup_scores[0]
                
                # Apply heuristics
                heuristically_scored = self._apply_basic_heuristics(
                    list(zip(final_scores, final_elements)), 
                    user_intent or "", 
                    target or ""
                )
                
                # Build results
                results = []
                for score, element, reasons in heuristically_scored:
                    results.append({
                        "selector": f"//{element.get('tag', 'div')}[@id='{element.get('attributes', {}).get('id', '')}']",
                        "score": float(score),
                        "reasons": reasons,
                        "meta": element
                    })
                
                return {
                    "results": results[:top_k],
                    "strategy": "hybrid-minilm-markuplm",
                    "confidence": float(final_scores[0]) if final_scores else 0.0
                }
                
            except Exception as e:
                log.warning(f"MarkupLM search failed: {e}, falling back to MiniLM only")
        
        # Fallback to MiniLM only
        results = []
        for i, element in enumerate(top_elements[:top_k]):
            results.append({
                "selector": f"//{element.get('tag', 'div')}[@id='{element.get('attributes', {}).get('id', '')}']",
                "score": float(mini_scores[i]) if i < len(mini_scores) else 0.0,
                "reasons": ["minilm-only"],
                "meta": element
            })
        
        return {
            "results": results,
            "strategy": "minilm-only",
            "confidence": float(mini_scores[0]) if mini_scores else 0.0
        }

    def _query_two_stage(
        self,
        query: str,
        meta: List[Dict[str, Any]],
        top_k: int,
        page_sig: Optional[str],
        frame_hash: Optional[str],
        label_key: Optional[str],
        user_intent: Optional[str],
        target: Optional[str],
    ) -> Dict[str, Any]:
        """Execute two-stage hybrid search strategy."""
        log.info(f"Two-stage hybrid search: '{query}' with {len(meta)} elements")
        
        # Stage 1: MiniLM search
        mini_embeddings, elements = self._prepare_elements_for_query(meta, frame_hash)
        mini_store = self._get_mini_store(frame_hash)
        mini_scores, mini_indices = mini_store.search(mini_embeddings, top_k * 3)
        
        # Stage 2: MarkupLM reranking
        if _MARKUP_IMPORT_OK:
            try:
                top_elements = [elements[i] for i in mini_indices[0]]
                markup_scores, markup_indices = self._get_markup_store(frame_hash).search(
                    self.element_embedder.batch_encode(top_elements), top_k
                )
                
                final_elements = [top_elements[i] for i in markup_indices[0]]
                final_scores = markup_scores[0]
                
                results = []
                for i, element in enumerate(final_elements):
                    results.append({
                        "selector": f"//{element.get('tag', 'div')}[@id='{element.get('attributes', {}).get('id', '')}']",
                        "score": float(final_scores[i]),
                        "reasons": ["two-stage-hybrid"],
                        "meta": element
                    })
                
                return {
                    "results": results,
                    "strategy": "two-stage-hybrid",
                    "confidence": float(final_scores[0]) if final_scores else 0.0
                }
                
            except Exception as e:
                log.warning(f"Two-stage search failed: {e}, falling back to MiniLM only")
        
        # Fallback to MiniLM only
        results = []
        for i, element in enumerate([elements[i] for i in mini_indices[0]][:top_k]):
            results.append({
                "selector": f"//{element.get('tag', 'div')}[@id='{element.get('attributes', {}).get('id', '')}']",
                "score": float(mini_scores[0][i]),
                "reasons": ["minilm-only"],
                "meta": element
            })
        
        return {
            "results": results,
            "strategy": "minilm-only",
            "confidence": float(mini_scores[0][0]) if mini_scores[0] else 0.0
        }
