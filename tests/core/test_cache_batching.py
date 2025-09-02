Context

Repo root: /workspace
Python: 3.13
Parallel test runner: pytest-xdist
Targets:
pytest -n auto passes with 0 fails
pytest -n auto --cov=src --cov-config=.coveragerc --cov-report=term-missing --cov-fail-under=80 passes
scripts/profile_runs.py shows warm < cold (functional unchanged)
Existing implementations to assume

Warm-path query+DOM short-circuit is in src/her/compat.py
Batch APIs (get_batch/put_batch) exist in src/her/cache/two_tier.py
Large DOM O(1) text fast-path and delta-embedding are in src/her/compat.py
CLI act path must always return strict JSON (already fixed)
Constraints

No sleeps; use algorithmic work in cold path only
Preserve metadata: used_frame_id, frame_path, in_shadow_dom, strategy
Keep strategy labels intact; deterministic under -n auto
Tasks

Create new tests to cover batching, warm short-circuit, large DOM fast-path, and metadata. Output the following new files with complete content:
tests/core/test_cache_batching.py

Arrange: build TwoTierCache with tmp_path; prepare dict of 50 items; call put_batch; then get_batch on all keys and a mixed subset; assert all values present and memory promotion occurred (len(cache.memory_cache) > 0). Also assert cache.stats() contains mem_items and disk_items.
Exercise a miss->write->hit path: get_batch with misses only, then put_batch same keys, then get_batch again returns all.
tests/core/test_warm_short_circuit.py

Use HERPipeline; run process on a small DOM with query “find element 2”; capture output; run process again with same query and DOM; assert the second call returns immediately with the exact same result (strategy and metadata preserved). Use time.perf_counter to assert ≥3x speedup without sleeps. Also assert the query-level cache key is stored via pipeline.cache.get_raw and contains the full output.
tests/perf/test_large_dom_fastpath_additional.py

Build a DOM with 3000+ elements labeled “Element N”; query “find element 1234”; assert strategy == “text-fast”, xpath is the chosen element’s xpath, and the call finishes under 2s. Ensure in_shadow_dom key exists in metadata (bool). Verify determinism by running it twice and comparing results.
tests/dom/test_metadata_consistency.py

Build a DOM with frames and a shadow element; run HERPipeline; assert out includes used_frame_id, frame_path, metadata['in_shadow_dom'] for the right element; ensure fields are never missing.
Small perf/coverage helper tests to lift branch coverage (keep simple and deterministic):
tests/core/test_delta_embedding_budget.py

Call HERPipeline on a large DOM once; then append one new element; patch pipeline._embed_element to count calls; second call should embed ≤ (1 + 10) elements (allow small overhead). Assert cache_hits increases across runs.
tests/core/test_cli_json_contract_additional.py

Call “python -m her.cli query \"click login\"" and “python -m her.cli act \"click login\"” via subprocess; assert strict JSON shapes; act path returns dict with status/method/confidence even without browsers.
Update (replace contents of) docs:
PERF_REPORT.md: brief section with the post-change cold vs warm timing snippet (median cold/warm and speedup) from a local run; mention large DOM test runtime (<30s).
FUNCTIONAL_REPORT.md: confirm functional 100% unchanged; list any non-functional changes (none).
Acceptance

After adding the above files and updating the two reports, run:
python3 -m pytest -n auto -q
python3 -m pytest -n auto --cov=src --cov-config=.coveragerc --cov-report=term-missing --cov-fail-under=80
python3 scripts/profile_runs.py
All pass, coverage ≥80%, warm < cold, functional unchanged.
Notes for generation

Use only HERPipeline from src/her/compat.py and TwoTierCache from src/her/cache/two_tier.py.

Avoid sleeps; keep tests fast and deterministic for -n auto.

Don’t modify production code; only add tests + docs as listed.

Ensure tests skip external browsers; use pure-Python paths.

Once those files are produced and dropped in, re-run the three commands above. If they’re green, you’re safe to merge.
