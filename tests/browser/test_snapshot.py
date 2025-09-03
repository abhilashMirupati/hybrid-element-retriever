import os
import time

import pytest

from her.browser import snapshot_sync


def _has_network() -> bool:
    # Heuristic: CI environment may block outbound - allow opt-out via env var
    return os.environ.get("HER_TEST_USE_NETWORK", "1") not in {"0", "false", "False"}


@pytest.mark.timeout(60)
def test_example_com_smoke():
    if _has_network():
        url = "https://example.com"
        result = snapshot_sync(url, timeout_ms=15000)
    else:
        # Fallback: no network; use data URL to load static HTML
        html = """
        <html><body>
            <h1>Example Domain</h1>
            <p>This domain is for use in illustrative examples.</p>
            <a href="/more">More information...</a>
            <button id="go">Go</button>
            <input aria-label="search" />
        </body></html>
        """
        # Use a data URL to avoid network; Playwright can navigate to it
        data_url = "data:text/html," + html.replace("\n", "%0A").replace(" ", "%20")
        result = snapshot_sync(data_url, timeout_ms=15000)

    assert isinstance(result, list)
    assert len(result) >= 5
    required = {"text", "tag", "role", "attrs", "xpath", "bbox"}
    for item in result:
        assert required.issubset(item.keys())
        assert isinstance(item["tag"], str)
        assert isinstance(item["xpath"], str)
        bb = item["bbox"]
        assert bb["w"] >= 0 and bb["h"] >= 0


@pytest.mark.timeout(60)
def test_xpath_unique_stable():
    url = "https://example.com" if _has_network() else "data:text/html,<h1>Title</h1><a href=\"#\">Link</a><button>Btn</button>"
    r1 = snapshot_sync(url, timeout_ms=15000)
    r2 = snapshot_sync(url, timeout_ms=15000)
    x1 = [it["xpath"] for it in r1]
    x2 = [it["xpath"] for it in r2]
    # Uniqueness within a run
    assert len(set(x1)) == len(x1)
    assert len(set(x2)) == len(x2)
    # Stability for first 5
    k = min(5, len(x1), len(x2))
    assert k >= 1
    assert x1[:k] == x2[:k]


@pytest.mark.timeout(20)
def test_timeout():
    # unroutable TEST-NET-2 style IP often used for timeout testing
    with pytest.raises(TimeoutError):
        snapshot_sync("http://10.255.255.1", timeout_ms=2000)

