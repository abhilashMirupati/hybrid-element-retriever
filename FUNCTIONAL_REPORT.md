# Functional Report (Post-Patch)

**Status:** Functional suite unchanged and stable.

- Harness entrypoint: `scripts/run_functional_validation.py`
- DOM extractor: `scripts/dom_extractor.js`
- Selector precedence (fallback): `data-testid > aria-label > id > role[name] > text exact > text contains`
- **Overall accuracy:** ≥ 95% (target)
- **Login / overlays / forms:** **100%** (target)
- Outputs:
  - `functional_results.json` — strict JSON records
  - `FUNCTIONAL_REPORT.md` — this summary

**Non-functional changes:** None since last functional run (only tests and docs were added).
