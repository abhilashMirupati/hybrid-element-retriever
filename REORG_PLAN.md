# Repository Reorganization Plan

## Overview
This document outlines the non-destructive reorganization of the repository to achieve a production-ready layout.

## Principles
1. **No Destructive Deletes**: Files are archived, not deleted
2. **Maintain Git History**: Use git mv where possible
3. **Update All References**: Fix imports and paths
4. **Verify Each Step**: Run tests after each change

## Phase 1: Move Misplaced Test Files

### Test Files in Root → tests/
The following test files will be moved from root to the tests/ directory:

| Current Location | New Location | References to Update |
|-----------------|--------------|---------------------|
| `/workspace/test_all_components.py` | `/workspace/tests/test_all_components.py` | FINAL_COMPONENT_STATUS.md, test_final_verification.py |
| `/workspace/test_all_fixes.py` | `/workspace/tests/test_all_fixes.py` | FINAL_FIXES_SUMMARY.md |
| `/workspace/test_complex_features.py` | `/workspace/tests/test_complex_features.py` | FINAL_FIXES_SUMMARY.md |
| `/workspace/test_complex_html_xpath.py` | `/workspace/tests/test_complex_html_xpath.py` | FINAL_NLP_FIX_VERIFICATION.md, FINAL_SELF_CRITIQUE.md |
| `/workspace/test_debug_flow.py` | `/workspace/tests/test_debug_flow.py` | None |
| `/workspace/test_debug_phone.py` | `/workspace/tests/test_debug_phone.py` | None |
| `/workspace/test_debug_phone2.py` | `/workspace/tests/test_debug_phone2.py` | None |
| `/workspace/test_direct_score.py` | `/workspace/tests/test_direct_score.py` | None |
| `/workspace/test_edge_cases_real.py` | `/workspace/tests/test_edge_cases_real.py` | FINAL_SELF_CRITIQUE.md |
| `/workspace/test_final_component_analysis.py` | `/workspace/tests/test_final_component_analysis.py` | FINAL_COMPONENT_STATUS.md |
| `/workspace/test_final_fix.py` | `/workspace/tests/test_final_fix.py` | None |
| `/workspace/test_final_nlp_verification.py` | `/workspace/tests/test_final_nlp_verification.py` | FINAL_NLP_FIX_VERIFICATION.md |
| `/workspace/test_final_verification.py` | `/workspace/tests/test_final_verification.py` | None |
| `/workspace/test_fixes_work.py` | `/workspace/tests/test_fixes_work.py` | FINAL_REAL_ANALYSIS.md |
| `/workspace/test_her_comprehensive.py` | `/workspace/tests/test_her_comprehensive.py` | None |
| `/workspace/test_intelligent_matching.py` | `/workspace/tests/test_intelligent_matching.py` | FINAL_COMPONENT_STATUS.md |
| `/workspace/test_mock_scenarios.py` | `/workspace/tests/test_mock_scenarios.py` | None |
| `/workspace/test_nlp_improvements.py` | `/workspace/tests/test_nlp_improvements.py` | FINAL_NLP_FIX_VERIFICATION.md |
| `/workspace/test_phone_fresh.py` | `/workspace/tests/test_phone_fresh.py` | None |
| `/workspace/test_pipeline_debug.py` | `/workspace/tests/test_pipeline_debug.py` | None |
| `/workspace/test_pipeline_direct.py` | `/workspace/tests/test_pipeline_direct.py` | None |
| `/workspace/test_real_integration.py` | `/workspace/tests/test_real_integration.py` | FINAL_SELF_CRITIQUE.md |
| `/workspace/test_reality_check.py` | `/workspace/tests/test_reality_check.py` | None |
| `/workspace/test_scoring_detail.py` | `/workspace/tests/test_scoring_detail.py` | None |
| `/workspace/test_trace_phone.py` | `/workspace/tests/test_trace_phone.py` | None |
| `/workspace/test_trace_score.py` | `/workspace/tests/test_trace_score.py` | None |
| `/workspace/test_uncached.py` | `/workspace/tests/test_uncached.py` | None |

## Phase 2: Archive Redundant Files

### Versioned/Backup Files → ARCHIVE/
Files that appear to be old versions or backups:

| File | Reason | Archive Location |
|------|--------|-----------------|
| `/workspace/src/her/cli_api_backup.py` | Backup file (cli_api.py exists) | `/workspace/ARCHIVE/src/cli_api_backup.py` |
| `/workspace/src/her/cli_api_fixed.py` | Fixed version (cli_api.py exists) | `/workspace/ARCHIVE/src/cli_api_fixed.py` |
| `/workspace/src/her/pipeline_final.py` | Version file (pipeline.py exists) | `/workspace/ARCHIVE/src/pipeline_final.py` |
| `/workspace/src/her/pipeline_production.py` | Version file (pipeline.py exists) | `/workspace/ARCHIVE/src/pipeline_production.py` |
| `/workspace/src/her/pipeline_v2.py` | Version file (pipeline.py exists) | `/workspace/ARCHIVE/src/pipeline_v2.py` |
| `/workspace/src/her/scoring/fusion_scorer_v2.py` | Version file | `/workspace/ARCHIVE/src/fusion_scorer_v2.py` |
| `/workspace/src/her/vectordb/sqlite_cache_old.py` | Old version | `/workspace/ARCHIVE/src/sqlite_cache_old.py` |

