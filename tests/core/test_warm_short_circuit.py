# tests/core/test_warm_short_circuit.py
"""
Tests for HERPipeline warm-path short-circuiting.
- Cold run should be slower than warm.
- Warm reuses cached result exactly (xpath, strategy, metadata).
"""

import time

from src.her.compat import HERPipeline


def build_small_dom():
    # Minimal DOM with unique elements
    return """
    <html>
      <body>
        <div id="e1">element 1</div>
        <div id="e2">element 2</div>
        <div id="e3">element 3</div>
      </body>
    </html>
    """


def test_warm_short_circuit_speed_and_consistency(tmp_path):
    pipeline = HERPipeline(cache_dir=tmp_path)

    dom = build_small_dom()
    query = "find element 2"

    # Cold run
    t1 = time.perf_counter()
    out1 = pipeline.process(query, {"html": dom})
    cold_time = time.perf_counter() - t1

    assert out1 and "xpath" in out1
    xpath1, strategy1, metadata1 = out1["xpath"], out1["strategy"], out1["metadata"]

    # Warm run (should be much faster, identical result)
    t2 = time.perf_counter()
    out2 = pipeline.process(query, {"html": dom})
    warm_time = time.perf_counter() - t2

    assert out2["xpath"] == xpath1
    assert out2["strategy"] == strategy1
    assert out2["metadata"] == metadata1

    # Warm is at least 3x faster
    assert cold_time > 0
    assert warm_time * 3 < cold_time

    # Cache check: key should exist
    cached = pipeline.cache.get_raw(query)
    assert cached is not None
    assert cached["xpath"] == xpath1
