from her.recovery.self_heal import self_heal
from her.recovery.promotion import promote_locator


def test_self_heal_returns_true() -> None:
    assert self_heal() is True


def test_promote_does_not_raise() -> None:
    # Should not raise any exceptions
    promote_locator({"selector": "button"})