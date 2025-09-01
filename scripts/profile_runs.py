#!/usr/bin/env python3
import json, time
from pathlib import Path
from playwright.sync_api import sync_playwright

def main():
    out = {"runs": []}
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True)
        ctx = b.new_context()
        page = ctx.new_page()
        t0 = time.perf_counter()
        page.goto("https://example.com", wait_until="networkidle")
        t1 = time.perf_counter()
        cold_ms = round((t1 - t0) * 1000, 1)
        t2 = time.perf_counter()
        page.reload(wait_until="networkidle")
        t3 = time.perf_counter()
        warm_ms = round((t3 - t2) * 1000, 1)
        out["runs"].append({"cold_ms": cold_ms, "warm_ms": warm_ms})
        b.close()
    Path("PERF_REPORT.md").write_text(f"# Perf Report\n\n- Cold: {cold_ms} ms\n- Warm: {warm_ms} ms\n", encoding="utf-8")
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
