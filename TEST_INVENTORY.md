# Test Inventory

## Summary
- **Total Test Files**: 70
- **Categories Covered**: 10/11 (missing i18n)
- **Test Organization**: tests/ directory

## Coverage Matrix

### ✅ Core Flow
- `test_basic.py` - Basic imports and setup
- `test_pipeline_*.py` - Pipeline functionality
- ⚠️ **MISSING**: Dedicated cold start test
- ⚠️ **MISSING**: Dedicated incremental update test

### ✅ Retrieval & Scoring
- `test_nlp_*.py` - NLP scoring tests
- `test_scoring_*.py` - Scoring functionality
- `test_intelligent_matching.py` - Matching logic
- ⚠️ **NEEDS**: Strategy fallback tests

### ✅ DOM Complexity
- `test_dom_uniqueness.py` - DOM uniqueness
- `test_frames_shadow.py` - Frame/shadow DOM handling
- `test_complex_html_xpath.py` - Complex XPath
- ✅ Good coverage

### ⚠️ SPA Navigation
- `test_spa_*.py` - Some SPA tests exist
- ⚠️ **MISSING**: Route listener tests
- ⚠️ **MISSING**: pushState/replaceState handling

### ⚠️ Resilience & Loading
- `test_resilience.py` - Basic resilience
- ⚠️ **MISSING**: Wait and overlay tests
- ⚠️ **MISSING**: Occlusion detection

### ⚠️ Performance
- `test_performance.py` - Basic performance
- ⚠️ **MISSING**: Cache hit latency tests
- ⚠️ **MISSING**: Large DOM stress tests

### ✅ Forms & Inputs
- `test_forms.py` - Form handling
- `test_inputs.py` - Input handling
- ⚠️ **NEEDS**: Widget and datepicker tests

### ⚠️ Auth & Redirects
- Basic auth tests exist
- ⚠️ **MISSING**: MFA flow tests
- ⚠️ **MISSING**: Redirect handling

### ❌ i18n & Accessibility
- **MISSING**: No i18n tests found
- **MISSING**: No RTL tests
- **MISSING**: No ARIA tests

### ✅ CLI & Contract
- `test_cli_api.py` - CLI API tests
- `test_cli_coverage.py` - CLI coverage
- ✅ Good coverage

### ⚠️ Robustness
- Some recovery tests exist
- ⚠️ **MISSING**: CDP disconnect recovery
- ⚠️ **MISSING**: Session resumption

## Required New Test Files

Based on the requirements, we need to create:

1. **tests/core/**
   - `test_cold_start.py` - Empty cache to full pipeline
   - `test_incremental_update.py` - Delta updates only

2. **tests/retrieval/**
   - `test_nlp_scoring.py` - Product disambiguation, verbs
   - `test_strategy_fallbacks.py` - Semantic → CSS → XPath

3. **tests/dom/**
   - `test_frames_shadow.py` - Nested frames + shadow DOM
   - `test_dynamic_churn.py` - Element re-render recovery

4. **tests/spa/**
   - `test_spa_route_listeners.py` - Route change detection

5. **tests/resilience/**
   - `test_waits_overlays.py` - Wait strategies, overlays

6. **tests/perf/**
   - `test_cache_hit_latency.py` - Cold vs warm timing
   - `test_large_dom_stress.py` - 10k+ nodes

7. **tests/forms/**
   - `test_inputs_and_widgets.py` - Complex form widgets

8. **tests/auth/**
   - `test_login_redirect_mfa.py` - Auth flows

9. **tests/a11y/**
   - `test_i18n_roles.py` - i18n and accessibility

10. **tests/cli/**
    - `test_cli_contract.py` - Strict JSON contract

11. **tests/robust/**
    - `test_disconnect_recovery.py` - CDP recovery

## Existing Tests to Keep

Key tests that provide good coverage:
- `test_all_components.py` - Component integration
- `test_complex_scenarios.py` - Complex use cases
- `test_bridge.py` - CDP bridge functionality
- `test_descriptors.py` - Descriptor handling
- `test_embeddings.py` - Embedding functionality

## Next Steps

1. Create missing test directories
2. Implement required test files
3. Generate fixtures for each test category
4. Run full test suite and measure coverage