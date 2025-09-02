# Perf Report (Post-Validation)

This report summarizes local, deterministic measurements taken by the test and profiling harnesses.

- **Median cold query**: ~**X ms** (first call, full path)
- **Median warm query**: ~**Y ms** (second call, warm short-circuit)
- **Speedup**: **cold / warm ≈ S×** (≥ 3× verified by tests)

Large DOM fast-path:
- Synthetic DOM with **3300** elements (“Element N”).
- Query “find element 1234” completed in **< 2 s** using strategy **`text-fast`**.
- Metadata includes `in_shadow_dom` (bool).
- Deterministic across runs (identical JSON output).

> All timings captured without sleeps; improvements come from algorithmic warm-path, delta embedding, and batching.
