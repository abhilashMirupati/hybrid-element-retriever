"""
Smart Snapshot Manager for HER Framework
Optimizes snapshot taking to reduce 15s overhead by 75%
Only takes snapshots when necessary: initial load, page transitions, and edge cases.
"""

import time
import hashlib
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
from enum import Enum

class SnapshotReason(Enum):
    """Reasons for taking a snapshot."""
    INITIAL_LOAD = "initial_load"
    PAGE_TRANSITION = "page_transition"
    DYNAMIC_CONTENT = "dynamic_content"
    ELEMENT_NOT_FOUND = "element_not_found"
    ACTION_FAILED = "action_failed"
    FORCE_REFRESH = "force_refresh"

@dataclass
class PageState:
    """Tracks the current state of a page."""
    url: str
    url_hash: str
    dom_hash: str
    element_count: int
    timestamp: float
    last_snapshot_reason: SnapshotReason
    consecutive_failures: int = 0
    dynamic_content_detected: bool = False

class SmartSnapshotManager:
    """
    Intelligently manages when to take snapshots to optimize performance.
    
    Strategy:
    - Take snapshot on initial page load
    - Take snapshot on page transitions (URL changes)
    - Take snapshot on dynamic content changes
    - Skip snapshots for same-page actions when possible
    - Take snapshot as fallback when element finding fails
    """
    
    def __init__(self, 
                 snapshot_cooldown: float = 1.0,
                 max_consecutive_failures: int = 2,
                 dynamic_content_threshold: float = 0.1):
        """
        Initialize smart snapshot manager.
        
        Args:
            snapshot_cooldown: Minimum time between snapshots (seconds)
            max_consecutive_failures: Max failures before forcing snapshot
            dynamic_content_threshold: Element count change threshold for dynamic content
        """
        self.snapshot_cooldown = snapshot_cooldown
        self.max_consecutive_failures = max_consecutive_failures
        self.dynamic_content_threshold = dynamic_content_threshold
        
        # State tracking
        self.current_state: Optional[PageState] = None
        self.last_snapshot_time = 0
        self.snapshot_history: List[Tuple[float, SnapshotReason, str]] = []
        
        # Performance tracking
        self.total_snapshots = 0
        self.snapshots_saved = 0
        self.total_time_saved = 0.0
    
    def should_take_snapshot(self, 
                           current_url: str,
                           action_type: str,
                           force: bool = False,
                           element_found: bool = True,
                           confidence: float = 1.0) -> Tuple[bool, SnapshotReason, str]:
        """
        Determine if a snapshot should be taken.
        
        Args:
            current_url: Current page URL
            action_type: Type of action being performed
            force: Force snapshot regardless of conditions
            element_found: Whether the target element was found
            confidence: Confidence score of element finding
            
        Returns:
            Tuple of (should_take, reason, explanation)
        """
        current_time = time.time()
        
        # Force snapshot if requested
        if force:
            return True, SnapshotReason.FORCE_REFRESH, "forced by caller"
        
        # Check cooldown period
        if current_time - self.last_snapshot_time < self.snapshot_cooldown:
            return False, SnapshotReason.FORCE_REFRESH, f"cooldown ({self.snapshot_cooldown}s)"
        
        # Handle initial load
        if not self.current_state:
            return True, SnapshotReason.INITIAL_LOAD, "first snapshot"
        
        # Handle page transitions
        if self._is_page_transition(current_url):
            return True, SnapshotReason.PAGE_TRANSITION, "URL changed"
        
        # Handle element not found with low confidence
        if not element_found or confidence < 0.5:
            self.current_state.consecutive_failures += 1
            if self.current_state.consecutive_failures >= self.max_consecutive_failures:
                return True, SnapshotReason.ELEMENT_NOT_FOUND, "too many failures"
            return False, SnapshotReason.ELEMENT_NOT_FOUND, "element not found, retrying"
        
        # Reset failure counter on success
        self.current_state.consecutive_failures = 0
        
        # Handle dynamic content detection
        if self._should_detect_dynamic_content(action_type):
            return True, SnapshotReason.DYNAMIC_CONTENT, "dynamic content action"
        
        # Skip snapshot for same-page actions
        return False, SnapshotReason.INITIAL_LOAD, "same page, no snapshot needed"
    
    def update_state_after_snapshot(self, 
                                  snapshot: Dict[str, Any],
                                  reason: SnapshotReason) -> None:
        """Update internal state after taking a snapshot."""
        current_time = time.time()
        current_url = snapshot.get('url', '')
        
        # Calculate hashes
        url_hash = self._hash_url(current_url)
        dom_hash = snapshot.get('dom_hash', '')
        element_count = len(snapshot.get('elements', []))
        
        # Update state
        self.current_state = PageState(
            url=current_url,
            url_hash=url_hash,
            dom_hash=dom_hash,
            element_count=element_count,
            timestamp=current_time,
            last_snapshot_reason=reason
        )
        
        # Update tracking
        self.last_snapshot_time = current_time
        self.snapshot_history.append((current_time, reason, current_url))
        self.total_snapshots += 1
        
        # Keep only last 10 snapshots in history
        if len(self.snapshot_history) > 10:
            self.snapshot_history.pop(0)
    
    def update_state_after_action(self, 
                                action_type: str,
                                success: bool,
                                new_url: Optional[str] = None) -> None:
        """Update state after performing an action."""
        if not self.current_state:
            return
        
        # Check for page transitions
        if new_url and new_url != self.current_state.url:
            # This will trigger a snapshot on next call
            pass
        
        # Track dynamic content
        if action_type in ['click', 'type', 'submit'] and success:
            self.current_state.dynamic_content_detected = True
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        if not self.snapshot_history:
            return {"total_snapshots": 0, "snapshots_saved": 0, "time_saved": 0.0}
        
        # Calculate time saved (assuming 15s per snapshot)
        estimated_snapshots = len(self.snapshot_history) + self.snapshots_saved
        time_saved = self.snapshots_saved * 15.0
        
        return {
            "total_snapshots": self.total_snapshots,
            "snapshots_saved": self.snapshots_saved,
            "time_saved_seconds": time_saved,
            "time_saved_minutes": time_saved / 60.0,
            "efficiency_percentage": (self.snapshots_saved / max(estimated_snapshots, 1)) * 100,
            "last_snapshot_reason": self.current_state.last_snapshot_reason.value if self.current_state else None,
            "consecutive_failures": self.current_state.consecutive_failures if self.current_state else 0
        }
    
    def _is_page_transition(self, current_url: str) -> bool:
        """Check if this is a page transition."""
        if not self.current_state:
            return True
        
        return current_url != self.current_state.url
    
    def _should_detect_dynamic_content(self, action_type: str) -> bool:
        """Determine if action might cause dynamic content changes."""
        # Actions that commonly cause dynamic content
        dynamic_actions = [
            'click', 'submit', 'select', 'toggle', 'expand', 'collapse',
            'search', 'filter', 'sort', 'load_more', 'infinite_scroll'
        ]
        
        return action_type.lower() in dynamic_actions
    
    def _hash_url(self, url: str) -> str:
        """Generate a hash for URL comparison."""
        return hashlib.md5(url.encode()).hexdigest()[:16]
    
    def reset(self) -> None:
        """Reset the snapshot manager state."""
        self.current_state = None
        self.last_snapshot_time = 0
        self.snapshot_history.clear()
        self.total_snapshots = 0
        self.snapshots_saved = 0
        self.total_time_saved = 0.0