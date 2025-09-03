import os
import pytest
from her.browser import snapshot_sync

def _use_network() -> bool:
    return os.environ.get("HER_TEST_USE_NETWORK", "1") not in {"0", "false", "False"}

@pytest.mark.timeout(60)
def test_smoke_snapshot():
    url = "https://example.com" if _use_network() else "data:text/html,<h1>Title</h1><a href='#'>Link</a><button>Btn</button>"
    items = snapshot_sync(url, timeout_ms=15000)
    assert isinstance(items, list)
    assert len(items) >= 3
    for it in items[:5]:
        assert set(("text","tag","role","attrs","xpath","bbox")).issubset(it.keys())
        assert isinstance(it["text"], str)
        assert isinstance(it["tag"], str)
        assert isinstance(it["xpath"], str)
        bb = it["bbox"]
        assert isinstance(bb["w"], int) and isinstance(bb["h"], int)
        assert bb["w"] >= 0 and bb["h"] >= 0

@pytest.mark.timeout(60)
def test_xpath_unique_and_stable():
    url = "https://example.com" if _use_network() else "data:text/html,<h1>Title</h1><a href='#'>Link</a><button>Btn</button>"
    r1 = snapshot_sync(url, timeout_ms=15000)
    r2 = snapshot_sync(url, timeout_ms=15000)
    x1 = [it["xpath"] for it in r1]
    x2 = [it["xpath"] for it in r2]
    assert len(set(x1)) == len(x1)
    assert len(set(x2)) == len(x2)
    k = min(5, len(x1), len(x2))
    assert k >= 1
    assert x1[:k] == x2[:k]

@pytest.mark.timeout(20)
def test_timeout_error():
    with pytest.raises(TimeoutError):
        snapshot_sync("http://10.255.255.1", timeout_ms=2000)