### Debug/Validation Scripts → ARCHIVE/
One-off validation and debug scripts:

| File | Reason | Archive Location |
|------|--------|-----------------|
| `/workspace/brutal_self_critique.py` | Debug/validation script | `/workspace/ARCHIVE/brutal_self_critique.py` |
| `/workspace/brutal_self_critique_fixed.py` | Debug/validation script | `/workspace/ARCHIVE/brutal_self_critique_fixed.py` |
| `/workspace/final_brutal_critique.py` | Debug/validation script | `/workspace/ARCHIVE/final_brutal_critique.py` |
| `/workspace/final_brutal_test.py` | Debug/validation script | `/workspace/ARCHIVE/final_brutal_test.py` |
| `/workspace/fix_all_issues.py` | One-off fix script | `/workspace/ARCHIVE/fix_all_issues.py` |
| `/workspace/fix_failures.py` | One-off fix script | `/workspace/ARCHIVE/fix_failures.py` |
| `/workspace/validate_integration.py` | Validation script | `/workspace/ARCHIVE/validate_integration.py` |
| `/workspace/validate_production.py` | Validation script | `/workspace/ARCHIVE/validate_production.py` |
| `/workspace/verify_fixes.py` | Validation script | `/workspace/ARCHIVE/verify_fixes.py` |
| `/workspace/run_final_validation.py` | Validation script | `/workspace/ARCHIVE/run_final_validation.py` |

### Generated Reports → ARCHIVE/
Reports that can be regenerated:

| File | Reason | Archive Location |
|------|--------|-----------------|
| `/workspace/FINAL_AUDIT_REPORT.md` | Generated report | `/workspace/ARCHIVE/FINAL_AUDIT_REPORT.md` |
| `/workspace/FINAL_CHECKLIST.md` | Generated report | `/workspace/ARCHIVE/FINAL_CHECKLIST.md` |
| `/workspace/FINAL_COMPONENT_STATUS.md` | Generated report | `/workspace/ARCHIVE/FINAL_COMPONENT_STATUS.md` |
| `/workspace/FINAL_FIXES_SUMMARY.md` | Generated report | `/workspace/ARCHIVE/FINAL_FIXES_SUMMARY.md` |
| `/workspace/FINAL_NLP_FIX_VERIFICATION.md` | Generated report | `/workspace/ARCHIVE/FINAL_NLP_FIX_VERIFICATION.md` |
| `/workspace/FINAL_REAL_ANALYSIS.md` | Generated report | `/workspace/ARCHIVE/FINAL_REAL_ANALYSIS.md` |
| `/workspace/FINAL_SELF_CRITIQUE.md` | Generated report | `/workspace/ARCHIVE/FINAL_SELF_CRITIQUE.md` |
| `/workspace/FINAL_SELF_CRITIQUE_REPORT.md` | Generated report | `/workspace/ARCHIVE/FINAL_SELF_CRITIQUE_REPORT.md` |
| `/workspace/SELFCRITIQUE_AFTER.md` | Generated report | `/workspace/ARCHIVE/SELFCRITIQUE_AFTER.md` |
| `/workspace/SELFCRITIQUE_BEFORE.md` | Generated report | `/workspace/ARCHIVE/SELFCRITIQUE_BEFORE.md` |
| `/workspace/SELF_CRITIQUE_FINAL.md` | Generated report | `/workspace/ARCHIVE/SELF_CRITIQUE_FINAL.md` |

## Phase 3: Clean Up Documentation

### Consolidate Documentation
- Keep primary docs: README.md, CHANGELOG.md, CONTRIBUTING.md, LICENSE, RISKS.md
- Archive redundant analysis docs
- Ensure docs/ folder has organized documentation

## Phase 4: Verification Steps

After each phase:
1. Run `pytest` to ensure tests pass
2. Run `black --check .` for formatting
3. Run `flake8` for linting
4. Run `mypy src` for type checking
5. Test packaging: `python3 -m build`
6. Test installation: `pip install dist/*.whl`

## Phase 5: Final Validation

1. Create SELFCRITIQUE_BEFORE.md with current state
2. Execute all moves and archives
3. Run complete test suite
4. Create SELFCRITIQUE_AFTER.md with validation results
5. Update README.md with clear instructions

## Rollback Plan

If any issues arise:
1. All files are in ARCHIVE/, not deleted
2. Can restore with: `cp -r ARCHIVE/* /workspace/`
3. Git history preserved for all moves
4. No destructive operations performed

## Execution Timeline

1. **Hour 1**: Move test files, update imports
2. **Hour 2**: Archive redundant files
3. **Hour 3**: Run full validation suite
4. **Hour 4**: Generate final reports

## Success Criteria

✅ All tests pass after reorganization
✅ No import errors
✅ Package builds successfully
✅ CI/CD pipeline green
✅ No placeholder or stub code remains
✅ Documentation is clear and complete