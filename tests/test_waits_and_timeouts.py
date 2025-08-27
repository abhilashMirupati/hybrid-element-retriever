from her.config import DEFAULT_CONFIG, HERConfig


def test_default_config_values() -> None:
    cfg = DEFAULT_CONFIG
    assert cfg.dom_max_wait_ms == 10000
    assert cfg.auto_index is True


def test_override_config() -> None:
    cfg = HERConfig(dom_max_wait_ms=5000, auto_index=False)
    assert cfg.dom_max_wait_ms == 5000
    assert cfg.auto_index is False