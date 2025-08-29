"""Enhanced session management with cold start, incremental updates, and SPA support."""

from typing import Any, Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
import json
import pickle
import hashlib
from pathlib import Path

from ..bridge.snapshot import capture_snapshot, detect_dom_change
try:
    from ..embeddings.element_embedder import ElementEmbedder
except ImportError:
    # Fallback if numpy not available
    class ElementEmbedder:
        def embed(self, descriptor): return [0.0] * 768
        def embed_batch(self, descriptors): return [[0.0] * 768 for _ in descriptors]
from ..vectordb.faiss_store import InMemoryVectorStore
from ..vectordb.sqlite_cache import SQLiteKV
from ..utils.cache import LRUCache

logger = logging.getLogger(__name__)

try:
    from playwright.sync_api import Page, Browser, BrowserContext
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    Page = Any
    Browser = Any
    BrowserContext = Any
    PLAYWRIGHT_AVAILABLE = False


@dataclass
class EnhancedSessionState:
    """Enhanced state for a single browser session."""

    session_id: str
    created_at: datetime = field(default_factory=datetime.now)
    last_indexed: Optional[datetime] = None
    url: Optional[str] = None
    frame_path: str = "main"
    dom_hash: Optional[str] = None
    element_descriptors: List[Dict[str, Any]] = field(default_factory=list)
    vector_store: InMemoryVectorStore = field(default_factory=InMemoryVectorStore)
    index_count: int = 0
    auto_index_enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Enhanced tracking
    indexed_element_ids: Set[str] = field(default_factory=set)
    is_cold_start: bool = True
    previous_descriptors: List[Dict[str, Any]] = field(default_factory=list)
    spa_route_tracking: bool = False
    last_route: Optional[str] = None


