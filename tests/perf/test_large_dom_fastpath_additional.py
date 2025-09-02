# tests/perf/test_large_dom_fastpath_additional.py
"""
Large DOM fast-path test:
- Builds a 3300-element synthetic descriptor list (pure Python).
- Ensures HERPipeline resolves by O(1) text fast-path under 2 seconds.
- Asserts deterministic output and presence of key metadata fields.
- No browsers or sleeps; safe for -n auto.
"""

import time

from src.her.compat import HERPipeline  # type: ignore


def _large_element_descriptors(n=3300):
    # Synthetic canonical descriptors (mimic extractor output)
    els = []
    for i in range(1, n + 1):
        els.append(
            {
                "tag": "div",
                "text": f"Element {i}",
                "attributes": {
                    "data-idx": str(i),
                    # include some innocuous noise fields
                    "title": f"Card {i}"
                },
                "is_visible": True,
                "computed_xpath": f"//div[@data-idx='{i}']",
                "frame_path": [],
                "in_shadow_dom": False,
            }
        )
    # Mark first element as shadow-like to ensure metadata field is respected
    els[0]["in_shadow_dom"] = True
    return els


def test_large_dom_text_fast_under_2s_and_deterministic(tmp_path):
    pipeline = HERPipeline(cache_dir=tmp_path)  # isolated cache for -n auto
    elements = _large_element_descriptors(3300)
    query = "find element 1234"

    # First run: must hit text-fast path and be < 2s
    t0 = time.perf_counter()
    out1 = pipeline.process(query, {"elements": elements})
    t1 = time.perf_counter()
    elapsed = t1 - t0

    assert isinstance(out1, dict), "Pipeline must return a dict"
    assert "strategy" in out1 and isinstance(out1["strategy"], str)
    # Strategy must explicitly reflect the O(1) text fast-path
    assert out1["strategy"] == "text-fast", f"Expected 'text-fast', got {out1['strategy']!r}"
    assert "xpath" in out1 and isinstance(out1["xpath"], str)
    # The chosen xpath should correspond to element 1234
    assert "1234" in out1["xpath"], f"XPath should target the requested element: {out1['xpath']}"
    assert elapsed < 2.0, f"Large DOM fast-path should complete <2s, got {elapsed:.2f}s"

    # Metadata checks
    md = out1.get("metadata", {})
    assert isinstance(md, dict), "metadata must be present as a dict"
    assert "in_shadow_dom" in md, "metadata must include in_shadow_dom"
    assert isinstance(md["in_shadow_dom"], bool), "in_shadow_dom must be bool"

    # Determinism: second run must produce identical result
    out2 = pipeline.process(query, {"elements": elements})
    assert out2 == out1, "Fast-path must be deterministic across runs"
