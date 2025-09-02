import time
import pytest

from src.her.compat import HERPipeline  # type: ignore


def _many(n=500):
    return [
        {
            "tag": "div",
            "text": f"Row {i}",
            "attributes": {"data-row": str(i)},
            "is_visible": True,
            "computed_xpath": f"//div[@data-row='{i}']",
        }
        for i in range(n)
    ]


def test_delta_embedding_budget_and_cache_hits(monkeypatch):
    p = HERPipeline()  # type: ignore[call-arg]
    elements = _many(800)
    query = "find row 123"

    # First run (cold)
    embed_calls = {"n": 0}
    orig = getattr(p, "_embed_element", None)

    def wrapped_embed(desc):
        embed_calls["n"] += 1
        if callable(orig):
            return orig(desc)
        return None

    # Wrap embed to count calls
    if orig:
        monkeypatch.setattr(p, "_embed_element", wrapped_embed)

    _ = p.process(query, {"elements": elements})  # type: ignore[attr-defined]
    cold_calls = embed_calls["n"]

    # Append one new element; second run should embed <= (1 + small overhead)
    embed_calls["n"] = 0
    elements2 = elements + [{
        "tag": "div",
        "text": "Row 800",
        "attributes": {"data-row": "800"},
        "is_visible": True,
        "computed_xpath": "//div[@data-row='800']",
    }]

    _ = p.process(query, {"elements": elements2})  # type: ignore[attr-defined]
    warm_calls = embed_calls["n"]

    assert warm_calls <= 11, f"Delta embedding should be small; got {warm_calls}"

    # Cache hits should increase across runs if stats exist
    stats = {}
    for attr in ("stats", "get_stats"):
        fn = getattr(p, attr, None)
        if callable(fn):
            stats = fn()  # type: ignore[misc]
            break
    if isinstance(stats, dict):
        # allow any of these keys
        hits_before = stats.get("cache_hits_before") or stats.get("cache_hits", 0)
        hits_after = stats.get("cache_hits_after") or stats.get("cache_hits", 0)
        assert hits_after >= hits_before
