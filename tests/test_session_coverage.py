"""Tests to improve session manager coverage."""

from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import pytest

from her.session.manager import SessionManager, SessionState


class TestSessionCoverage:
    """Test session manager for coverage."""

    def test_session_state_init(self):
        """Test SessionState initialization."""
        state = SessionState(session_id="test123")
        assert state.session_id == "test123"
        assert state.created_at is not None
        assert state.last_indexed is None
        assert state.url is None
        assert state.frame_path == "main"
        assert state.dom_hash is None
        assert state.element_descriptors == []
        assert state.index_count == 0
        assert state.auto_index_enabled is True

    @patch("her.session.manager.PLAYWRIGHT_AVAILABLE", False)
    def test_session_manager_no_playwright(self):
        """Test session manager without Playwright."""
        manager = SessionManager()
        assert manager.sessions == {}
        assert manager.auto_index is True

    def test_session_manager_get_session_for_page_not_found(self):
        """Test get session for page when not found."""
        manager = SessionManager()
        mock_page = Mock()

        result = manager.get_session_for_page(mock_page)
        assert result is None

    def test_session_manager_get_session_for_page_found(self):
        """Test get session for page when found."""
        manager = SessionManager()
        session = manager.create_session("test")

        mock_page = Mock()
        manager._page_to_session[mock_page] = "test"

        result = manager.get_session_for_page(mock_page)
        assert result == session

    def test_session_manager_trigger_reindex_disabled(self):
        """Test trigger reindex when disabled."""
        manager = SessionManager(reindex_on_failure=False)

        result = manager.trigger_reindex_on_failure("test", None, None)
        assert result is False

    def test_session_manager_trigger_reindex_no_session(self):
        """Test trigger reindex with no session."""
        manager = SessionManager(reindex_on_failure=True)

        result = manager.trigger_reindex_on_failure("nonexistent", None, None)
        assert result is False

    def test_session_manager_get_cache_key_no_session(self):
        """Test get cache key with no session."""
        manager = SessionManager()

        key = manager.get_cache_key("nonexistent")
        assert "unknown" in key

    def test_session_manager_get_cache_key_with_session(self):
        """Test get cache key with session."""
        manager = SessionManager()
        session = manager.create_session("test")
        session.url = "http://example.com"
        session.frame_path = "main"
        session.dom_hash = "abc123"

        key = manager.get_cache_key("test")
        assert "http://example.com" in key
        assert "main" in key
        assert "abc123" in key

    def test_session_manager_export_session_not_found(self):
        """Test export session when not found."""
        manager = SessionManager()

        result = manager.export_session("nonexistent")
        assert result == {}

    def test_session_manager_export_session_found(self):
        """Test export session when found."""
        manager = SessionManager()
        session = manager.create_session("test")
        session.url = "http://example.com"
        session.index_count = 5

        result = manager.export_session("test")
        assert result["session_id"] == "test"
        assert result["url"] == "http://example.com"
        assert result["index_count"] == 5

    def test_session_manager_get_stats_empty(self):
        """Test get stats with no sessions."""
        manager = SessionManager()

        stats = manager.get_stats()
        assert stats["session_count"] == 0
        assert stats["total_elements"] == 0
        assert stats["total_indexes"] == 0

    def test_session_manager_get_stats_with_sessions(self):
        """Test get stats with sessions."""
        manager = SessionManager()

        session1 = manager.create_session("test1")
        session1.element_descriptors = [{"id": 1}, {"id": 2}]
        session1.index_count = 3

        session2 = manager.create_session("test2")
        session2.element_descriptors = [{"id": 3}]
        session2.index_count = 1

        stats = manager.get_stats()
        assert stats["session_count"] == 2
        assert stats["total_elements"] == 3
        assert stats["total_indexes"] == 4
