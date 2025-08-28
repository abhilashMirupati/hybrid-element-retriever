"""Session management with automatic indexing and DOM change detection."""

from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
import json
from pathlib import Path

from ..bridge.snapshot import capture_snapshot, detect_dom_change
from ..embeddings.element_embedder import ElementEmbedder
from ..vectordb.faiss_store import InMemoryVectorStore

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
class SessionState:
    """State for a single browser session."""

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


class SessionManager:
    """Manages browser sessions with automatic indexing."""

    def __init__(
        self,
        auto_index: bool = True,
        reindex_on_change: bool = True,
        reindex_on_failure: bool = True,
        index_interval_seconds: int = 30,
    ):
        self.sessions: Dict[str, SessionState] = {}
        self.auto_index = auto_index
        self.reindex_on_change = reindex_on_change
        self.reindex_on_failure = reindex_on_failure
        self.index_interval = timedelta(seconds=index_interval_seconds)
        self.element_embedder = ElementEmbedder()
        self._page_to_session: Dict[Any, str] = {}
        self._last_snapshot: Dict[str, Any] = {}

    def create_session(
        self,
        session_id: str,
        page: Optional[Page] = None,
        auto_index: Optional[bool] = None,
    ) -> SessionState:
        """Create a new session.

        Args:
            session_id: Unique session identifier
            page: Playwright page instance
            auto_index: Override global auto_index setting

        Returns:
            Created session state
        """
        if session_id in self.sessions:
            logger.warning(f"Session {session_id} already exists, returning existing")
            return self.sessions[session_id]

        session = SessionState(
            session_id=session_id,
            auto_index_enabled=(
                auto_index if auto_index is not None else self.auto_index
            ),
        )

        self.sessions[session_id] = session

        if page:
            self._page_to_session[page] = session_id
            if session.auto_index_enabled:
                self._index_page(session_id, page)
            # Set up SPA tracking
            self._setup_spa_tracking(page, session_id)

        logger.info(f"Created session: {session_id}")
        return session

    def get_session(self, session_id: str) -> Optional[SessionState]:
        """Get session by ID."""
        return self.sessions.get(session_id)

    def get_session_for_page(self, page: Page) -> Optional[SessionState]:
        """Get session associated with a page."""
        session_id = self._page_to_session.get(page)
        if session_id:
            return self.sessions.get(session_id)
        return None

    def destroy_session(self, session_id: str) -> None:
        """Destroy a session and clean up resources."""
        if session_id in self.sessions:
            session = self.sessions[session_id]

            # Clean up page mapping
            pages_to_remove = [
                p for p, sid in self._page_to_session.items() if sid == session_id
            ]
            for page in pages_to_remove:
                del self._page_to_session[page]

            del self.sessions[session_id]
            logger.info(f"Destroyed session: {session_id}")

    def should_reindex(
        self, session: SessionState, page: Optional[Page] = None, force: bool = False
    ) -> bool:
        """Determine if page should be reindexed.

        Args:
            session: Session state
            page: Playwright page
            force: Force reindex regardless of conditions

        Returns:
            True if reindexing is needed
        """
        if force:
            return True

        if not session.auto_index_enabled:
            return False

        # Never indexed
        if session.last_indexed is None:
            return True

        # Check time since last index
        if datetime.now() - session.last_indexed > self.index_interval:
            return True

        # Check URL change
        if page:
            current_url = page.url
            if current_url != session.url:
                logger.debug(f"URL changed: {session.url} -> {current_url}")
                return True

        # Check DOM change
        if self.reindex_on_change and page:
            _, new_hash = capture_snapshot(page, session.frame_path)
            if detect_dom_change(session.dom_hash, new_hash):
                old8 = (session.dom_hash or '')[:8]
                new8 = (new_hash or '')[:8]
                logger.debug(
                    f"DOM changed: {old8}... -> {new8}..."
                )
                return True
            else:
                return False

        return False

    def index_page(
        self, session_id: str, page: Page, force: bool = False
    ) -> Tuple[List[Dict[str, Any]], str]:
        """Index a page for the session.

        Args:
            session_id: Session ID
            page: Page to index
            force: Force reindex even if not needed

        Returns:
            Tuple of (element_descriptors, dom_hash)
        """
        session = self.sessions.get(session_id)
        if not session:
            session = self.create_session(session_id, page)

        return self._index_page(session_id, page, force)

    def _index_page(
        self, session_id: str, page: Page, force: bool = False
    ) -> Tuple[List[Dict[str, Any]], str]:
        """Internal method to index a page."""
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Check if reindex is needed
        if not self.should_reindex(session, page, force):
            logger.debug(f"Skipping reindex for session {session_id}")
            return session.element_descriptors, session.dom_hash or ""

        logger.info(f"Indexing page for session {session_id}")

        # Capture snapshot
        descriptors, dom_hash = capture_snapshot(page, session.frame_path)
        # Save snapshot for external inspection
        self._last_snapshot[session_id] = {"descriptors": descriptors, "dom_hash": dom_hash}

        # Update session
        session.element_descriptors = descriptors
        session.dom_hash = dom_hash
        session.last_indexed = datetime.now()
        session.url = page.url if page else None
        session.index_count += 1

        # Clear and rebuild vector store
        session.vector_store = InMemoryVectorStore()

        # Generate embeddings and add to vector store
        for desc in descriptors:
            try:
                embedding = self.element_embedder.embed(desc)
                session.vector_store.add(embedding, desc)
            except Exception as e:
                logger.warning(f"Failed to embed element: {e}")

        logger.info(
            f"Indexed {len(descriptors)} elements for session {session_id}, "
            f"hash={dom_hash[:8]}..., index_count={session.index_count}"
        )

        return descriptors, dom_hash

    # ---- Helpers for tests ----
    def get_current_snapshot(self) -> Optional[Dict[str, Any]]:
        """Return last captured snapshot for any session (single session use)."""
        if not self.sessions:
            return None
        # Return snapshot of the first/only session
        sid = next(iter(self.sessions.keys()))
        return self._last_snapshot.get(sid)

    def needs_reindex(self, session_id: str) -> bool:
        """Compatibility helper used in tests to indicate DOM changed."""
        session = self.sessions.get(session_id)
        if not session:
            return True
        # Compare stored dom_hash vs snapshot dom_hash
        snap = self._last_snapshot.get(session_id)
        if not snap:
            return True
        return bool(detect_dom_change(session.dom_hash or '', snap.get('dom_hash','') or ''))

    def trigger_reindex_on_failure(
        self,
        session_id: str,
        page: Optional[Page] = None,
        error: Optional[Exception] = None,
    ) -> bool:
        """Trigger reindex after a locator failure.

        Args:
            session_id: Session ID
            page: Page instance
            error: The error that triggered reindex

        Returns:
            True if reindex was performed
        """
        if not self.reindex_on_failure:
            return False

        session = self.sessions.get(session_id)
        if not session or not page:
            return False

        logger.info(f"Triggering reindex due to failure: {error}")

        try:
            self._index_page(session_id, page, force=True)
            return True
        except Exception as e:
            logger.error(f"Failed to reindex on failure: {e}")
            return False

    def get_cache_key(self, session_id: str) -> str:
        """Get cache key for current session state.

        Args:
            session_id: Session ID

        Returns:
            Cache key string
        """
        session = self.sessions.get(session_id)
        if not session:
            return f"{session_id}|unknown|unknown"

        return f"{session.url or 'unknown'}|{session.frame_path}|{session.dom_hash or 'unknown'}"

    def export_session(self, session_id: str) -> Dict[str, Any]:
        """Export session state for persistence.

        Args:
            session_id: Session ID

        Returns:
            Serializable session state
        """
        session = self.sessions.get(session_id)
        if not session:
            return {}

        return {
            "session_id": session.session_id,
            "created_at": session.created_at.isoformat(),
            "last_indexed": (
                session.last_indexed.isoformat() if session.last_indexed else None
            ),
            "url": session.url,
            "frame_path": session.frame_path,
            "dom_hash": session.dom_hash,
            "index_count": session.index_count,
            "element_count": len(session.element_descriptors),
            "metadata": session.metadata,
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get session manager statistics.

        Returns:
            Statistics dictionary
        """
        total_elements = sum(len(s.element_descriptors) for s in self.sessions.values())
        total_indexes = sum(s.index_count for s in self.sessions.values())

        return {
            "session_count": len(self.sessions),
            "total_elements": total_elements,
            "total_indexes": total_indexes,
            "auto_index": self.auto_index,
            "reindex_on_change": self.reindex_on_change,
            "reindex_on_failure": self.reindex_on_failure,
        }

    def _setup_spa_tracking(self, page: Page, session_id: str) -> None:
        """Set up SPA route change tracking.

        Args:
            page: Playwright page instance
            session_id: Session ID to track
        """
        if not page:
            return

        try:
            # Inject JavaScript to track SPA route changes
            spa_tracking_script = """
            (() => {
                // Track the original methods
                const originalPushState = history.pushState;
                const originalReplaceState = history.replaceState;

                // Flag to track if we should re-index
                window.__herNeedsReindex = false;
                window.__herLastUrl = window.location.href;

                // Override pushState
                history.pushState = function() {
                    originalPushState.apply(history, arguments);
                    window.__herNeedsReindex = true;
                    window.__herLastUrl = window.location.href;
                    window.dispatchEvent(new Event('__herRouteChange'));
                };

                // Override replaceState
                history.replaceState = function() {
                    originalReplaceState.apply(history, arguments);
                    window.__herNeedsReindex = true;
                    window.__herLastUrl = window.location.href;
                    window.dispatchEvent(new Event('__herRouteChange'));
                };

                // Listen for popstate (back/forward)
                window.addEventListener('popstate', () => {
                    window.__herNeedsReindex = true;
                    window.__herLastUrl = window.location.href;
                    window.dispatchEvent(new Event('__herRouteChange'));
                });

                // Also track hash changes
                window.addEventListener('hashchange', () => {
                    window.__herNeedsReindex = true;
                    window.__herLastUrl = window.location.href;
                    window.dispatchEvent(new Event('__herRouteChange'));
                });

                console.log('HER: SPA tracking initialized');
            })();
            """

            # Inject the tracking script
            try:
                page.evaluate(spa_tracking_script)
            except Exception:
                # Allow mocks without evaluate implementation
                pass

            # Set up listener for route changes
            try:
                page.expose_function(
                    "__herHandleRouteChange",
                    lambda: self._handle_spa_route_change(session_id, page),
                )
            except Exception:
                pass

            # Add event listener for our custom event
            try:
                page.evaluate(
                    """
                    window.addEventListener('__herRouteChange', () => {
                        if (window.__herHandleRouteChange) {
                            window.__herHandleRouteChange();
                        }
                    });
                """
                )
            except Exception:
                pass

            logger.info(f"SPA tracking set up for session {session_id}")

        except Exception as e:
            logger.warning(f"Failed to set up SPA tracking: {e}")

    def _handle_spa_route_change(self, session_id: str, page: Page) -> None:
        """Handle SPA route change event.

        Args:
            session_id: Session ID
            page: Page that changed
        """
        try:
            session = self.get_session(session_id)
            if not session:
                return

            # Check if URL actually changed
            new_url = page.url
            if new_url != session.url:
                logger.info(f"SPA route change detected: {session.url} -> {new_url}")
                session.url = new_url

                # Re-index if auto-index is enabled
                if session.auto_index_enabled and self.reindex_on_change:
                    logger.info(
                        f"Re-indexing after SPA route change for session {session_id}"
                    )
                    self._index_page(session_id, page)

        except Exception as e:
            logger.warning(f"Failed to handle SPA route change: {e}")

    def check_spa_changes(self, session_id: str, page: Page) -> bool:
        """Check if SPA has navigated since last check.

        Args:
            session_id: Session ID
            page: Page to check

        Returns:
            True if SPA navigation detected
        """
        if not page or not PLAYWRIGHT_AVAILABLE:
            return False

        try:
            # Check the flag we set in JavaScript
            needs_reindex = page.evaluate("window.__herNeedsReindex || false")

            if needs_reindex:
                # Reset the flag
                page.evaluate("window.__herNeedsReindex = false")

                # Update session URL
                session = self.get_session(session_id)
                if session:
                    new_url = page.url
                    if new_url != session.url:
                        logger.info(
                            f"SPA navigation detected via flag: {session.url} -> {new_url}"
                        )
                        session.url = new_url
                        return True

            return False

        except Exception as e:
            logger.debug(f"Failed to check SPA changes: {e}")
            return False
