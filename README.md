# Hybrid Element Retriever (HER)

Production-grade framework that turns **plain English** into **robust UI actions** via a hybrid pipeline:
**NL intent → DOM/AX snapshot → delta-aware embeddings → per-frame vector search → tie-breaks → XPath → execute → promotions**.

- ✅ **CPU-friendly** (Windows 11 friendly)
- ✅ **Cold / Warm / Delta** flows
- ✅ **SQLite-backed** embedding cache + promotions
- ✅ **Per-frame** vector stores (FAISS if available, pure Python fallback)
- ✅ **Fail-fast** (no silent passes)

---

## 1) Quickstart

> **Python**: 3.12 recommended  
> **OS**: Windows/macOS/Linux  
> **Strict mode**: enabled by default; errors are explicit.

### Windows (PowerShell)
```powershell
# 1. Create venv
py -3.12 -m venv .venv
. .\.venv\Scripts\Activate.ps1
python -m pip install -U pip

# 2. Install deps
pip install -r requirements.txt

# 3. Install Playwright browsers (Chromium)
python -m playwright install chromium

# 4. Download local models (MiniLM ONNX, MarkupLM)
.\scripts\install_models.ps1

# 5. Initialize caches/DB
$env:HER_MODELS_DIR = (Resolve-Path "src/her/models").Path
$env:HER_CACHE_DIR  = (Resolve-Path ".her_cache").Path
.\scripts\init_dbs.ps1
macOS/Linux (bash)
bash
Copy code
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
pip install -r requirements.txt
python -m playwright install chromium
bash scripts/install_models.sh

export HER_MODELS_DIR="$(pwd)/src/her/models"
export HER_CACHE_DIR="$(pwd)/.her_cache"
mkdir -p "$HER_CACHE_DIR"
bash scripts/init_dbs.sh
Environment variables

HER_MODELS_DIR → absolute path to models (e.g., src/her/models)

HER_CACHE_DIR → cache directory (e.g., .her_cache)

2) Key Concepts
Cold / Warm / Delta
Cold: first visit → embed all elements; cache to SQLite.

Warm: revisit (same page/frame) → reuse cached vectors; rebuild in-mem stores quickly.

Delta: only embed new/changed elements using element_dom_hash.

Per-frame Vector Stores
Each frame_hash gets its own in-memory store (FAISS if available). Stores are rebuilt when the frame changes.

Promotions
After successful actions, the final selector is persisted (scoped by page_sig, frame_hash, label_key). Next time, HER pre-checks promotions before vector search.

3) Minimal Usage (Python)
python
Copy code
from her.pipeline import HybridPipeline
from her.promotion_adapter import compute_label_key
from her.executor import Executor

# 1) Snapshot page with your existing browser/snapshot code
#    -> 'elements' is a list of element descriptors, each with meta.frame_hash etc.

pipe = HybridPipeline()
label_key = compute_label_key(["send", "message"])  # from parsed intent

out = pipe.query(
    query="click Send",
    elements=elements,
    top_k=10,
    page_sig="PAGE_SIGNATURE_STABLE",      # required for promotions
    frame_hash="FRAME_HASH_OF_TARGET",     # from element meta
    label_key=label_key,                   # from intent label tokens
)

best = out["results"][0]
selector = best["selector"]

# 2) Execute (Playwright)
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto("https://example.com")
    ex = Executor(page)
    ex.click(
        selector,
        page_sig="PAGE_SIGNATURE_STABLE",
        frame_hash="FRAME_HASH_OF_TARGET",
        label_key=label_key,
    )
    browser.close()
4) Architecture (ASCII)
sql
Copy code
NL Query ──> Intent Parser ──────────┐
                                     │  label_tokens
DOM/AX Snapshot ──> Descriptors ─────┼─> element_dom_hash + frame_hash
                                     │        │
                                     ▼        ▼
               SQLite Embedding Cache (delta get/put)
                         │
                         ▼
        Per-frame Vector Stores (FAISS / Python)
                         │
                         ▼
                 Shortlist + Tie-breaks
                         │
                         ▼
       Promotions Pre-check (page_sig, frame_hash, label_key)
                         │
                         ▼
                  Final XPath Selector
                         │
                         ▼
                Playwright Executor (record success/failure)
5) Files You’ll Touch
Pipeline: src/her/pipeline.py
Cold/Warm/Delta flows; promotions pre-check (optional args).

SQLite Cache: src/her/vectordb/sqlite_cache.py
WAL-mode DB with embeddings, kv, promotions tables.

Promotion Adapter: src/her/promotion_adapter.py
Compute label_key, lookup/record promotions.

Executor: src/her/executor.py
Strict Playwright executor. Records promotion success/failure.

Snapshotter: src/her/browser/snapshot.py
Must include meta.frame_hash and page-level dom_hash.

6) Running Acceptance (static) for Step 3
bash
Copy code
python scripts/step3_acceptance.py
Expected tail output:

makefile
Copy code
STEP3_OK: fields present, frame_hash & dom_hash detected, defaults verified ✅
7) Cleanup Deprecated Files
We keep deprecations until Step 4+ runs clean, then remove them:

bash
Copy code
python scripts/cleanup_deprecated.py --plan
# review plan, then:
python scripts/cleanup_deprecated.py --apply
Targets (typical):

src/her/embeddings/real_embedder.py

src/her/embeddings/minilm_embedder.py

src/her/embeddings/cache.py

src/her/embeddings/enhanced_element_embedder.py

src/her/matching/intelligent_matcher.py

Any *.deprecated renamed in earlier steps

The script fails fast if anything is unexpected.

8) Troubleshooting
Playwright missing
swift
Copy code
RuntimeError: Playwright is required for executor...
Install browsers:

bash
Copy code
python -m playwright install chromium
Models missing
Ensure you ran:

Windows: .\scripts\install_models.ps1

macOS/Linux: bash scripts/install_models.sh

SQLite permission/lock
Use a writable HER_CACHE_DIR. WAL mode is enabled by default.

FAISS wheel unavailable
Vector store will fall back to pure Python search. Nothing to install; performance remains acceptable for small/medium pages.

9) Design Guarantees
No silent fallbacks: missing deps or invalid inputs raise explicit errors.

Deterministic selectors: absolute XPath with stable sibling indices.

Isolation: promotions keyed by (page_sig, frame_hash, label_key).

Compatibility: HybridPipeline public methods preserved.

10) License
MIT (add your license here).

python
Copy code

---

# ✅ Add file — `scripts/cleanup_deprecated.py` (FULL CONTENT)

```python
#!/usr/bin/env python3
"""
Cleanup Deprecated Files (Step 7)

- Prints an exact plan of files to remove (default: PLAN ONLY).
- Requires --apply to actually delete.
- Fails fast if unexpected state is detected.
- No silent passes.

Usage:
  python scripts/cleanup_deprecated.py --plan
  python scripts/cleanup_deprecated.py --apply
"""