class EnhancedSessionManager:
    """Enhanced session manager with cold start and incremental updates."""

    def __init__(
        self,
        auto_index: bool = True,
        reindex_on_change: bool = True,
        reindex_on_failure: bool = True,
        index_interval_seconds: int = 30,
        cache_dir: Optional[Path] = None,
        enable_incremental: bool = True,
        enable_spa_tracking: bool = True,
    ):
        self.sessions: Dict[str, EnhancedSessionState] = {}
        self.auto_index = auto_index
        self.reindex_on_change = reindex_on_change
        self.reindex_on_failure = reindex_on_failure
        self.index_interval = timedelta(seconds=index_interval_seconds)
        self.element_embedder = ElementEmbedder()
        self._page_to_session: Dict[Any, str] = {}
        self._last_snapshot: Dict[str, Any] = {}
        self.enable_incremental = enable_incremental
        self.enable_spa_tracking = enable_spa_tracking
        
        # Setup caching
        cache_dir = cache_dir or Path(".cache")
        self.cache_dir = cache_dir
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        # SQLite cache for cold start
        self.sqlite_cache = SQLiteKV(cache_dir / "her_cache.db")
        
        # In-memory LRU cache
        self.memory_cache = LRUCache(capacity=512)

    def create_session(
        self,
        session_id: str,
        page: Optional[Page] = None,
        auto_index: Optional[bool] = None,
    ) -> EnhancedSessionState:
        """Create a new enhanced session."""
        if session_id in self.sessions:
            logger.warning(f"Session {session_id} already exists, returning existing")
            return self.sessions[session_id]

        session = EnhancedSessionState(
            session_id=session_id,
            auto_index_enabled=(
                auto_index if auto_index is not None else self.auto_index
            ),
        )

        self.sessions[session_id] = session

        if page:
            self._page_to_session[page] = session_id
            
            # Setup SPA tracking if enabled
            if self.enable_spa_tracking:
                self._setup_spa_tracking(page, session_id)
            
            # Index if auto-index enabled
            if session.auto_index_enabled:
                self._index_page_enhanced(session_id, page)

        logger.info(f"Created enhanced session: {session_id}")
        return session

    def _setup_spa_tracking(self, page: Page, session_id: str) -> None:
        """Setup SPA route change detection."""
        if not PLAYWRIGHT_AVAILABLE:
            return
            
        try:
            # Inject JavaScript to track history changes
            page.evaluate("""
                (() => {
                    if (window.__herSpaTracking) return;
                    window.__herSpaTracking = true;
                    
                    // Store original methods
                    const originalPushState = history.pushState;
                    const originalReplaceState = history.replaceState;
                    
                    // Track route changes
                    window.__herRouteChanges = [];
                    
                    // Override pushState
                    history.pushState = function() {
                        const result = originalPushState.apply(history, arguments);
                        window.__herRouteChanges.push({
                            type: 'pushState',
                            url: window.location.href,
                            timestamp: Date.now()
                        });
                        // Dispatch custom event
                        window.dispatchEvent(new CustomEvent('her-route-change', {
                            detail: { type: 'pushState', url: window.location.href }
                        }));
                        return result;
                    };
                    
                    // Override replaceState
                    history.replaceState = function() {
                        const result = originalReplaceState.apply(history, arguments);
                        window.__herRouteChanges.push({
                            type: 'replaceState',
                            url: window.location.href,
                            timestamp: Date.now()
                        });
                        window.dispatchEvent(new CustomEvent('her-route-change', {
                            detail: { type: 'replaceState', url: window.location.href }
                        }));
                        return result;
                    };
                    
                    // Listen for popstate
                    window.addEventListener('popstate', () => {
                        window.__herRouteChanges.push({
                            type: 'popstate',
                            url: window.location.href,
                            timestamp: Date.now()
                        });
                        window.dispatchEvent(new CustomEvent('her-route-change', {
                            detail: { type: 'popstate', url: window.location.href }
                        }));
                    });
                    
                    console.log('HER: SPA tracking initialized');
                })();
            """)
            
            # Setup listener for route changes
            page.expose_function("__herOnRouteChange", 
                lambda data: self._handle_spa_route_change(session_id, data))
            
            page.evaluate("""
                window.addEventListener('her-route-change', (e) => {
                    window.__herOnRouteChange(e.detail);
                });
            """)
            
            session = self.sessions.get(session_id)
            if session:
                session.spa_route_tracking = True
                
            logger.info(f"SPA tracking setup for session {session_id}")
            
        except Exception as e:
            logger.warning(f"Failed to setup SPA tracking: {e}")

    def _handle_spa_route_change(self, session_id: str, route_data: Dict) -> None:
        """Handle SPA route change event."""
        session = self.sessions.get(session_id)
        if not session:
            return
            
        new_route = route_data.get('url', '')
        route_type = route_data.get('type', '')
        
        logger.info(f"SPA route change detected: {route_type} to {new_route}")
        
        # Check if route actually changed
        if session.last_route != new_route:
            session.last_route = new_route
            
            # Get the page for this session
            page = None
            for p, sid in self._page_to_session.items():
                if sid == session_id:
                    page = p
                    break
                    
            if page:
                # Force re-index on route change
                logger.info(f"Re-indexing due to SPA route change")
                self._index_page_enhanced(session_id, page, force=True)

    def _wait_for_page_idle(self, page: Page, timeout: float = 5.0) -> bool:
        """Wait for page to be idle (document ready, network idle)."""
        if not PLAYWRIGHT_AVAILABLE or not page:
            return False
            
        try:
            # Wait for document ready state
            ready_state = page.evaluate("document.readyState")
            if ready_state != "complete":
                page.wait_for_load_state("domcontentloaded", timeout=timeout * 1000)
                page.wait_for_load_state("load", timeout=timeout * 1000)
            
            # Wait for network idle
            page.wait_for_load_state("networkidle", timeout=timeout * 1000)
            
            # Additional wait for async rendering
            page.wait_for_timeout(500)
            
            return True
            
        except Exception as e:
            logger.warning(f"Page not idle within timeout: {e}")
            return False

    def _index_page_enhanced(
        self, session_id: str, page: Page, force: bool = False
    ) -> Tuple[List[Dict[str, Any]], str]:
        """Enhanced page indexing with incremental updates."""
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Wait for page to be idle
        self._wait_for_page_idle(page)

        # Capture snapshot
        descriptors, dom_hash = capture_snapshot(page, session.frame_path)
        
        # Save snapshot for debugging
        self._last_snapshot[session_id] = {
            "descriptors": descriptors, 
            "dom_hash": dom_hash
        }

        # Handle cold start - check cache first
        if session.is_cold_start:
            cached_data = self._load_from_cache(dom_hash)
            if cached_data:
                logger.info(f"Cold start: loaded from cache for hash {dom_hash[:8]}")
                session.element_descriptors = cached_data['descriptors']
                session.vector_store = cached_data['vector_store']
                session.indexed_element_ids = cached_data['element_ids']
                session.dom_hash = dom_hash
                session.is_cold_start = False
                session.last_indexed = datetime.now()
                return session.element_descriptors, dom_hash
            else:
                logger.info(f"Cold start: no cache, performing full index")

        # Determine incremental updates
        elements_to_embed = []
        new_element_ids = set()
        removed_element_ids = set()
        
        if self.enable_incremental and not session.is_cold_start and not force:
            # Generate IDs for all current elements
            for desc in descriptors:
                elem_id = self._generate_element_id(desc)
                new_element_ids.add(elem_id)
                
                # Only embed if not already indexed
                if elem_id not in session.indexed_element_ids:
                    elements_to_embed.append(desc)
            
            # Find removed elements
            removed_element_ids = session.indexed_element_ids - new_element_ids
            
            if removed_element_ids:
                logger.info(f"Detected {len(removed_element_ids)} removed elements")
                
        else:
            # Full re-index
            elements_to_embed = descriptors
            for desc in descriptors:
                elem_id = self._generate_element_id(desc)
                new_element_ids.add(elem_id)

        # Store previous descriptors for diff
        session.previous_descriptors = session.element_descriptors.copy()
        
        # Update session
        session.element_descriptors = descriptors
        session.dom_hash = dom_hash
        session.last_indexed = datetime.now()
        session.url = page.url if page else None
        session.index_count += 1

        # Create embeddings for new/changed elements
        if elements_to_embed:
            try:
                logger.info(
                    f"Embedding {len(elements_to_embed)} elements "
                    f"(incremental={self.enable_incremental and not force})"
                )
                
                # Batch embed for efficiency
                embeddings = self.element_embedder.embed_batch(elements_to_embed)
                
                # Initialize or update vector store
                if session.is_cold_start or force or not session.vector_store:
                    session.vector_store = InMemoryVectorStore()
                    session.vector_store.add_batch(embeddings, elements_to_embed)
                else:
                    # Incremental update
                    for emb, desc in zip(embeddings, elements_to_embed):
                        session.vector_store.add(emb, desc)
                
                # Update indexed element IDs
                session.indexed_element_ids = new_element_ids
                
                # Save to cache
                self._save_to_cache(dom_hash, descriptors, session.vector_store, new_element_ids)
                
            except Exception as e:
                logger.error(f"Failed to create embeddings: {e}")
        else:
            logger.info(f"No new elements to embed (all {len(descriptors)} already indexed)")

        session.is_cold_start = False
        
        logger.info(
            f"Indexed page for session {session_id}: "
            f"total={len(descriptors)}, new={len(elements_to_embed)}, "
            f"removed={len(removed_element_ids)}, hash={dom_hash[:8]}"
        )

        return descriptors, dom_hash

    def _generate_element_id(self, descriptor: Dict[str, Any]) -> str:
        """Generate stable unique ID for element."""
        # Use stable properties
        id_parts = [
            descriptor.get('tag', ''),
            descriptor.get('id', ''),
            '|'.join(sorted(descriptor.get('classes', []))),
            descriptor.get('role', ''),
            descriptor.get('name', ''),
            str(descriptor.get('backendId', '')),
            str(descriptor.get('xpath', '')),
            # Include position for uniqueness
            str(descriptor.get('x', 0)),
            str(descriptor.get('y', 0)),
        ]
        id_str = '|'.join(str(p) for p in id_parts)
        return hashlib.sha256(id_str.encode()).hexdigest()[:16]

    def _save_to_cache(
        self, 
        dom_hash: str, 
        descriptors: List[Dict[str, Any]], 
        vector_store: InMemoryVectorStore, 
        element_ids: Set[str]
    ) -> None:
        """Save to both SQLite and memory cache."""
        try:
            cache_data = {
                'descriptors': descriptors,
                'vector_store': vector_store,
                'element_ids': element_ids,
                'timestamp': datetime.now().isoformat()
            }
            
            # Save to SQLite for persistence
            self.sqlite_cache.put(dom_hash, pickle.dumps(cache_data))
            
            # Save to memory cache for speed
            self.memory_cache.put(dom_hash, cache_data)
            
            logger.debug(f"Cached data for hash {dom_hash[:8]}")
            
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")

    def _load_from_cache(self, dom_hash: str) -> Optional[Dict[str, Any]]:
        """Load from cache (memory first, then SQLite)."""
        try:
            # Check memory cache first
            cached = self.memory_cache.get(dom_hash)
            if cached:
                logger.debug(f"Cache hit (memory) for {dom_hash[:8]}")
                return cached
            
            # Check SQLite cache
            data = self.sqlite_cache.get(dom_hash)
            if data:
                cached = pickle.loads(data)
                # Put in memory for next time
                self.memory_cache.put(dom_hash, cached)
                logger.debug(f"Cache hit (SQLite) for {dom_hash[:8]}")
                return cached
            
            logger.debug(f"Cache miss for {dom_hash[:8]}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to load cache: {e}")
            return None

    def get_session(self, session_id: str) -> Optional[EnhancedSessionState]:
        """Get session by ID."""
        return self.sessions.get(session_id)

    def should_reindex(
        self, 
        session: EnhancedSessionState, 
        page: Page, 
        force: bool = False
    ) -> bool:
        """Check if reindexing is needed."""
        if force:
            return True
            
        if not session.dom_hash:
            return True
            
        # Check time interval
        if session.last_indexed:
            elapsed = datetime.now() - session.last_indexed
            if elapsed > self.index_interval:
                return True
        
        # Check DOM change
        try:
            _, current_hash = capture_snapshot(page, session.frame_path)
            if detect_dom_change(session.dom_hash, current_hash):
                return True
        except Exception:
            pass
            
        return False

    def get_element_diff(
        self, 
        session_id: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get diff between previous and current elements."""
        session = self.sessions.get(session_id)
        if not session:
            return {"added": [], "removed": [], "unchanged": []}
        
        prev_ids = set()
        for desc in session.previous_descriptors:
            prev_ids.add(self._generate_element_id(desc))
        
        curr_ids = session.indexed_element_ids
        
        added_ids = curr_ids - prev_ids
        removed_ids = prev_ids - curr_ids
        unchanged_ids = curr_ids & prev_ids
        
        # Map IDs back to descriptors
        added = []
        unchanged = []
        
        for desc in session.element_descriptors:
            elem_id = self._generate_element_id(desc)
            if elem_id in added_ids:
                added.append(desc)
            elif elem_id in unchanged_ids:
                unchanged.append(desc)
        
        removed = []
        for desc in session.previous_descriptors:
            elem_id = self._generate_element_id(desc)
            if elem_id in removed_ids:
                removed.append(desc)
        
        return {
            "added": added,
            "removed": removed,
            "unchanged": unchanged
        }

    def clear_cache(self) -> None:
        """Clear all caches."""
        self.memory_cache = LRUCache(capacity=512)
        # Note: SQLite cache persists unless explicitly cleared
        logger.info("Cleared memory cache")


__all__ = ['EnhancedSessionManager', 'EnhancedSessionState']