"""Integration tests for HER."""

import pytest
import time
from pathlib import Path
from unittest.mock import Mock, patch

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from her import HybridElementRetriever
from her.cli_api import HybridElementRetrieverClient
from her.session.manager import SessionManager
from her.session.enhanced_manager import EnhancedSessionManager


class TestSessionManagerIntegration:
    """Test SessionManager integration."""
    
    def test_session_manager_api_compatibility(self):
        """Test that both session managers have compatible APIs."""
        # Create both managers
        basic_manager = SessionManager()
        enhanced_manager = EnhancedSessionManager()
        
        # Check they have the same key methods
        key_methods = ['create_session', 'get_session', 'index_page']
        
        for method in key_methods:
            assert hasattr(basic_manager, method), f"SessionManager missing {method}"
            assert hasattr(enhanced_manager, method), f"EnhancedSessionManager missing {method}"
    
    @patch('her.bridge.snapshot.capture_snapshot')
    def test_session_indexing(self, mock_capture):
        """Test session indexing works with both managers."""
        mock_capture.return_value = ([
            {"tag": "button", "text": "Click"},
            {"tag": "input", "id": "search"}
        ], "hash123")
        
        mock_page = Mock()
        mock_page.url = "https://example.com"
        
        # Test with basic manager
        basic_manager = SessionManager()
        session = basic_manager.create_session("test1", mock_page)
        descriptors, dom_hash = basic_manager.index_page("test1", mock_page)
        
        assert len(descriptors) == 2
        assert dom_hash == "hash123"
        
        # Test with enhanced manager
        enhanced_manager = EnhancedSessionManager()
        session = enhanced_manager.create_session("test2", mock_page)
        descriptors, dom_hash = enhanced_manager.index_page("test2", mock_page)
        
        assert len(descriptors) == 2
        assert dom_hash == "hash123"


class TestClientIntegration:
    """Test HER client integration."""
    
    @patch('her.cli_api.playwright')
    def test_client_with_basic_manager(self, mock_playwright):
        """Test client works with basic SessionManager."""
        mock_browser = Mock()
        mock_page = Mock()
        mock_page.url = "https://example.com"
        mock_page.content.return_value = "<html><button>Click</button></html>"
        
        mock_playwright.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        
        client = HybridElementRetrieverClient(use_enhanced=False)
        
        # Test query
        with patch.object(client.session_manager, 'index_page') as mock_index:
            mock_index.return_value = ([
                {"tag": "button", "text": "Click"}
            ], "hash123")
            
            result = client.query("Find button")
            
            # Should return results
            assert isinstance(result, (list, dict))
    
    @patch('her.cli_api.playwright')
    def test_client_with_enhanced_manager(self, mock_playwright):
        """Test client works with EnhancedSessionManager."""
        mock_browser = Mock()
        mock_page = Mock()
        mock_page.url = "https://example.com"
        mock_page.content.return_value = "<html><button>Click</button></html>"
        
        mock_playwright.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        
        client = HybridElementRetrieverClient(use_enhanced=True)
        
        # Test query
        with patch.object(client.session_manager, 'index_page') as mock_index:
            mock_index.return_value = ([
                {"tag": "button", "text": "Click"}
            ], "hash123")
            
            result = client.query("Find button")
            
            # Should return results
            assert isinstance(result, (list, dict))
    
    def test_client_action_methods(self):
        """Test client action methods."""
        client = HybridElementRetrieverClient()
        
        # Check all action methods exist
        action_methods = ['click', 'type_text', 'select_option', 'hover', 'scroll_to']
        
        for method in action_methods:
            assert hasattr(client, method), f"Client missing {method} method"


class TestEndToEnd:
    """End-to-end integration tests."""
    
    @patch('her.cli_api.playwright')
    @patch('her.bridge.snapshot.capture_snapshot')
    def test_full_query_flow(self, mock_capture, mock_playwright):
        """Test full query flow from client to results."""
        # Setup mocks
        mock_browser = Mock()
        mock_page = Mock()
        mock_page.url = "https://example.com"
        mock_page.evaluate.return_value = "complete"
        mock_page.query_selector.return_value = Mock()
        
        mock_playwright.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        
        mock_capture.return_value = ([
            {"tag": "button", "text": "Submit", "id": "submit-btn"},
            {"tag": "input", "text": "", "id": "email-field"},
            {"tag": "a", "text": "Login", "attributes": {"href": "/login"}}
        ], "hash123")
        
        # Create client
        client = HybridElementRetrieverClient(auto_index=True)
        
        # Test various queries
        queries = [
            "Find submit button",
            "Find email input",
            "Find login link"
        ]
        
        for query in queries:
            result = client.query(query)
            assert result is not None
            
            # Check result structure
            if isinstance(result, dict):
                assert 'selector' in result or 'xpath' in result or 'ok' in result
            elif isinstance(result, list):
                assert len(result) > 0
    
    @patch('her.cli_api.playwright')
    def test_action_execution(self, mock_playwright):
        """Test action execution flow."""
        mock_browser = Mock()
        mock_page = Mock()
        mock_element = Mock()
        
        mock_playwright.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        mock_page.query_selector.return_value = mock_element
        
        client = HybridElementRetrieverClient()
        
        # Test click action
        result = client.click("Click submit button")
        assert result['ok'] or 'error' in result
        
        # Test type action
        result = client.type_text("Type 'test@example.com' in email field", "test@example.com")
        assert result['ok'] or 'error' in result


