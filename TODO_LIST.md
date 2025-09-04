### Step-1: Deprecations and Shim

- [x] Renamed 5 legacy files to `*.deprecated`
- [x] Added `src/her/embeddings/minilm_embedder.py` shim
- [x] Grep shows no lingering imports of deprecated modules
- [x] Import smoke test passes
- [x] Reports created: `step1_selfcritique_before.md`, `step1_selfcritique_after.md`, `step1_changes.md`