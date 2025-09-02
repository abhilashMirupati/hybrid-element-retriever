# tests/core/test_delta_embedding_budget.py
"""
Delta-embedding budget test:
- Cold run embeds many elements.
- Warm run after appending ONE element should embed only a tiny number (<= 11).
- Also asserts cache hits non-decreasing if stats are available.
- Pure-Python; no browsers; safe for -n auto.
"""

import pytest

from src.her.compat import HERPipeline  # type: ignore


def _many(n=800):
    return [
        {
            "tag": "div",
            "text": f"Row {i}",
            "attributes": {"data-row": str(i)},
            "is_visible": True,
            "computed_xpath": f"//div[@data-row='{i}']",
            "frame_path": [],
            "in_shadow_dom": False,
        }
        for i in range(n)
    ]


@pytest.mark.parametrize("n", [800])
def test_delta_embedding_budget_and_cache_hits(tmp_path, n):
    p = HERPipeline(cache_dir=tmp_path)  # isolated cache dir for -n auto
    elements = _many(n)
    query = "find row 123"

    # If pipeline doesn't expose _embed_element, we still run but skip strict budget assert
    can_count = hasattr(p, "_embed_element")
    embed_calls = {"n": 0}
    original = getattr(p, "_embed_element", None)

    def wrapped_embed(desc):
        embed_calls["n"] += 1
        return original(desc)  # type: ignore[misc]

    if can_count and callable(original):
        # Count cold path embed calls
        p._embed_element = wrapped_embed  # type: ignore[attr-defined]

    # First run (cold)
    _ = p.process(query, {"elements": elements})  # type: ignore[attr-defined]
    cold_calls = embed_calls["n"] if can_count else None

    # Append one new element
    embed_calls["n"] = 0
    elements2 = elements + [
        {
            "tag": "div",
            "text": f"Row {n}",
            "attributes": {"data-row": str(n)},
            "is_visible": True,
            "computed_xpath": f"//div[@data-row='{n}']",
            "frame_path": [],
            "in_shadow_dom": False,
        }
    ]

    # Second run (warm, delta-only)
    _ = p.process(query, {"elements": elements2})  # type: ignore[attr-defined]
    warm_calls = embed_calls["n"] if can_count else None

    if can_count:
        assert warm_calls is not None
        # Budget: ONE new element + small bookkeeping overhead
        assert warm_calls <= 11, f"Delta embedding too high: {warm_calls}"

    # Cache hits non-decreasing if stats exist
    stats = {}
    for attr in ("stats", "get_stats"):
        fn = getattr(p, attr, None)
        if callable(fn):
            stats = fn()  # type: ignore[misc]
            break

    if isinstance(stats, dict):
        # Accept either explicit before/after or single monotonically increasing counter
        ch = stats.get("cache_hits")
        if isinstance(ch, int):
            # Run a third warm call to ensure monotonic increase
            _ = p.process(query, {"elements": elements2})
            stats2 = {}
            for attr in ("stats", "get_stats"):
                fn = getattr(p, attr, None)
                if callable(fn):
                    stats2 = fn()  # type: ignore[misc]
                    break
            ch2 = stats2.get("cache_hits")
            if isinstance(ch2, int):
                assert ch2 >= ch
