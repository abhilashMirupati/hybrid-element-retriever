from her.session.manager import SessionManager
from her.config import DEFAULT_CONFIG


def test_dom_hash_changes_triggers_new_page() -> None:
    manager = SessionManager(config=DEFAULT_CONFIG)
    info1 = manager.ensure_page("http://example.com")
    info2 = manager.ensure_page("http://example.org")
    assert info1["dom_hash"] != info2["dom_hash"]
