"""Test SPA route change detection and handling."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from her.pipeline import HERPipeline, PipelineConfig


class TestSPARouteListeners:
    """Test SPA route change listeners and reindexing."""
    
    @pytest.fixture
    def pipeline(self):
        """Create pipeline with SPA support."""
        config = PipelineConfig(
            enable_spa_tracking=True,
            detect_route_changes=True
        )
        return HERPipeline(config=config)
    
    def test_pushstate_detection(self, pipeline):
        """Test detection of pushState route changes."""
        # Simulate pushState event
        old_url = "https://example.com/page1"
        new_url = "https://example.com/page2"
        
        with patch.object(pipeline, '_on_route_change') as mock_route_change:
            # Simulate browser pushState
            pipeline._handle_pushstate(old_url, new_url)
            mock_route_change.assert_called_once()
    
    def test_replacestate_detection(self, pipeline):
        """Test detection of replaceState route changes."""
        old_url = "https://example.com/page1"
        new_url = "https://example.com/page1?updated=true"
        
        with patch.object(pipeline, '_on_route_change') as mock_route_change:
            # Simulate browser replaceState
            pipeline._handle_replacestate(old_url, new_url)
            mock_route_change.assert_called_once()
    
    def test_popstate_detection(self, pipeline):
        """Test detection of popstate (back/forward) events."""
        with patch.object(pipeline, '_on_route_change') as mock_route_change:
            # Simulate browser back button
            pipeline._handle_popstate()
            mock_route_change.assert_called_once()
    
    def test_hash_change_detection(self, pipeline):
        """Test detection of hash changes in URL."""
        old_url = "https://example.com/#section1"
        new_url = "https://example.com/#section2"
        
        with patch.object(pipeline, '_on_route_change') as mock_route_change:
            pipeline._handle_hashchange(old_url, new_url)
            mock_route_change.assert_called_once()
    
    def test_reindex_on_route_change(self, pipeline):
        """Test that route changes trigger reindexing without full reload."""
        initial_dom = {
            "url": "https://example.com/page1",
            "elements": [
                {"tag": "div", "text": "Page 1", "xpath": "//div[1]"}
            ]
        }
        
        new_dom = {
            "url": "https://example.com/page2",
            "elements": [
                {"tag": "div", "text": "Page 2", "xpath": "//div[1]"}
            ]
        }
        
        # Track reindexing
        reindex_called = False
        
        def mock_reindex():
            nonlocal reindex_called
            reindex_called = True
        
        with patch.object(pipeline, '_reindex_dom', side_effect=mock_reindex):
            with patch.object(pipeline, '_get_dom_snapshot', side_effect=[initial_dom, new_dom]):
                # Process initial page
                pipeline.process("find content", initial_dom)
                
                # Simulate route change
                pipeline._handle_route_change("https://example.com/page1", "https://example.com/page2")
                
                assert reindex_called
    
    def test_no_reload_on_spa_navigation(self, pipeline):
        """Test that SPA navigation doesn't trigger full page reload."""
        reload_called = False
        
        def mock_reload():
            nonlocal reload_called
            reload_called = True
        
        with patch.object(pipeline, '_full_page_reload', side_effect=mock_reload):
            # Simulate SPA navigation
            pipeline._handle_pushstate("https://example.com/page1", "https://example.com/page2")
            
            # Should NOT trigger full reload
            assert not reload_called
    
    def test_spa_state_preservation(self, pipeline):
        """Test that SPA state is preserved across route changes."""
        # Set some state
        pipeline._spa_state = {"user": "test", "session": "abc123"}
        
        # Simulate route change
        with patch.object(pipeline, '_reindex_dom'):
            pipeline._handle_route_change("https://example.com/page1", "https://example.com/page2")
        
        # State should be preserved
        assert pipeline._spa_state == {"user": "test", "session": "abc123"}
    
    def test_route_listener_registration(self, pipeline):
        """Test that route listeners are properly registered."""
        listeners = []
        
        def mock_add_listener(event_type, callback):
            listeners.append(event_type)
        
        with patch.object(pipeline, '_add_browser_listener', side_effect=mock_add_listener):
            pipeline._register_spa_listeners()
        
        # Should register all SPA events
        expected_events = ['pushState', 'replaceState', 'popstate', 'hashchange']
        for event in expected_events:
            assert event in listeners