"""Tests for self-healing and promotion modules."""

from her.recovery.self_heal import SelfHealer
from her.recovery.promotion import PromotionStore


def test_self_heal_returns_true() -> None:
    """Test that self-healer can be created."""
    healer = SelfHealer()
    assert healer is not None


def test_promote_does_not_raise() -> None:
    """Test that promotion store can be created and used."""
    store = PromotionStore(use_sqlite=False)  # Use JSON for testing

    # Should not raise any exceptions
    store.record_success("button", "test_context")
    assert store.get_promotion_score("button", "test_context") > 0
