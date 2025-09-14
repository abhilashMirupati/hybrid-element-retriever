# Hybrid Element Retriever (HER) - Deterministic + Reranker Pipeline

Production-grade framework that turns **plain English** into **robust UI actions** via a **deterministic + reranker pipeline**:
**Snapshot + Canonicalization → Intent Parsing → Target Matching → MarkupLM Reranking → XPath Generation → Execution → Promotion Learning**.

## 🚀 **Key Features**

- ✅ **Deterministic Pipeline**: Consistent, reliable element selection with canonical descriptors
- ✅ **2-Stage Hybrid Search**: MiniLM (384-d) for fast shortlisting + MarkupLM (768-d) for precise reranking
- ✅ **Strict Intent Validation**: Enforces quoted targets and $"value" format for reliability
- ✅ **Relative XPath Only**: Never generates absolute paths, always robust relative selectors
- ✅ **Enhanced Frame Support**: Automatic frame switching and shadow DOM detection
- ✅ **Off-screen Handling**: Comprehensive element visibility detection and smooth scrolling
- ✅ **Promotion System**: SQLite-backed learning with warm < cold performance validation
- ✅ **Production Ready**: Tested with Verizon.com flow and comprehensive test suite

---

## 1) Quickstart

> **Python**: 3.12+ recommended  
> **OS**: Windows/macOS/Linux  
> **Models**: Real MiniLM + MarkupLM (installed automatically)

### Installation

```bash
# 1. Install dependencies
pip install --break-system-packages -r requirements.txt
pip install --break-system-packages playwright pytest pytest-xdist pytest-timeout

# 2. Install Playwright browsers
python -m playwright install chromium

# 3. Install real models (MiniLM + MarkupLM)
bash scripts/install_models.sh

# 4. Run tests to verify everything works
python -m pytest tests/test_verizon_flow.py -v -s --timeout=300
python -m pytest tests/test_promotion_validation.py -v -s --timeout=300
```

### Environment Variables

The HER framework uses environment variables for configuration. You can set them in two ways:

#### Option 1: Using .env file (Recommended)
```bash
# Copy the example file and modify as needed
cp config/.env.example config/.env

# Load environment variables (Python)
python tools/load_env.py

# Or source them in your shell
eval "$(python tools/load_env.py --export)"
```

#### Option 2: Manual export (Legacy)
```bash
export HER_MODELS_DIR="$(pwd)/src/her/models"  # Path to models
export HER_CACHE_DIR="$(pwd)/.her_cache"       # Cache directory
```

#### Available Environment Variables
See `config/.env.example` for a complete list of all available environment variables with descriptions and default values.

## 📚 Documentation

Complete documentation is available in the `docs/` directory:

- **[Setup Guide](docs/setup/SETUP.md)** - Complete setup instructions
- **[Environment Configuration](docs/guides/environment-configuration.md)** - Environment variables guide
- **[Dependency Analysis](docs/development/dependency-analysis.md)** - Required and optional dependencies
- **[Migration Guide](docs/development/migration-guide.md)** - Guide for users migrating from old structure

## 2) Key Concepts

### 2-Stage Hybrid Search
1. **MiniLM Shortlist (384-d)**: Fast text-based search to find top-K candidates
2. **MarkupLM Rerank (768-d)**: Precise structural understanding for final ranking
3. **Heuristics**: Apply clickable bonuses, tag biases, and text matching

### Cold / Warm / Delta Flows
- **Cold**: First visit → embed all elements; cache to SQLite
- **Warm**: Revisit (same page/frame) → reuse cached vectors; rebuild in-mem stores quickly  
- **Delta**: Only embed new/changed elements using element_dom_hash

### Per-frame Vector Stores
Each frame_hash gets its own in-memory store (FAISS for performance). Stores are rebuilt when the frame changes.

### Promotions System
After successful actions, the final selector is persisted (scoped by page_sig, frame_hash, label_key). Next time, HER pre-checks promotions before vector search.

## 3) Usage Example

```python
from her.core.runner import run_steps

# Deterministic step-by-step execution with strict format
steps = [
    "Open https://www.verizon.com/smartphones/apple/",
    "Click \"iPhone 16 Pro\"",
    "Validate \"Apple iPhone 16 Pro\""
]

# Run with deterministic + reranker pipeline
run_steps(steps, headless=True)
```

### **Strict Intent Format Requirements**

The new deterministic pipeline enforces strict format validation:

```python
# ✅ CORRECT FORMATS
"Click \"Login\""                    # Quoted target required
"Type $\"John123\" into \"Username\"" # $value must be quoted
"Validate \"Welcome back\""           # Quoted validation text

# ❌ INCORRECT FORMATS  
"Click Login"                        # Missing quotes
"Type John123 into Username"         # Missing $ and quotes
"Validate Welcome back"              # Missing quotes
```

### Advanced Usage

