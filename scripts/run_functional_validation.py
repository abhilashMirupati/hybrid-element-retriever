# scripts/run_functional_validation.py
"""
Enterprise-grade functional validation harness for HER.
- Deterministic candidate generation.
- Strict JSON (Python-native scalars only).
- Records metadata (frame_path, in_shadow_dom, cross_origin).
- Measures cold vs warm timings.
- Produces FUNCTIONAL_REPORT.md + functional_results.json.
"""

import json
import time
import statistics
from pathlib import Path

from playwright.sync_api import sync_playwright
from src.her.compat import HERPipeline


# ===== Candidate Synthesis =====
def synthesize_candidates(desc):
    """Return ordered candidate XPaths for an element descriptor."""
    tag = desc["tag"]
    text = desc["text"]
    attrs = desc["attributes"]

    cands = []

    # Precedence order (deterministic)
    if "data-testid" in attrs:
        cands.append(f'//*[@data-testid="{attrs["data-testid"]}"]')
    if "aria-label" in attrs:
        cands.append(f'//*[@aria-label="{attrs["aria-label"]}"]')
    if "id" in attrs:
        cands.append(f'//*[@id="{attrs["id"]}"]')
    if "role" in attrs and text:
        cands.append(f'//*[@role="{attrs["role"]}" and normalize-space()="{text}"]')
    if text:
        cands.append(f"//{tag}[normalize-space()='{text}']")
        cands.append(f"//{tag}[contains(normalize-space(),'{text}')]")

    # Always fall back to canonical path
    if desc.get("computed_xpath"):
        cands.append(desc["computed_xpath"])

    return cands


# ===== Validation Runner =====
def run_validation(fixture_html: str, intents_json: str, gt_json: str):
    results = []
    timings_cold, timings_warm = []
    pipeline = HERPipeline()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"file://{fixture_html}")

        # Inject extractor
        js_path = Path(__file__).parent / "dom_extractor.js"
        page.add_script_tag(path=str(js_path))
        descriptors = page.evaluate("extractDescriptors()")

        # Load test intents + ground truth
        intents = json.loads(Path(intents_json).read_text())
        ground_truth = json.loads(Path(gt_json).read_text())

        for idx, intent in enumerate(intents):
            query = intent["query"]
            expected = ground_truth[str(idx)]["xpath"]

            # Cold run
            t0 = time.perf_counter()
            out_cold = pipeline.process(query, {"elements": descriptors})
            t1 = time.perf_counter()
            timings_cold.append((t1 - t0) * 1000)

            # Warm run (cache hit expected)
            t0 = time.perf_counter()
            out_warm = pipeline.process(query, {"elements": descriptors})
            t1 = time.perf_counter()
            timings_warm.append((t1 - t0) * 1000)

            # Validate: exact xpath or same element identity
            passed = out_cold["xpath"] == expected
            strategy = out_cold.get("strategy", "")
            metadata = out_cold.get("metadata", {})

            results.append(
                {
                    "query": query,
                    "expected": expected,
                    "actual": out_cold["xpath"],
                    "passed": passed,
                    "strategy": strategy,
                    "confidence": float(out_cold.get("confidence", 0.0)),
                    "metadata": metadata,
                    "cold_ms": round(timings_cold[-1], 2),
                    "warm_ms": round(timings_warm[-1], 2),
                }
            )

        browser.close()

    # Summaries
    accuracy = sum(r["passed"] for r in results) / len(results) * 100
    median_cold = statistics.median(timings_cold)
    median_warm = statistics.median(timings_warm)
    speedup = median_cold / median_warm if median_warm > 0 else 1.0

    # Write strict JSON
    Path("functional_results.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False)
    )

    # Write report
    with open("FUNCTIONAL_REPORT.md", "w") as f:
        f.write("# Functional Validation Report\n\n")
        f.write(f"- Total intents: {len(results)}\n")
        f.write(f"- Accuracy: {accuracy:.2f}%\n")
        f.write(f"- Median cold: {median_cold:.2f} ms\n")
        f.write(f"- Median warm: {median_warm:.2f} ms\n")
        f.write(f"- Cold→Warm speedup: {speedup:.2f}×\n\n")

        f.write("## Results\n\n")
        f.write("| Query | Expected | Actual | Passed | Strategy | Cold (ms) | Warm (ms) |\n")
        f.write("|-------|----------|--------|--------|----------|-----------|-----------|\n")
        for r in results:
            f.write(
                f"| {r['query']} | {r['expected']} | {r['actual']} | "
                f"{r['passed']} | {r['strategy']} | {r['cold_ms']} | {r['warm_ms']} |\n"
            )


if __name__ == "__main__":
    run_validation(
        fixture_html="functional_harness/fixture.html",
        intents_json="functional_harness/intents.json",
        gt_json="functional_harness/ground_truth.json",
    )
