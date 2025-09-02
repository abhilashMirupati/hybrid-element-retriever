import time
import json
import pathlib
import pytest

# Only use HERPipeline from compat
from src.her.compat import HERPipeline  # type: ignore


def _elements_small():
    # Minimal, pure-Python descriptors; pipeline should accept via context={'elements': ...}
    return [
        {"tag": "div", "text": "element 1", "attributes": {}, "is_visible": True, "computed_xpath": "//div[@data-idx='1']"},
        {"tag": "div", "text": "element 2", "attributes": {}, "is_visible": True, "computed_xpath": "//div[@data-idx='2']"},
        {"tag": "div", "text": "element 3", "attributes": {}, "is_visible": True, "computed_xpath": "//div[@data-idx='3']"},
        {"tag": "button", "text": "go", "attributes": {"role": "button"}, "is_visible": True, "computed_xpath": "//button[1]"},
    ]


def test_warm_short_circuit_and_query_cache(monkeypatch):
    p = HERPipeline()  # type: ignore[call-arg]

    query = "find element 2"
    ctx = {"elements": _elements_small()}

    t0 = time.perf_counter()
    out1 = p.process(query, ctx)  # type: ignore[attr-defined]
    t1 = time.perf_counter()

    # second call on same query+DOM should be much faster (≥3x)
    t2 = time.perf_counter()
    out2 = p.process(query, ctx)  # type: ignore[attr-defined]
    t3 = time.perf_counter()

    cold_ms = (t1 - t0) * 1000.0
    warm_ms = (t3 - t2) * 1000.0

    # Same exact result (including strategy/metadata)
    assert isinstance(out1, dict) and isinstance(out2, dict)
    assert out1 == out2
    assert cold_ms > 0.1  # non-zero
    # 3x speedup without sleeps (pure algorithmic warm path)
    assert warm_ms <= (cold_ms / 3.0), f"Expected ≥3x speedup, got cold={cold_ms:.2f}ms warm={warm_ms:.2f}ms"

    # Ensure query-level cache stored the full output
    # Pipeline should expose cache.get_raw; accept either direct query key or internal key
    cache = getattr(p, "cache", None)
    assert cache is not None and hasattr(cache, "get_raw"), "Pipeline must expose cache.get_raw for warm path"

    # Try a couple of plausible keys
    got = cache.get_raw(query)  # type: ignore[attr-defined]
    if not got:
        key_fn = getattr(p, "_make_query_cache_key", None)
        if callable(key_fn):
            got = cache.get_raw(key_fn(query))  # type: ignore[attr-defined]

    assert got, "Expected cached record for query"
    assert isinstance(got, dict)
    # cached object should contain main fields from result
    for k in ("xpath", "strategy", "metadata"):
        assert k in got