from __future__ import annotations
import argparse
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[1]

# Candidate files to delete once Step 4+ are in place
CANDIDATES = [
    "src/her/embeddings/real_embedder.py",
    "src/her/embeddings/minilm_embedder.py",
    "src/her/embeddings/cache.py",
    "src/her/embeddings/enhanced_element_embedder.py",
    "src/her/matching/intelligent_matcher.py",
]

def die(msg: str) -> None:
    print(f"[FAIL] {msg}")
    sys.exit(1)

def ok(msg: str) -> None:
    print(f"[PASS] {msg}")

def note(msg: str) -> None:
    print(f"[INFO] {msg}")

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="actually delete files")
    ap.add_argument("--plan", action="store_true", help="print plan and exit (default)")
    args = ap.parse_args()

    # Default to plan if neither specified
    plan_only = args.plan or not args.apply

    # Validate repo structure
    if not (REPO / "src" / "her").exists():
        die("Not at repo root: expected src/her/ to exist")

    # Build absolute paths
    to_delete = []
    for rel in CANDIDATES:
        p = REPO / rel
        if p.exists():
            to_delete.append(p)

    # Also include any "*.deprecated" files left behind
    for p in (REPO / "src" / "her").rglob("*.deprecated"):
        to_delete.append(p)

    # De-dup and sort
    uniq = sorted(set(to_delete))

    if not uniq:
        ok("No deprecated files found. Nothing to clean.")
        return

    print("Cleanup plan:")
    for p in uniq:
        print(f"  - {p.relative_to(REPO)}")

    if plan_only:
        note("Plan only. Re-run with --apply to delete.")
        return

    # Safety checks before deletion
    # Ensure we've already shipped the new pipeline with delta/promotions
    new_pipeline = REPO / "src" / "her" / "pipeline.py"
    if not new_pipeline.exists():
        die("Missing src/her/pipeline.py — cannot proceed with cleanup.")

    # Ensure sqlite cache exists (indicative of Steps 4–6)
    sqlite_mod = REPO / "src" / "her" / "vectordb" / "sqlite_cache.py"
    if not sqlite_mod.exists():
        die("Missing src/her/vectordb/sqlite_cache.py — cannot proceed with cleanup.")

    # Apply deletion
    deleted = 0
    for p in uniq:
        try:
            p.unlink()
            deleted += 1
        except Exception as e:
            die(f"Failed to delete {p}: {e}")

    ok(f"Deleted {deleted} deprecated file(s).")

if __name__ == "__main__":
    main()
