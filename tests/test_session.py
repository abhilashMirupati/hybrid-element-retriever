"""Tests for session management."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import time

from her.session.manager import SessionManager, SessionState


class TestSessionManager:
    """Test session manager."""
    
    def test_init(self):
        """Test initialization."""
        manager = SessionManager()
        assert manager.auto_index == True
        assert manager.reindex_on_change == True
        assert manager.reindex_on_failure == True
        assert len(manager.sessions) == 0
    
    def test_create_session(self):
        """Test session creation."""
        manager = SessionManager()
        
        session = manager.create_session("test_session")
        assert session.session_id == "test_session"
        assert session.auto_index_enabled == True
        assert session.last_indexed is None
        assert len(session.element_descriptors) == 0
        
        # Creating same session returns existing
        session2 = manager.create_session("test_session")
        assert session2 is session
    
    def test_get_session(self):
        """Test getting session."""
        manager = SessionManager()
        
        assert manager.get_session("nonexistent") is None
        
        manager.create_session("test")
        session = manager.get_session("test")
        assert session is not None
        assert session.session_id == "test"
    
    def test_destroy_session(self):
        """Test destroying session."""
        manager = SessionManager()
        
        manager.create_session("test")
        assert "test" in manager.sessions
        
        manager.destroy_session("test")
        assert "test" not in manager.sessions
    
    def test_should_reindex_never_indexed(self):
        """Test reindex check for never indexed session."""
        manager = SessionManager()
        session = manager.create_session("test")
        
        assert manager.should_reindex(session) == True
    
    def test_should_reindex_time_based(self):
        """Test time-based reindex check."""
        manager = SessionManager(index_interval_seconds=1)
        session = manager.create_session("test")
        session.last_indexed = datetime.now() - timedelta(seconds=2)
        
        assert manager.should_reindex(session) == True
        
        session.last_indexed = datetime.now()
        assert manager.should_reindex(session) == False
    
    @patch('her.session.manager.PLAYWRIGHT_AVAILABLE', True)
    def test_should_reindex_url_change(self):
        """Test URL change reindex check."""
        manager = SessionManager()
        session = manager.create_session("test")
        session.last_indexed = datetime.now()
        session.url = "https://example.com"
        
        mock_page = Mock()
        mock_page.url = "https://different.com"
        
        assert manager.should_reindex(session, mock_page) == True
        
        mock_page.url = "https://example.com"
        assert manager.should_reindex(session, mock_page) == False
    
    @patch('her.session.manager.capture_snapshot')
    def test_should_reindex_dom_change(self, mock_capture):
        """Test DOM change reindex check."""
        manager = SessionManager(reindex_on_change=True)
        session = manager.create_session("test")
        session.last_indexed = datetime.now()
        session.dom_hash = "old_hash"
        
        mock_capture.return_value = ([], "new_hash")
        mock_page = Mock()
        
        assert manager.should_reindex(session, mock_page) == True
        
        mock_capture.return_value = ([], "old_hash")
        assert manager.should_reindex(session, mock_page) == False
    
    @patch('her.session.manager.capture_snapshot')
    def test_index_page(self, mock_capture):
        """Test page indexing."""
        manager = SessionManager()
        mock_page = Mock()
        mock_page.url = "https://example.com"
        
        mock_descriptors = [
            {"backendNodeId": 1, "tag": "button", "text": "Click me"}
        ]
        mock_capture.return_value = (mock_descriptors, "test_hash")
        
        descriptors, dom_hash = manager.index_page("test", mock_page)
        
        assert descriptors == mock_descriptors
        assert dom_hash == "test_hash"
        
        session = manager.get_session("test")
        assert session.element_descriptors == mock_descriptors
        assert session.dom_hash == "test_hash"
        assert session.url == "https://example.com"
        assert session.index_count == 1
    
    def test_get_cache_key(self):
        """Test cache key generation."""
        manager = SessionManager()
        session = manager.create_session("test")
        session.url = "https://example.com"
        session.frame_path = "main"
        session.dom_hash = "abc123"
        
        key = manager.get_cache_key("test")
        assert key == "https://example.com|main|abc123"
    
    def test_export_session(self):
        """Test session export."""
        manager = SessionManager()
        session = manager.create_session("test")
        session.url = "https://example.com"
        session.dom_hash = "test_hash"
        session.index_count = 5
        session.element_descriptors = [1, 2, 3]
        
        exported = manager.export_session("test")
        
        assert exported["session_id"] == "test"
        assert exported["url"] == "https://example.com"
        assert exported["dom_hash"] == "test_hash"
        assert exported["index_count"] == 5
        assert exported["element_count"] == 3
    
    def test_get_stats(self):
        """Test statistics."""
        manager = SessionManager()
        
        session1 = manager.create_session("test1")
        session1.element_descriptors = [1, 2, 3]
        session1.index_count = 2
        
        session2 = manager.create_session("test2")
        session2.element_descriptors = [4, 5]
        session2.index_count = 1
        
        stats = manager.get_stats()
        
        assert stats["session_count"] == 2
        assert stats["total_elements"] == 5
        assert stats["total_indexes"] == 3
        assert stats["auto_index"] == True