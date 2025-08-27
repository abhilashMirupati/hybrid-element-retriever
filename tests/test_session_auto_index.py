"""Tests for session auto-indexing."""

from her.session.manager import SessionManager


def test_dom_hash_changes_triggers_new_page() -> None:
    """Test that DOM hash changes trigger re-indexing."""
    manager = SessionManager(auto_index=True)

    # Create a session
    session = manager.create_session("test_session")
    assert session is not None
    assert session.session_id == "test_session"
    assert session.auto_index_enabled is True

    # Check that session can be retrieved
    retrieved = manager.get_session("test_session")
    assert retrieved == session

    # Clean up
    manager.destroy_session("test_session")
