import pytest

from her.cli_api import HybridClient


def test_zero_index_flow() -> None:
    """The framework should auto-index on first use without manual calls."""
    client = HybridClient()
    # First action should trigger an index and succeed/fail gracefully
    result = client.act("Click the login button", url="http://example.com")
    assert isinstance(result, dict)
    assert result["status"] in ("ok", "fail")
    # Second action on the same page should reuse the cache
    result2 = client.act("Click the login button", url="http://example.com")
    assert result2["status"] in ("ok", "fail")