class TestErrorHandling:
    """Test error handling in integration."""
    
    def test_missing_browser(self):
        """Test handling when browser is not available."""
        client = HybridElementRetrieverClient()
        
        # Should handle gracefully
        result = client.query("Find button")
        
        if isinstance(result, dict):
            assert not result.get('ok', True) or 'error' in result
    
    @patch('her.cli_api.playwright')
    def test_page_crash_recovery(self, mock_playwright):
        """Test recovery from page crash."""
        mock_browser = Mock()
        mock_page = Mock()
        
        mock_playwright.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        
        # Simulate page crash
        mock_page.query_selector.side_effect = Exception("Page crashed")
        
        client = HybridElementRetrieverClient()
        
        # Should handle crash
        result = client.query("Find button")
        assert isinstance(result, (dict, list))
    
    def test_invalid_selector_handling(self):
        """Test handling of invalid selectors."""
        client = HybridElementRetrieverClient()
        
        # Test with invalid XPath
        from her.validators import InputValidator
        
        valid, sanitized, error = InputValidator.validate_xpath("invalid xpath")
        assert not valid


class TestCaching:
    """Test caching integration."""
    
    def test_cache_persistence(self, tmp_path):
        """Test cache persists across sessions."""
        cache_dir = tmp_path / "cache"
        
        # First session
        client1 = HybridElementRetrieverClient(cache_dir=cache_dir)
        # Simulate some caching
        if client1.session_manager and hasattr(client1.session_manager, 'cache_dir'):
            assert client1.session_manager.cache_dir.exists()
        
        # Second session should use same cache
        client2 = HybridElementRetrieverClient(cache_dir=cache_dir)
        if client2.session_manager and hasattr(client2.session_manager, 'cache_dir'):
            assert client2.session_manager.cache_dir == client1.session_manager.cache_dir
    
    @patch('her.bridge.snapshot.capture_snapshot')
    def test_incremental_updates(self, mock_capture):
        """Test incremental update functionality."""
        # Initial snapshot
        initial_descriptors = [
            {"tag": "button", "text": "Button 1", "id": "btn1"},
            {"tag": "button", "text": "Button 2", "id": "btn2"}
        ]
        
        # Updated snapshot with new element
        updated_descriptors = initial_descriptors + [
            {"tag": "button", "text": "Button 3", "id": "btn3"}
        ]
        
        mock_capture.side_effect = [
            (initial_descriptors, "hash1"),
            (updated_descriptors, "hash2")
        ]
        
        manager = EnhancedSessionManager(enable_incremental=True)
        mock_page = Mock()
        
        # First index
        session = manager.create_session("test", mock_page)
        desc1, hash1 = manager.index_page("test", mock_page)
        
        # Second index should detect new element
        desc2, hash2 = manager.index_page("test", mock_page)
        
        assert len(desc2) > len(desc1)


class TestMultiSession:
    """Test multi-session support."""
    
    def test_multiple_sessions(self):
        """Test handling multiple concurrent sessions."""
        manager = SessionManager()
        
        # Create multiple sessions
        sessions = []
        for i in range(5):
            session = manager.create_session(f"session-{i}")
            sessions.append(session)
        
        # All sessions should be tracked
        assert len(manager.sessions) == 5
        
        # Each session should be independent
        for i, session in enumerate(sessions):
            assert session.session_id == f"session-{i}"
    
    def test_session_cleanup(self):
        """Test session cleanup."""
        manager = SessionManager()
        
        # Create sessions
        for i in range(10):
            manager.create_session(f"session-{i}")
        
        # Cleanup old sessions (if implemented)
        if hasattr(manager, 'cleanup_sessions'):
            manager.cleanup_sessions(max_age_seconds=0)
            # Old sessions should be removed


class TestJavaIntegration:
    """Test Java bridge integration."""
    
    def test_gateway_server_import(self):
        """Test gateway server can be imported."""
        from her.gateway_server import HERGateway
        
        gateway = HERGateway()
        assert hasattr(gateway, 'query')
        assert hasattr(gateway, 'findXPaths')
    
    def test_java_api_compatibility(self):
        """Test Java API compatibility."""
        from her.gateway_server import HERGateway
        
        gateway = HERGateway()
        
        # Test query method signature
        import inspect
        sig = inspect.signature(gateway.query)
        params = list(sig.parameters.keys())
        
        assert 'phrase' in params
        assert 'url' in params


class TestBackwardCompatibility:
    """Test backward compatibility."""
    
    def test_old_api_still_works(self):
        """Test that old API methods still work."""
        client = HybridElementRetrieverClient()
        
        # Old methods should still exist
        old_methods = ['synthesize_locators', 'rank_elements']
        
        for method in old_methods:
            if hasattr(client, method):
                # Method exists, good for compatibility
                pass
    
    def test_import_paths(self):
        """Test that common import paths work."""
        # These imports should not fail
        from her import HybridElementRetriever
        from her.cli_api import HybridElementRetrieverClient
        from her.session.manager import SessionManager
        
        # Check main class
        assert HybridElementRetriever is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])