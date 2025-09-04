### Step-1: Deprecations and Shim

- [x] Renamed 5 legacy files to `*.deprecated`
- [x] Added `src/her/embeddings/minilm_embedder.py` shim
- [x] Grep shows no lingering imports of deprecated modules
- [x] Import smoke test passes
- [x] Reports created: `step1_selfcritique_before.md`, `step1_selfcritique_after.md`, `step1_changes.md`
 
### Step-2: Init scripts and reports

- [x] Added `scripts/init_dbs.ps1` & `scripts/init_dbs.sh`
- [x] Verified cache dir creation and DB touch (Windows + Unix examples documented)
- [x] Created `reports/step2_selfcritique_before.md` & `reports/step2_selfcritique_after.md`
- [x] Logged changes in `reports/step2_changes.md` (or appended to step1 file)