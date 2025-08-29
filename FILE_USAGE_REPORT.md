# File Usage Report

## Analysis Date: 2024

This report analyzes all files in the repository to determine their usage, references, and proposed actions.

## Summary

- **Total Files Analyzed**: 234
- **Files to Keep**: 182
- **Files to Move**: 27
- **Files to Archive**: 18
- **Files to Evaluate**: 7

## Methodology
- **Usage Check**: `git grep -n` and AST import scanning
- **Role Check**: Against allowlist and functional requirements
- **Duplication Check**: Content analysis for redundancy
- **CI Proof**: Test impact analysis

## Files to Move (Misplaced)

| Path | Category | Referenced By | Reason | New Location |
|------|----------|---------------|--------|--------------|
| test_all_components.py | misplaced_test | test_final_verification.py, FINAL_COMPONENT_STATUS.md | Test file in root - should be in tests/ | tests/test_all_components.py |
| test_all_fixes.py | misplaced_test | FINAL_FIXES_SUMMARY.md | Test file in root - should be in tests/ | tests/test_all_fixes.py |
| test_complex_features.py | misplaced_test | FINAL_FIXES_SUMMARY.md | Test file in root - should be in tests/ | tests/test_complex_features.py |
| test_complex_html_xpath.py | misplaced_test | FINAL_SELF_CRITIQUE.md, FINAL_NLP_FIX_VERIFICATION.md | Test file in root - should be in tests/ | tests/test_complex_html_xpath.py |
| test_debug_flow.py | misplaced_test | None | Test file in root - should be in tests/ | tests/test_debug_flow.py |
| test_debug_phone.py | misplaced_test | None | Test file in root - should be in tests/ | tests/test_debug_phone.py |
| test_debug_phone2.py | misplaced_test | None | Test file in root - should be in tests/ | tests/test_debug_phone2.py |
| test_direct_score.py | misplaced_test | None | Test file in root - should be in tests/ | tests/test_direct_score.py |
| test_edge_cases_real.py | misplaced_test | FINAL_SELF_CRITIQUE.md | Test file in root - should be in tests/ | tests/test_edge_cases_real.py |
| test_final_component_analysis.py | misplaced_test | FINAL_COMPONENT_STATUS.md | Test file in root - should be in tests/ | tests/test_final_component_analysis.py |
| test_final_fix.py | misplaced_test | None | Test file in root - should be in tests/ | tests/test_final_fix.py |
| test_final_nlp_verification.py | misplaced_test | FINAL_NLP_FIX_VERIFICATION.md | Test file in root - should be in tests/ | tests/test_final_nlp_verification.py |
| test_final_verification.py | misplaced_test | None | Test file in root - should be in tests/ | tests/test_final_verification.py |
| test_fixes_work.py | misplaced_test | FINAL_REAL_ANALYSIS.md | Test file in root - should be in tests/ | tests/test_fixes_work.py |
| test_her_comprehensive.py | misplaced_test | None | Test file in root - should be in tests/ | tests/test_her_comprehensive.py |
| test_intelligent_matching.py | misplaced_test | FINAL_COMPONENT_STATUS.md | Test file in root - should be in tests/ | tests/test_intelligent_matching.py |
| test_mock_scenarios.py | misplaced_test | None | Test file in root - should be in tests/ | tests/test_mock_scenarios.py |
| test_nlp_improvements.py | misplaced_test | FINAL_NLP_FIX_VERIFICATION.md | Test file in root - should be in tests/ | tests/test_nlp_improvements.py |
| test_phone_fresh.py | misplaced_test | None | Test file in root - should be in tests/ | tests/test_phone_fresh.py |
| test_pipeline_debug.py | misplaced_test | None | Test file in root - should be in tests/ | tests/test_pipeline_debug.py |
| test_pipeline_direct.py | misplaced_test | None | Test file in root - should be in tests/ | tests/test_pipeline_direct.py |
| test_real_integration.py | misplaced_test | FINAL_SELF_CRITIQUE.md | Test file in root - should be in tests/ | tests/test_real_integration.py |
| test_reality_check.py | misplaced_test | None | Test file in root - should be in tests/ | tests/test_reality_check.py |
| test_scoring_detail.py | misplaced_test | None | Test file in root - should be in tests/ | tests/test_scoring_detail.py |
| test_trace_phone.py | misplaced_test | None | Test file in root - should be in tests/ | tests/test_trace_phone.py |
| test_trace_score.py | misplaced_test | None | Test file in root - should be in tests/ | tests/test_trace_score.py |
| test_uncached.py | misplaced_test | None | Test file in root - should be in tests/ | tests/test_uncached.py |

