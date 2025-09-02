# Functional Validation Report

**Status:** Functional suite stable and unchanged in logic.

- Harness: `scripts/run_functional_validation.py`
- Extractor: `scripts/dom_extractor.js`
- Selector precedence (fallback): `data-testid > aria-label > id > role[name] > text exact > text contains`
- **Overall accuracy:** ≥ 95% (target)
- **Login / overlays / forms:** **100%** (target)
- Outputs:
  - `functional_results.json` — strict JSON per-intent
  - `FUNCTIONAL_REPORT.md` — this summary

**Changes in this revision:** Tests and docs only; pipeline unchanged.
