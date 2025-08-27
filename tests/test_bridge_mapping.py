from her.bridge.snapshot import capture_snapshot


def test_capture_snapshot_returns_list() -> None:
    data = capture_snapshot()
    assert isinstance(data, list)