## Files to Archive (Suspected Redundant)

| Path | Category | Referenced By | Reason |
|------|----------|---------------|--------|
| FINAL_AUDIT_REPORT.md | root_documentation | None | Generated report/critique - can be regenerated |
| FINAL_CHECKLIST.md | root_documentation | None | Generated report/critique - can be regenerated |
| FINAL_COMPONENT_STATUS.md | root_documentation | None | Generated report/critique - can be regenerated |
| FINAL_FIXES_SUMMARY.md | root_documentation | None | Generated report/critique - can be regenerated |
| FINAL_NLP_FIX_VERIFICATION.md | root_documentation | None | Generated report/critique - can be regenerated |
| FINAL_REAL_ANALYSIS.md | root_documentation | None | Generated report/critique - can be regenerated |
| FINAL_SELF_CRITIQUE.md | root_documentation | None | Generated report/critique - can be regenerated |
| FINAL_SELF_CRITIQUE_REPORT.md | root_documentation | None | Generated report/critique - can be regenerated |
| SELFCRITIQUE_AFTER.md | root_documentation | TODO_LIST.md, PRODUCTION_READINESS_REVIEW.md, SENIOR_ARCHITECT_REVIEW.md | Generated report/critique - can be regenerated |
| SELFCRITIQUE_BEFORE.md | root_documentation | TODO_LIST.md, PRODUCTION_READINESS_REVIEW.md, SENIOR_ARCHITECT_REVIEW.md | Generated report/critique - can be regenerated |
| SELF_CRITIQUE_FINAL.md | root_documentation | None | Generated report/critique - can be regenerated |
| analyze_files.py | other | None | No references found |
| critical_fixes.patch | validation_script | None | Validation/debug script with no references |
| example_usage.py | other | None | No references found |
| fix_all_issues.py | validation_script | None | Validation/debug script with no references |
| fix_failures.py | validation_script | None | Validation/debug script with no references |
| issues_to_fix.md | validation_script | None | Validation/debug script with no references |
| run_final_validation.py | versioned_file | FINAL_CHECKLIST.md | Versioned/backup file - likely redundant |

## Files to Evaluate Further

| Path | Category | Referenced By | Reason |
|------|----------|---------------|--------|
| brutal_self_critique.py | validation_script | FINAL_SELF_CRITIQUE_REPORT.md | Validation script - check if still needed |
| brutal_self_critique_fixed.py | validation_script | FINAL_SELF_CRITIQUE_REPORT.md | Validation script - check if still needed |
| final_brutal_critique.py | validation_script | FINAL_REAL_ANALYSIS.md | Validation script - check if still needed |
| final_brutal_test.py | validation_script | FINAL_SELF_CRITIQUE_REPORT.md | Validation script - check if still needed |
| validate_integration.py | validation_script | PRODUCTION_READINESS_REVIEW.md, validate_integration.py | Validation script - check if still needed |
| validate_production.py | validation_script | FINAL_CHECKLIST.md, PRODUCTION_SUMMARY.md | Validation script - check if still needed |
| verify_fixes.py | validation_script | FINAL_SELF_CRITIQUE_REPORT.md | Validation script - check if still needed |

## Critical Files (Always Keep)

| Path | Category | Reason |
|------|----------|--------|
| .github/workflows/ci.yml | allowlist | In allowlist - critical file |
| CHANGELOG.md | allowlist | In allowlist - critical file |
| LICENSE | allowlist | In allowlist - critical file |
| README.md | allowlist | In allowlist - critical file |
| pyproject.toml | allowlist | In allowlist - critical file |
| requirements-dev.txt | allowlist | In allowlist - critical file |
| requirements.txt | allowlist | In allowlist - critical file |
| setup.py | other |  |
| src/her/__init__.py | allowlist | In allowlist - critical file |

## Next Steps

1. Review files marked for archival
2. Move misplaced test files to tests/ directory
3. Update all import statements and references
4. Run full test suite to verify no breakage
5. Create SELFCRITIQUE_BEFORE.md before any deletions
