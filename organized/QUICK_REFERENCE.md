# HER Framework - Quick Reference Guide

## 🚀 Quick Start

### Run Essential Tests
```bash
# Run main essential validation (recommended)
python organized/tests/test_essential_validation.py

# Run comprehensive validation with subprocess isolation
python organized/tests/test_final_comprehensive_validation.py

# Run all project tests
python run_all_tests.py
```

### Run Individual CDP Modes
```bash
# Test all 3 modes individually
python organized/tests/test_cdp_modes_individual.py

# Test specific mode
python organized/tests/test_all_modes_comprehensive.py
```

### Run Regression Tests
```bash
# Verizon regression test
python organized/tests/test_verizon_regression_comprehensive.py

# Google regression test  
python organized/tests/test_google_regression_comprehensive.py
```

## 🔧 Debug Commands

### Debug Issues
```bash
# Run comprehensive debug test (main debug script)
python organized/debug/debug_comprehensive_testing.py
```

### Debug Performance
```bash
# Run comprehensive debug test (includes performance analysis)
python organized/debug/debug_comprehensive_testing.py
```

## 📊 Test Categories

### 1. Essential Tests
- `test_essential_validation.py` - **MAIN TEST** - Essential functionality validation
- `test_final_comprehensive_validation.py` - Comprehensive validation with subprocess isolation
- `test_all_modes_comprehensive.py` - All 3 CDP modes
- `test_cdp_modes_individual.py` - Individual mode testing

### 2. Regression Tests
- `test_verizon_regression_comprehensive.py` - Verizon.com testing
- `test_google_regression_comprehensive.py` - Google.com testing
- `test_verizon_regression_individual.py` - Verizon individual tests

### 3. Performance Tests
- `test_runner_optimization.py` - Runner optimization
- `test_model_loading_performance.py` - Model loading performance
- `test_production_ready_comprehensive.py` - Production readiness

### 4. Validation Tests
- `test_validation_comprehensive.py` - Comprehensive validation
- `test_validation_accessibility_only.py` - Accessibility validation
- `test_validation_simple_flow.py` - Simple flow validation

## 🎯 Expected Results

### Successful Test Output
```
🚀 FINAL COMPREHENSIVE VALIDATION TEST
======================================================================

🔍 Running DOM_ONLY Mode (DOM_ONLY)...
   ✅ PASSED (45.23s)

🔍 Running ACCESSIBILITY_ONLY Mode (ACCESSIBILITY_ONLY)...
   ✅ PASSED (46.12s)

🔍 Running BOTH Mode (BOTH)...
   ✅ PASSED (48.67s)

🧠 Testing Model Caching...
   ✅ PASSED (0.01s)

📈 COMPREHENSIVE TEST RESULTS
==================================================
DOM_ONLY             | ✅ PASS | 2532 elements | 45.230s | Binding: 99.7%
ACCESSIBILITY_ONLY   | ✅ PASS |  931 elements | 46.120s | Binding: 99.8%
BOTH                 | ✅ PASS | 3457 elements | 48.670s | Binding: 99.6%
MODEL_CACHING        | ✅ PASS | First: 38.45s | Second: 0.01s

🎯 FINAL RESULT: ✅ ALL TESTS PASSED

🎉 PRODUCTION READY!
✅ All 3 CDP modes working correctly
✅ Model caching optimization working
✅ Element extraction working
✅ Node binding working
✅ No import/compile/runtime issues
✅ Framework is production-ready
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Import Errors
```bash
# Check Python path
export PYTHONPATH="/workspace/src:$PYTHONPATH"

# Check dependencies
pip install -r requirements.txt
```

#### 2. Runtime Errors
```bash
# Check environment variables
export HER_CANONICAL_MODE="DOM_ONLY"

# Check Playwright installation
python -m playwright install chromium
```

#### 3. Performance Issues
```bash
# Check model loading
python organized/debug/debug_performance_timing_analysis.py

# Check memory usage
python organized/tests/test_model_loading_performance.py
```

### Debug Steps
1. **Run main test**: `python organized/tests/test_final_comprehensive_validation.py`
2. **Check specific mode**: Run individual mode tests
3. **Debug issues**: Use debug scripts in `organized/debug/`
4. **Check logs**: Review error messages and stack traces
5. **Fix and retry**: Address issues and re-run tests

## 📁 File Organization

```
/workspace/
├── run_all_tests.py                    # Main test runner
├── organized/
│   ├── tests/                          # All test scripts
│   │   ├── test_final_comprehensive_validation.py  # MAIN TEST
│   │   ├── test_all_modes_comprehensive.py
│   │   └── ...
│   ├── debug/                          # Debug utilities
│   │   ├── debug_accessibility_tree_structure.py
│   │   ├── debug_cdp_integration_test.py
│   │   └── ...
│   ├── reports/                        # Analysis reports
│   │   ├── report_performance_analysis_2025-09-09.md
│   │   └── ...
│   └── scripts/                        # Utility scripts
│       └── test_suite_optimization_analysis.py
└── src/her/                           # Framework source code
```

## 🎯 Success Criteria

- ✅ All 3 CDP modes working (DOM_ONLY, ACCESSIBILITY_ONLY, BOTH)
- ✅ Model caching optimization working
- ✅ Element extraction working correctly
- ✅ Node binding working (99%+ backendNodeId coverage)
- ✅ No import/compile/runtime errors
- ✅ Performance within acceptable limits
- ✅ All regression tests passing

## 📞 Support

If you encounter issues:
1. Check this quick reference guide
2. Review the organized test output
3. Use debug scripts to identify problems
4. Check the main README.md for detailed documentation
5. Review the PROJECT_ORGANIZATION.md for file structure