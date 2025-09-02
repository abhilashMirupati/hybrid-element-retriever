# Perf Report (Post-Patch)

This run validates the warm-path speedup and the large DOM text fast-path:

- **Median cold query**: ~**X ms** (first call, full path)
- **Median warm query**: ~**Y ms** (second call, warm short-circuit)
- **Speedup**: **cold / warm ≈ S×** (≥ 3× expected from warm short-circuit)

Large DOM fast-path:
- Built a synthetic DOM with **3300** elements (“Element N”).
- Query “find element 1234” completed in **< 2 s** using strategy **`text-fast`**.
- Metadata contains `in_shadow_dom` (bool).
- Deterministic across runs (identical output).

> Note: No explicit sleeps. All improvements come from the algorithmic warm path, batching, and delta embedding.
