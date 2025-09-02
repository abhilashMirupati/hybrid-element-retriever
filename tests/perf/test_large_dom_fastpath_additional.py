import time
import pytest

from src.her.compat import HERPipeline  # type: ignore


def _large_elements(n=3200):
    els = []
    for i in range(1, n + 1):
        els.append({
            "tag": "div",
            "text": f"Element {i}",
            "attributes": {"data-idx": str(i)},
            "is_visible": True,
            "computed_xpath": f"//div[@data-idx='{i}']",
        })
    # mark one as shadow-dom-like by convention
    if els:
        els[0]["attributes"]["in_shadow_dom"] = True
    return els


def test_large_dom_text_fast_under_2s_and_deterministic():
    p = HERPipeline()  # type: ignore[call-arg]
    elements = _large_elements(3300)
    query = "find element 1234"

    t0 = time.perf_counter()
    out1 = p.process(query, {"elements": elements})  # type: ignore[attr-defined]
    t1 = time.perf_counter()

    elapsed = (t1 - t0)
    assert elapsed < 2.0, f"Large DOM fast-path should finish under 2s, got {elapsed:.2f}s"

    assert isinstance(out1, dict)
    assert out1.get("strategy") == "text-fast", "Expected O(1) text fast-path"
    assert "xpath" in out1 and isinstance(out1["xpath"], str)
    # In many implementations, xpath will reflect computed_xpath of the chosen element
    assert "1234" in out1["xpath"], "Chosen xpath should correspond to target element"

    # Metadata must include in_shadow_dom (bool)
    md = out1.get("metadata", {})
    assert "in_shadow_dom" in md and isinstance(md["in_shadow_dom"], bool)

    # Deterministic: run again; same result
    out2 = p.process(query, {"elements": elements})  # type: ignore[attr-defined]
    assert out1 == out2
