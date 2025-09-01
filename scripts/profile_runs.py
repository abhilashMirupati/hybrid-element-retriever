#!/usr/bin/env python3
import time
import json
from pathlib import Path

from her.pipeline import HERPipeline, PipelineConfig


def profile_once(name: str, query: str, dom_elements: int = 200):
    cfg = PipelineConfig()
    pipe = HERPipeline(cfg)
    dom = {"elements": [
        {"tag": "div", "text": f"Element {i}", "xpath": f"//div[{i}]"}
        for i in range(dom_elements)
    ]}
    # Cold
    t0 = time.perf_counter()
    pipe.process(query, dom)
    cold = time.perf_counter() - t0
    # Warm
    t1 = time.perf_counter()
    pipe.process(query, dom)
    warm = time.perf_counter() - t1
    return {
        "name": name,
        "query": query,
        "elements": dom_elements,
        "cold_s": cold,
        "warm_s": warm,
        "speedup": (cold / warm) if warm > 0 else None,
    }


def main():
    cases = [
        ("small", "find element 10", 200),
        ("medium", "find element 50", 1000),
    ]
    results = [profile_once(n, q, k) for n, q, k in cases]
    perf = {
        "profiles": results,
        "notes": "Cold vs warm timings of HERPipeline on synthetic DOM snapshots.",
    }
    Path("PERF_REPORT.md").write_text(
        "\n".join(
            [
                "# Performance Report",
                *(f"- {r['name']}: cold={r['cold_s']:.3f}s, warm={r['warm_s']:.3f}s, speedup={r['speedup']:.2f}x" for r in results),
            ]
        )
    )
    Path("perf_results.json").write_text(json.dumps(perf, indent=2))


if __name__ == "__main__":
    main()