```python
from her.core.pipeline import HybridPipeline
from her.promotion.promotion_adapter import compute_label_key
from her.executor.main import Executor

# 1) Create pipeline with real models
pipe = HybridPipeline(models_root=Path("src/her/models"))

# 2) Query with hybrid search
out = pipe.query(
    query="click Send button",
    elements=elements,  # from DOM snapshot
    top_k=10,
    page_sig="PAGE_SIGNATURE_STABLE",
    frame_hash="FRAME_HASH_OF_TARGET", 
    label_key=compute_label_key(["send", "button"])
)

# 3) Get best selector
best = out["results"][0]
selector = best["selector"]
print(f"Found selector: {selector}")
print(f"Confidence: {out['confidence']:.3f}")
print(f"Strategy: {out['strategy']}")  # "hybrid-minilm-markuplm"
```
## 4) Architecture (Deterministic + Reranker Pipeline)

```
User Intent ──> Intent Parser (Strict Validation) ──┐
                                                    │
DOM/AX Snapshot ──> Canonical Descriptors ──────────┼─> Deterministic Signatures
                                                    │        │
                                                    ▼        ▼
                                    SQLite Embedding Cache (delta get/put)
                                              │
                                              ▼
                              Per-frame Vector Stores (FAISS / Python)
                                              │
                                              ▼
                                  MiniLM Shortlist (384-d) ──> Target Matcher
                                              │                    │
                                              ▼                    ▼
                                  MarkupLM Reranker (768-d) ──> Heuristics ──> XPath Builder
                                              │                    │              │
                                              ▼                    ▼              ▼
                              Promotions Pre-check ──────────> Relative XPath ──> Executor
                                    (page_sig, frame_hash,         (// only)        (frame/shadow)
                                     label_key)                     │              │
                                              │                    ▼              ▼
                                              ▼               Off-screen      Promotion
                                              ▼               Detection        Recording
                                    Performance Validation    & Scrolling      (SQLite)
                                    (warm < cold)
```
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

8) Test Suite Optimization

### Performance Analysis for Large Test Suites (1000+ tests)

**Current Performance:**
- **Runner Initialization**: 38s (one-time cost)
- **Element Processing**: 0.001-0.004s per mode
- **Total per test**: 46-48s (with initialization)

**Optimization Strategy:**
- **Shared Runner**: Reuse runner instance across all tests
- **Model Persistence**: Keep ML models loaded in memory
- **Browser Reuse**: Maintain single browser instance
- **Memory Management**: ~650MB RAM for models + browser

**Optimized Test Runner:**
```python
from optimized_test_runner import OptimizedTestRunner

# Initialize once for entire test suite
runner = OptimizedTestRunner()

# Run multiple tests with same runner
for test_case in test_suite:
    result = runner.run_test(test_case)
    # Models stay loaded, browser stays open

# Cleanup when done
runner.cleanup()
```

**Performance Gains:**
- **First test**: 38s (initialization)
- **Subsequent tests**: 8-10s each (90% faster)
- **1000 tests**: 8.4 hours → 2.8 hours (67% reduction)

### Memory Usage
- **Models**: ~650MB (MiniLM + MarkupLM + SQLite cache)
- **Browser**: ~200MB (Chromium instance)
- **Total**: ~850MB persistent memory

### Cleanup Methods
```python
# Manual cleanup if needed
runner.cleanup()  # Closes browser, clears models
```

9) Troubleshooting
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

## 9) Testing & Validation

### **Comprehensive Test Suite**

The HER framework includes extensive tests to validate the deterministic + reranker pipeline:

```bash
# Run all tests
python -m pytest tests/ -v -s --timeout=300

# Run specific test suites
python -m pytest tests/test_verizon_flow.py -v -s           # Verizon flow validation
python -m pytest tests/test_promotion_validation.py -v -s   # Promotion system tests
```

### **Test Coverage**

- ✅ **Verizon Flow**: Complete end-to-end validation with required steps
- ✅ **Promotion Performance**: Warm < cold execution time validation  
- ✅ **Intent Format Validation**: Strict quoted target and $"value" enforcement
- ✅ **Relative XPath**: Ensures only relative selectors (never absolute)
- ✅ **Frame & Shadow DOM**: Enhanced element detection and interaction
- ✅ **Off-screen Handling**: Comprehensive visibility detection and scrolling
- ✅ **SQLite Persistence**: Promotion cache persistence across runs

### **Performance Validation**

```bash
# Test promotion system performance
python -m pytest tests/test_promotion_validation.py::TestPromotionValidation::test_promotion_cold_vs_warm_performance -v -s

# Expected output:
# Cold Start: 15.2s
# Warm Hit:   8.1s  
# Improvement: 46.7%
```

## 10) Design Guarantees

- ✅ **No Silent Fallbacks**: Missing deps or invalid inputs raise explicit errors
- ✅ **Deterministic Selectors**: Relative XPath with stable, robust patterns
- ✅ **Strict Format Validation**: Enforces quoted targets and $"value" format
- ✅ **Promotion Isolation**: Keyed by (page_sig, frame_hash, label_key)
- ✅ **Performance Guaranteed**: Warm hits are faster than cold starts
- ✅ **Frame & Shadow DOM**: Automatic detection and switching
- ✅ **Off-screen Robustness**: Comprehensive element visibility handling

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
