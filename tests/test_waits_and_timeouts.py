"""Tests for configuration and timeouts."""

from her.config import (
    DEFAULT_TIMEOUT_MS,
    DEFAULT_WAIT_MS,
    DEFAULT_SETTLE_MS,
    AUTO_INDEX_THRESHOLD,
)


def test_default_config_values() -> None:
    """Test that default configuration values are set correctly."""
    assert DEFAULT_TIMEOUT_MS == 30000
    assert DEFAULT_WAIT_MS == 100
    assert DEFAULT_SETTLE_MS == 500
    assert AUTO_INDEX_THRESHOLD == 0.3


def test_timeout_values_are_reasonable() -> None:
    """Test that timeout values are reasonable."""
    assert DEFAULT_TIMEOUT_MS > 0
    assert DEFAULT_TIMEOUT_MS <= 60000  # Max 1 minute
    assert DEFAULT_WAIT_MS >= 0
    assert DEFAULT_WAIT_MS <= 5000  # Max 5 seconds
    assert DEFAULT_SETTLE_MS >= 0
    assert DEFAULT_SETTLE_MS <= 5000  # Max 5 seconds
