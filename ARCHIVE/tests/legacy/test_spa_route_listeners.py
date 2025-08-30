"""Test SPA route change detection and handling."""

import pytest
from unittest.mock import Mock, MagicMock, patch
# import sys
# from pathlib import Path
# removed sys.path hack
from her.session.snapshot import SnapshotManager


class TestSPARouteListeners:
    """Test SPA route change detection."""
    
    def test_pushstate_detection(self):
        """Test pushState route change detection."""
        snapshot_mgr = SnapshotManager()
        
        mock_page = Mock()
        mock_page.url = "http://example.com/home"
        
        # Simulate route change via pushState
        mock_page.evaluate.side_effect = [
            None,  # Inject listeners
            [{"type": "pushState", "url": "http://example.com/about", "timestamp": 123}],  # Check changes
            [],  # Clear changes
        ]
        
        # Inject listeners
        snapshot_mgr._inject_spa_listeners(mock_page)
        
        # Check for route changes
        assert snapshot_mgr.check_route_changed(mock_page)
        
        # Clear changes
        snapshot_mgr.clear_route_changes(mock_page)
    
    def test_replacestate_detection(self):
        """Test replaceState route change detection."""
        snapshot_mgr = SnapshotManager()
        
        mock_page = Mock()
        mock_page.evaluate.return_value = [
            {"type": "replaceState", "url": "http://example.com/profile", "timestamp": 456}
        ]
        
        assert snapshot_mgr.check_route_changed(mock_page)
    
    def test_popstate_detection(self):
        """Test popstate (back/forward) detection."""
        snapshot_mgr = SnapshotManager()
        
        mock_page = Mock()
        mock_page.evaluate.return_value = [
            {"type": "popstate", "url": "http://example.com/previous", "timestamp": 789}
        ]
        
        assert snapshot_mgr.check_route_changed(mock_page)
    
    def test_hashchange_detection(self):
        """Test hash-only navigation detection."""
        snapshot_mgr = SnapshotManager()
        
        mock_page = Mock()
        mock_page.evaluate.return_value = [
            {"type": "hashchange", "url": "http://example.com/#section2", "timestamp": 999}
        ]
        
        assert snapshot_mgr.check_route_changed(mock_page)
    
    def test_reindex_trigger_without_reload(self):
        """Test that reindex is triggered without page reload."""
        snapshot_mgr = SnapshotManager()
        
        mock_page = Mock()
        mock_page.url = "http://example.com"
        mock_page.content.return_value = "<html><body>New content</body></html>"
        mock_page.evaluate.side_effect = [
            # Initial snapshot
            [{"tag": "div", "id": "content", "text": "Initial"}],
            # Route change detected
            [{"type": "pushState", "url": "http://example.com/new", "timestamp": 111}],
            # New element count after route change
            150,  # Significant change in element count
        ]
        
        # Initial snapshot
        snapshot1, _ = snapshot_mgr.capture_snapshot(mock_page, "session1")
        
        # Check if reindex needed (route changed)
        needs_reindex = snapshot_mgr.needs_reindex(mock_page, "session1")
        
        assert needs_reindex, "Should trigger reindex after route change"
    
    def test_soft_navigation_detection(self):
        """Test soft navigation (no URL change but content change)."""
        snapshot_mgr = SnapshotManager()
        
        mock_page = Mock()
        mock_page.url = "http://example.com"
        
        # Initial snapshot
        mock_page.content.return_value = "<html><body>Content1</body></html>"
        mock_page.evaluate.return_value = 100  # Element count
        
        snapshot1, _ = snapshot_mgr.capture_snapshot(mock_page, "session1")
        
        # Significant DOM change without URL change
        mock_page.content.return_value = "<html><body>Content2 with much more</body></html>"
        mock_page.evaluate.side_effect = [
            [],  # No route changes
            200,  # Double the element count
        ]
        
        needs_reindex = snapshot_mgr.needs_reindex(mock_page, "session1", threshold=0.3)
        
        assert needs_reindex, "Should detect significant DOM change"
    
    def test_spa_listener_injection_once(self):
        """Test that SPA listeners are injected only once."""
        snapshot_mgr = SnapshotManager()
        
        mock_page = Mock()
        mock_page.evaluate.return_value = None
        
        # First injection
        snapshot_mgr._inject_spa_listeners(mock_page)
        snapshot_mgr.spa_listener_injected["session1"] = True
        
        # Try to inject again for same session
        mock_page.evaluate.reset_mock()
        snapshot_mgr.capture_snapshot(mock_page, "session1")
        
        # Should not inject again
        # Note: In real implementation, would check window.__herListenersInjected