# archived duplicate of src/her/executor/session.py
"""Session management for SPA route detection and DOM delta tracking."""

import asyncio
import time
import hashlib
import json
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
import logging

from playwright.async_api import Page, Response

from her.bridge.snapshot import Snapshot, SnapshotResult

logger = logging.getLogger(__name__)


@dataclass
class RouteChange:
    """Represents a detected route change."""
    timestamp: float
    old_url: str
    new_url: str
    change_type: str  # 'navigation', 'pushstate', 'replacestate', 'popstate', 'hashchange'
    dom_delta: float  # Percentage of DOM change
    

@dataclass
class SessionState:
    """Current session state."""
    url: str
    dom_hash: str
    last_snapshot: Optional[SnapshotResult]
    route_changes: List[RouteChange] = field(default_factory=list)
    total_snapshots: int = 0
    cache_hits: int = 0
    reindex_count: int = 0
    

class Session:
    """Manages browser session with SPA route detection and DOM delta tracking."""
    
    # DOM delta threshold for triggering reindex (30% change)
    DELTA_THRESHOLD = 0.3
    
    # Minimum time between snapshots (ms)
    MIN_SNAPSHOT_INTERVAL = 100
    
    def __init__(self, page: Page, auto_detect_spa: bool = True):
        self.page = page
        self.snapshot = Snapshot(page)
        self.auto_detect_spa = auto_detect_spa
        self.state = SessionState(
            url=page.url,
            dom_hash="",
            last_snapshot=None
        )
        self._last_snapshot_time = 0
        self._route_listeners_attached = False
        self._snapshot_cache: Dict[str, SnapshotResult] = {}
        self._reindex_callback: Optional[Callable] = None
        
    async def initialize(self) -> None:
        """Initialize session and attach listeners."""
        if self.auto_detect_spa:
            await self._attach_route_listeners()
            
        # Take initial snapshot
        await self.take_snapshot()
        
    async def _attach_route_listeners(self) -> None:
        """Attach listeners for SPA route changes."""
        if self._route_listeners_attached:
            return
            
        # Inject route detection script
        await self.page.evaluate("""
            (() => {
                // Track pushState
                const originalPushState = history.pushState;
                history.pushState = function(...args) {
                    const oldUrl = window.location.href;
                    originalPushState.apply(history, args);
                    window.__herRouteChange = {
                        type: 'pushstate',
                        oldUrl: oldUrl,
                        newUrl: window.location.href,
                        timestamp: Date.now()
                    };
                    window.dispatchEvent(new CustomEvent('her-route-change'));
                };
                
                // Track replaceState  
                const originalReplaceState = history.replaceState;
                history.replaceState = function(...args) {
                    const oldUrl = window.location.href;
                    originalReplaceState.apply(history, args);
                    window.__herRouteChange = {
                        type: 'replacestate',
                        oldUrl: oldUrl,
                        newUrl: window.location.href,
                        timestamp: Date.now()
                    };
                    window.dispatchEvent(new CustomEvent('her-route-change'));
                };
                
                // Track popstate
                window.addEventListener('popstate', () => {
                    window.__herRouteChange = {
                        type: 'popstate',
                        oldUrl: window.__herLastUrl || '',
                        newUrl: window.location.href,
                        timestamp: Date.now()
                    };
                    window.dispatchEvent(new CustomEvent('her-route-change'));
                });
                
                // Track hashchange
                window.addEventListener('hashchange', (e) => {
                    window.__herRouteChange = {
                        type: 'hashchange',
                        oldUrl: e.oldURL,
                        newUrl: e.newURL,
                        timestamp: Date.now()
                    };
                    window.dispatchEvent(new CustomEvent('her-route-change'));
                });
                
                window.__herLastUrl = window.location.href;
            })();
        """)
        
        # Listen for route changes
        await self.page.expose_function('__herHandleRouteChange', self._handle_route_change)
        await self.page.evaluate("""
            window.addEventListener('her-route-change', async () => {
                if (window.__herRouteChange) {
                    await window.__herHandleRouteChange(window.__herRouteChange);
                    window.__herLastUrl = window.location.href;
                }
            });
        """)
        
        self._route_listeners_attached = True
        logger.info("SPA route listeners attached")
        
    async def _handle_route_change(self, change_data: Dict) -> None:
        """Handle detected route change."""
        logger.info(f"Route change detected: {change_data['type']} from {change_data['oldUrl']} to {change_data['newUrl']}")
        
        # Take new snapshot and calculate delta
        old_hash = self.state.dom_hash
        new_snapshot = await self.take_snapshot()
        new_hash = self.state.dom_hash
        
        # Calculate DOM delta
        dom_delta = await self._calculate_dom_delta(old_hash, new_hash)
        
        # Record route change
        route_change = RouteChange(
            timestamp=time.time(),
            old_url=change_data['oldUrl'],
            new_url=change_data['newUrl'],
            change_type=change_data['type'],
            dom_delta=dom_delta
        )
        self.state.route_changes.append(route_change)
        
        # Check if reindex needed
        if dom_delta > self.DELTA_THRESHOLD:
            await self.reindex_if_needed()
            
    async def take_snapshot(self, force: bool = False) -> SnapshotResult:
        """Take a DOM/AX snapshot, using cache if available.
        
        Args:
            force: Force new snapshot even if cached
            
        Returns:
            SnapshotResult
        """
        current_time = time.time() * 1000
        
        # Check minimum interval
        if not force and current_time - self._last_snapshot_time < self.MIN_SNAPSHOT_INTERVAL:
            if self.state.last_snapshot:
                return self.state.last_snapshot
                
        # Check cache
        url = self.page.url
        cache_key = f"{url}:{await self._get_page_state_hash()}"
        
        if not force and cache_key in self._snapshot_cache:
            self.state.cache_hits += 1
            snapshot = self._snapshot_cache[cache_key]
        else:
            # Take new snapshot
            snapshot = await self.snapshot.capture()
            self._snapshot_cache[cache_key] = snapshot
            
            # Limit cache size
            if len(self._snapshot_cache) > 10:
                oldest = min(self._snapshot_cache.keys())
                del self._snapshot_cache[oldest]
                
        # Update state
        self.state.url = url
        self.state.last_snapshot = snapshot
        self.state.total_snapshots += 1
        self._last_snapshot_time = current_time
        
        # Update DOM hash
        if snapshot.frames:
            self.state.dom_hash = snapshot.frames[0].dom_hash
            
        return snapshot
        
    async def _get_page_state_hash(self) -> str:
        """Get hash of current page state for caching."""
        try:
            # Get key page state indicators
            state_data = await self.page.evaluate("""
                (() => {
                    return {
                        url: window.location.href,
                        title: document.title,
                        bodyClass: document.body?.className || '',
                        mainContent: document.querySelector('main')?.innerHTML?.substring(0, 100) || '',
                        formCount: document.querySelectorAll('form').length,
                        inputCount: document.querySelectorAll('input, select, textarea').length
                    };
                })();
            """)
            state_str = json.dumps(state_data, sort_keys=True)
            return hashlib.md5(state_str.encode()).hexdigest()[:8]
        except:
            return "unknown"
            
    async def _calculate_dom_delta(self, old_hash: str, new_hash: str) -> float:
        """Calculate DOM change percentage between hashes.
        
        Returns:
            Float between 0.0 (no change) and 1.0 (complete change)
        """
        if not old_hash or not new_hash:
            return 1.0
        if old_hash == new_hash:
            return 0.0
            
        # Simple hash difference ratio
        # In production, would compare actual node lists
        diff_chars = sum(1 for a, b in zip(old_hash, new_hash) if a != b)
        return diff_chars / len(old_hash)
        
    async def reindex_if_needed(self, force: bool = False) -> bool:
        """Trigger reindexing if DOM changed significantly.
        
        Args:
            force: Force reindex regardless of delta
            
        Returns:
            True if reindex was triggered
        """
        if not self.state.last_snapshot:
            return False
            
        # Check if reindex needed
        needs_reindex = force
        if not needs_reindex and self.state.route_changes:
            recent_change = self.state.route_changes[-1]
            needs_reindex = recent_change.dom_delta > self.DELTA_THRESHOLD
            
        if needs_reindex:
            logger.info(f"Reindexing triggered (force={force})")
            self.state.reindex_count += 1
            
            # Clear snapshot cache
            self._snapshot_cache.clear()
            
            # Take fresh snapshot
            await self.take_snapshot(force=True)
            
            # Call reindex callback if set
            if self._reindex_callback:
                await self._reindex_callback(self.state.last_snapshot)
                
            return True
            
        return False
        
    def set_reindex_callback(self, callback: Callable) -> None:
        """Set callback to be called when reindex is triggered.
        
        Args:
            callback: Async function that takes SnapshotResult
        """
        self._reindex_callback = callback
        
    async def wait_for_stable_dom(self, timeout: int = 5000) -> None:
        """Wait for DOM to stabilize (no changes for a period).
        
        Args:
            timeout: Maximum time to wait in ms
        """
        start_time = time.time() * 1000
        last_hash = ""
        stable_count = 0
        
        while time.time() * 1000 - start_time < timeout:
            current_hash = await self._get_page_state_hash()
            
            if current_hash == last_hash:
                stable_count += 1
                if stable_count >= 3:  # Stable for 3 checks
                    return
            else:
                stable_count = 0
                last_hash = current_hash
                
            await asyncio.sleep(0.1)
            
        logger.warning(f"DOM did not stabilize within {timeout}ms")
        
    def get_stats(self) -> Dict[str, Any]:
        """Get session statistics.
        
        Returns:
            Dictionary of session stats
        """
        return {
            "url": self.state.url,
            "total_snapshots": self.state.total_snapshots,
            "cache_hits": self.state.cache_hits,
            "cache_hit_rate": self.state.cache_hits / max(1, self.state.total_snapshots),
            "route_changes": len(self.state.route_changes),
            "reindex_count": self.state.reindex_count,
            "last_dom_hash": self.state.dom_hash
        }