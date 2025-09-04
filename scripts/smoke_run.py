#!/usr/bin/env python3
"""
HER Smoke Run (real Playwright + NL → XPath → action)

This does a full end-to-end test with Chromium:
  - Launch Chromium
  - Create a tiny test page (set_content)
  - Snapshot → pipeline.query("close popup") → get XPath
  - Execute click → verify popup removed
  - Hard-fail on any missing dependency or unexpected result

Exit:
  0 = success
  1 = failure with clear reason
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import List, Dict, Any

from her.strict import (
    require_playwright, require_path_exists, require_sqlite_open
)
from her.pipeline import HybridPipeline
from her.executor import Executor
from her.promotion_adapter import compute_label_key
from her.browser.snapshot import Snapshotter


TEST_HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>HER Smoke Test</title>
  <style>
    #overlay {
      position: fixed; inset: 0; background: rgba(0,0,0,0.4);
      display: flex; align-items: center; justify-content: center;
    }
    #popup {
      background: white; padding: 20px; border-radius: 8px;
    }
    #search { margin-top: 40px; }
  </style>
</head>
<body>
  <div id="overlay">
    <div id="popup">
      <p>Welcome!</p>
      <button id="closeBtn" aria-label="Close popup">Close</button>
    </div>
  </div>

  <main>
    <input id="search" type="text" placeholder="Search items"/>
    <button id="sendBtn" role="button">Send</button>
  </main>
</body>
</html>
""".strip()


def _env_checks() -> None:
    # Require Playwright + Chromium
    require_playwright(True)

    # Basic DB presence
    cache_dir = os.getenv("HER_CACHE_DIR", "").strip()
    if not cache_dir:
        raise SystemExit("HER_CACHE_DIR not set. Run scripts/init_dbs.* and set env.")
    require_path_exists(cache_dir, kind="cache dir")
    db_path = str(Path(cache_dir) / "embeddings.db")
    require_sqlite_open(db_path)

    # Models present (we enforce for smoke)
    models_dir = os.getenv("HER_MODELS_DIR", "").strip()
    if not models_dir:
        raise SystemExit("HER_MODELS_DIR not set. Run scripts/install_models.* and set env.")
    require_path_exists(models_dir, kind="models dir")


def _snapshot_descriptors(page) -> Dict[str, Any]:
    # Use the real snapshotter (Step 3)
    snap = Snapshotter(include_iframes=True, include_shadow_dom=True)
    result = snap.snapshot(page)  # expected: dict { "frames": [...], "dom_hash": "..." }
    if not isinstance(result, dict) or "frames" not in result:
        raise RuntimeError("Snapshotter did not return expected dict with 'frames'")
    # Flatten element descriptors across frames
    elements: List[Dict[str, Any]] = []
    frames = result.get("frames", [])
    for fr in frames:
        items = fr.get("elements", [])
        for el in items:
            elements.append(el)
    return {"elements": elements, "dom_hash": result.get("dom_hash", "")}


def main() -> None:
    from playwright.sync_api import sync_playwright

    _env_checks()

    pipe = HybridPipeline()
    label_key = compute_label_key(["close", "popup"])

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_content(TEST_HTML)

        # Snapshot → descriptors
        snap = _snapshot_descriptors(page)
        elements = snap["elements"]
        if not elements:
            raise SystemExit("No elements captured by snapshotter.")

        # Query: plain English → XPath
        out = pipe.query(
            query="close popup",
            elements=elements,
            top_k=5,
            page_sig="SMOKE_PAGE",
            frame_hash=elements[0].get("meta", {}).get("frame_hash", ""),
            label_key=label_key,
        )
        if not out["results"]:
            raise SystemExit("Pipeline returned no candidates for 'close popup'.")

        selector = out["results"][0]["selector"]
        if not isinstance(selector, str) or not selector.startswith("/"):
            raise SystemExit(f"Invalid XPath selector returned: {selector!r}")

        # Execute action
        ex = Executor(page)
        ex.click(selector, page_sig="SMOKE_PAGE",
                           frame_hash=elements[0].get("meta", {}).get("frame_hash", ""),
                           label_key=label_key)

        # Validate: overlay removed
        overlay_present = page.locator("#overlay").count()
        if overlay_present != 0:
            raise SystemExit("Popup overlay still present after click.")

        # Second step: type into search (warm path)
        # Re-snapshot after DOM changed
        snap2 = _snapshot_descriptors(page)
        elements2 = snap2["elements"]

        out2 = pipe.query(
            query="type hello into search",
            elements=elements2,
            top_k=5,
            page_sig="SMOKE_PAGE",
            frame_hash=elements2[0].get("meta", {}).get("frame_hash", ""),
            label_key=compute_label_key(["type", "search"]),
        )
        if not out2["results"]:
            raise SystemExit("Pipeline returned no candidates for 'type hello into search'.")

        sel2 = out2["results"][0]["selector"]
        ex.type(sel2, "hello", page_sig="SMOKE_PAGE",
                          frame_hash=elements2[0].get("meta", {}).get("frame_hash", ""),
                          label_key=compute_label_key(["type", "search"]))

        # Validate input value
        value = page.locator("#search").input_value()
        if value != "hello":
            raise SystemExit(f"Typing failed; expected 'hello', got {value!r}")

        browser.close()

    print("SMOKE_OK: NL → XPath → Action succeeded (close + type) ✅")


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        msg = str(e) or "Smoke failed."
        if msg:
            print(msg)
        sys.exit(1)
    except Exception as e:
        print(f"Smoke error: {e}")
        sys.exit(1)
