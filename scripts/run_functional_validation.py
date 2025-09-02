from __future__ import annotations
from pathlib import Path
import json, time, statistics
from playwright.sync_api import sync_playwright
from her.compat import HERPipeline

def run_validation(fixture_html: str, intents_json: str, gt_json: str) -> None:
    pipeline = HERPipeline()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"file://{fixture_html}")
        js_path = str(Path(__file__).parent / "dom_extractor.js")
        page.add_script_tag(path=js_path)
        descriptors = page.evaluate("extractDescriptors()")
        intents = json.loads(Path(intents_json).read_text())
        gt = json.loads(Path(gt_json).read_text())
        results = []
        cold_times = []; warm_times = []
        for i, intent in enumerate(intents):
            q = intent["query"]; expected = gt[str(i)]["xpath"]
            t0 = time.perf_counter(); out_cold = pipeline.process(q, {"elements": descriptors}); t1 = time.perf_counter()
            t2 = time.perf_counter(); out_warm = pipeline.process(q, {"elements": descriptors}); t3 = time.perf_counter()
            cold_ms = (t1 - t0) * 1000.0; warm_ms = (t3 - t2) * 1000.0
            cold_times.append(cold_ms); warm_times.append(warm_ms)
            results.append({
                "query": q, "expected": expected, "actual": out_cold.get("xpath",""),
                "passed": out_cold.get("xpath","") == expected, "strategy": out_cold.get("strategy",""),
                "confidence": float(out_cold.get("confidence", 0.0)), "metadata": out_cold.get("metadata", {}),
                "cold_ms": round(cold_ms, 2), "warm_ms": round(warm_ms, 2),
            })
        browser.close()
    accuracy = (sum(1 for r in results if r["passed"]) / len(results) * 100.0) if results else 0.0
    med_cold = statistics.median(cold_times) if cold_times else 0.0
    med_warm = statistics.median(warm_times) if warm_times else 0.0
    speed = (med_cold / med_warm) if med_warm > 0 else 1.0
    Path("functional_results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False))
    with open("FUNCTIONAL_REPORT.md", "w") as f:
        f.write("# Functional Validation Report\\n\\n")
        f.write(f"- Total intents: {len(results)}\\n")
        f.write(f"- Accuracy: {accuracy:.2f}%\\n")
        f.write(f"- Median cold: {med_cold:.2f} ms\\n")
        f.write(f"- Median warm: {med_warm:.2f} ms\\n")
        f.write(f"- Cold→Warm speedup: {speed:.2f}×\\n\\n")
        f.write("## Results\\n\\n")
        f.write("| Query | Expected | Actual | Passed | Strategy | Cold (ms) | Warm (ms) |\\n")
        f.write("|---|---|---|---|---|---:|---:|\\n")
        for r in results:
            f.write(f"| {r['query']} | {r['expected']} | {r['actual']} | {r['passed']} | {r['strategy']} | {r['cold_ms']} | {r['warm_ms']} |\\n")

if __name__ == "__main__":
    run_validation(
        fixture_html="functional_harness/fixture.html",
        intents_json="functional_harness/intents.json",
        gt_json="functional_harness/ground_truth.json",
    )
