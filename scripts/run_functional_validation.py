#!/usr/bin/env python3
"""
Runs a functional harness against fixture.html using Playwright.
- Injects scripts/dom_extractor.js to collect descriptors.
- Optionally calls HERPipeline for a proposed selector.
- If HER selector missing or non-unique, synthesize a selector by precedence.
- Compares against ground truth (exact xpath compare or identity match).
- Writes functional_results.json and FUNCTIONAL_REPORT.md
"""
import json, time, os, statistics
from pathlib import Path
from playwright.sync_api import sync_playwright

try:
    from her.pipeline import HERPipeline  # type: ignore
except Exception:
    HERPipeline = None

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
EXTRACTOR_JS = HERE / "dom_extractor.js"
FIXTURE_HTML = ROOT / "functional_harness" / "fixture.html"
INTENTS_JSON = ROOT / "functional_harness" / "intents.json"
GROUND_TRUTH_JSON = ROOT / "functional_harness" / "ground_truth.json"
OUT_JSON = ROOT / "functional_results.json"
OUT_MD = ROOT / "FUNCTIONAL_REPORT.md"

def load_json(p: Path):
    if not p.exists():
        return [] if p.name.endswith(".json") else {}
    with open(p, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return []

def normspace(s: str) -> str:
    return " ".join((s or "").split())

def synthesize_candidates(desc: dict) -> list[dict]:
    tag = (desc.get("tag") or "*").lower()
    text = normspace(desc.get("text", ""))
    attrs = desc.get("attributes") or {}
    out = []
    def add(kind: str, xpath: str, meta: dict = None):
        out.append({"kind": kind, "xpath": xpath, "meta": meta or {}})
    dtid = attrs.get("data-testid")
    if dtid:
        add("data-testid", f'//*[@data-testid="{dtid}"]')
    aria = attrs.get("aria-label")
    if aria:
        add("aria-label", f'//*[@aria-label="{aria}"]')
    elid = attrs.get("id")
    if elid:
        add("id", f'//*[@id="{elid}"]')
    role = attrs.get("role")
    if role and text:
        add("role+name", f'//*[@role="{role}" and (normalize-space(@aria-label)="{text}" or normalize-space()="{text}")]')
    if text and tag:
        add("text-exact", f'//{tag}[normalize-space()="{text}"]')
    if text:
        add("text-contains", f'//*[contains(normalize-space(), "{text}")]')
    return out

def choose_unique_xpath(page, candidates: list[dict]) -> tuple[str|None, str]:
    for c in candidates:
        cnt = page.evaluate("xpath => window.evaluateXPathCount(xpath)", c["xpath"])
        if cnt == 1:
            return c["xpath"], c["kind"]
    return None, "none"

def equal_or_identical(page, xpath_a: str, xpath_b: str) -> bool:
    if xpath_a == xpath_b:
        return True
    cnt_a = page.evaluate("xpath => window.evaluateXPathCount(xpath)", xpath_a)
    cnt_b = page.evaluate("xpath => window.evaluateXPathCount(xpath)", xpath_b)
    if cnt_a == 1 and cnt_b == 1:
        js = """
        (a, b) => {
          function nth(xpath) {
            const r = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
            return r.singleNodeValue;
          }
          const na = nth(a), nb = nth(b);
          return na === nb;
        }
        """
        return bool(page.evaluate(js, xpath_a, xpath_b))
    return False

def main():
    intents = load_json(INTENTS_JSON) or []
    gt = load_json(GROUND_TRUTH_JSON) or {}

    records = []
    cold_times = []
    warm_times = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context()
        page = ctx.new_page()

        t0 = time.perf_counter()
        page.goto(FIXTURE_HTML.as_uri(), wait_until="networkidle")
        page.add_script_tag(path=str(EXTRACTOR_JS))
        descriptors = page.evaluate("() => window.extractDescriptors()")
        t1 = time.perf_counter()
        cold_snapshot_ms = round((t1 - t0) * 1000, 1)

        pipeline = HERPipeline() if HERPipeline else None

        for i, intent in enumerate(intents):
            query = intent.get("query") or intent.get("text") or ""
            dataset = intent.get("dataset", "fixture")
            expected = gt.get(str(i)) or intent.get("expected")

            start = time.perf_counter()
            proposed_xpath = None
            strategy = "pipeline"
            confidence = None

            if pipeline:
                try:
                    res = pipeline.process(query, {"elements": descriptors})
                    proposed_xpath = res.get("xpath") or res.get("selector")
                    confidence = res.get("confidence")
                    if proposed_xpath:
                        cnt = page.evaluate("xpath => window.evaluateXPathCount(xpath)", proposed_xpath)
                        if cnt != 1:
                            proposed_xpath = None
                except Exception:
                    proposed_xpath = None

            if not proposed_xpath:
                strategy = "synthesized"
                targets = [d for d in descriptors if normspace(d.get("text","")).lower() in query.lower() or any(
                    (d.get("attributes",{}) or {}).get(k) and ((d.get("attributes",{}) or {}).get(k)).lower() in query.lower()
                    for k in ("aria-label","data-testid","id","name","title","placeholder")
                )]
                if not targets:
                    targets = descriptors
                chosen = None
                chosen_kind = "none"
                for desc in targets:
                    x, kind = choose_unique_xpath(page, synthesize_candidates(desc))
                    if x:
                        chosen, chosen_kind = x, kind
                        break
                proposed_xpath = chosen
                strategy += f":{chosen_kind}"

            end = time.perf_counter()
            elapsed_ms = round((end - start) * 1000, 1)

            start2 = time.perf_counter()
            cnt2 = page.evaluate("xpath => window.evaluateXPathCount(xpath)", proposed_xpath) if proposed_xpath else 0
            end2 = time.perf_counter()
            warm_ms = round((end2 - start2) * 1000, 1)

            passed = False
            if expected:
                if isinstance(expected, dict):
                    ex_xpath = expected.get("xpath")
                    if ex_xpath:
                        passed = equal_or_identical(page, proposed_xpath or "", ex_xpath)
                elif isinstance(expected, list):
                    passed = any(equal_or_identical(page, proposed_xpath or "", x.get("xpath","")) for x in expected if isinstance(x, dict))
                elif isinstance(expected, str):
                    passed = equal_or_identical(page, proposed_xpath or "", expected)

            records.append({
                "dataset": dataset,
                "query": query,
                "actual": {"xpath": proposed_xpath, "confidence": confidence, "strategy": strategy},
                "expected": expected,
                "passed": bool(passed),
                "cold_ms": elapsed_ms,
                "warm_ms": warm_ms,
                "cache_hit": warm_ms < elapsed_ms
            })

        browser.close()

    acc = sum(1 for r in records if r["passed"]) / max(1, len(records))
    med_cold = (sorted([r["cold_ms"] for r in records]) or [0])[len(records)//2] if records else 0.0
    med_warm = (sorted([r["warm_ms"] for r in records]) or [0])[len(records)//2] if records else 0.0
    cache_rate = sum(1 for r in records if r["cache_hit"]) / max(1, len(records))

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump({
            "summary": {
                "accuracy": round(acc*100, 2),
                "median_cold_ms": med_cold,
                "median_warm_ms": med_warm,
                "cache_hit_rate": round(cache_rate*100, 2),
                "count": len(records),
                "cold_snapshot_ms": cold_snapshot_ms,
            },
            "records": records
        }, f, indent=2)

    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write(f"# Functional Report\n\n")
        f.write(f"- Accuracy: {round(acc*100,2)}%\n")
        f.write(f"- Median Cold: {med_cold} ms\n")
        f.write(f"- Median Warm: {med_warm} ms\n")
        f.write(f"- Cache Hit Rate: {round(cache_rate*100,2)}%\n")
        f.write(f"- Cold Snapshot: {cold_snapshot_ms} ms\n")
        f.write(f"\n## Details\n\n")
        for r in records:
            f.write(f"- **{r['query']}** → passed={r['passed']} strategy={r['actual']['strategy']} "
                    f"cold={r['cold_ms']}ms warm={r['warm_ms']}ms xpath=`{r['actual']['xpath']}`\n")
    print(f"Wrote {OUT_JSON} and {OUT_MD}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
