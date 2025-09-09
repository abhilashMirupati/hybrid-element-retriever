# HER Framework - Project Organization

## 📁 Directory Structure

```
/workspace/
├── src/her/                    # Main framework source code
├── tests/                      # Official test suite
├── scripts/                    # Installation and utility scripts
├── organized/                  # Organized development files
│   ├── debug/                  # Debug scripts and utilities
│   ├── reports/                # Analysis reports and logs
│   ├── tests/                  # Development test scripts
│   └── scripts/                # Development utility scripts
├── README.md                   # Main project documentation
├── requirements.txt            # Production dependencies
├── pyproject.toml             # Project configuration
└── setup.py                   # Package setup
```

## 🗂️ File Naming Conventions

### Debug Scripts (`organized/debug/`)
- `debug_comprehensive_testing.py` - **MAIN DEBUG SCRIPT** - Tests all 3 CDP modes with detailed analysis

### Test Scripts (`organized/tests/`)
- `test_essential_validation.py` - **MAIN TEST** - Essential functionality validation
- `test_final_comprehensive_validation.py` - Comprehensive validation with subprocess isolation
- `test_all_modes_comprehensive.py` - All 3 CDP modes testing
- `test_cdp_modes_individual.py` - Individual CDP mode testing
- `test_verizon_regression_comprehensive.py` - Verizon.com regression testing
- `test_google_regression_comprehensive.py` - Google.com regression testing
- `test_model_loading_performance.py` - Model loading performance testing
- `test_runner_optimization.py` - Runner optimization testing
- `test_production_ready_comprehensive.py` - Production readiness testing
- `test_production_ready_optimized.py` - Optimized production testing
- `optimized_test_runner.py` - TestSuiteRunner for large test suites

### Reports (`organized/reports/`)
- `report_<analysis>_<date>.md` - Analysis reports
- `report_<test>_results_<date>.json` - Test results
- `report_<performance>_<date>.log` - Performance logs

### Scripts (`organized/scripts/`)
- `script_<utility>_<purpose>.py` - Utility scripts
- `script_<maintenance>_<action>.py` - Maintenance scripts

## 🧪 Test Categories

### 1. CDP Mode Tests
- `test_dom_only_validation.py` - DOM-only mode testing
- `test_accessibility_only_validation.py` - Accessibility-only mode testing
- `test_both_mode_validation.py` - Both mode testing
- `test_all_modes_comprehensive.py` - All modes comprehensive testing

### 2. Performance Tests
- `test_model_loading_performance.py` - Model loading optimization
- `test_runner_initialization.py` - Runner initialization testing
- `test_memory_usage.py` - Memory usage analysis

### 3. Integration Tests
- `test_dom_accessibility_binding.py` - DOM+Accessibility binding
- `test_element_extraction.py` - Element extraction testing
- `test_text_processing.py` - Text processing validation

### 4. Regression Tests
- `test_verizon_regression.py` - Verizon.com regression testing
- `test_google_regression.py` - Google.com regression testing
- `test_framework_regression.py` - Framework regression testing

## 🔧 Debug Utilities

### 1. CDP Debugging
- `debug_cdp_integration.py` - CDP integration debugging
- `debug_dom_snapshot.py` - DOM snapshot debugging
- `debug_accessibility_structure.py` - Accessibility tree debugging

### 2. Element Processing
- `debug_element_extraction.py` - Element extraction debugging
- `debug_text_processing.py` - Text processing debugging
- `debug_node_binding.py` - Node binding debugging

### 3. Performance Debugging
- `debug_timing_analysis.py` - Timing analysis debugging
- `debug_memory_usage.py` - Memory usage debugging
- `debug_model_loading.py` - Model loading debugging

## 📊 Reports and Analysis

### 1. Performance Reports
- `report_performance_analysis_2025-09-09.md` - Performance analysis
- `report_timing_breakdown_2025-09-09.log` - Timing breakdown logs
- `report_memory_usage_2025-09-09.json` - Memory usage data

### 2. Test Results
- `report_test_results_2025-09-09.json` - Comprehensive test results
- `report_regression_test_2025-09-09.md` - Regression test results
- `report_verizon_analysis_2025-09-09.md` - Verizon.com analysis

### 3. Framework Analysis
- `report_cdp_analysis_2025-09-09.md` - CDP mode analysis
- `report_element_extraction_2025-09-09.md` - Element extraction analysis
- `report_binding_analysis_2025-09-09.md` - Node binding analysis

## 🚀 Quick Start Guide

### Running Tests
```bash
# Run all CDP modes
python organized/tests/test_all_modes_comprehensive.py

# Run specific mode
python organized/tests/test_dom_only_validation.py

# Run regression tests
python organized/tests/test_verizon_regression.py
```

### Debugging Issues
```bash
# Debug CDP integration
python organized/debug/debug_cdp_integration.py

# Debug element extraction
python organized/debug/debug_element_extraction.py

# Debug performance
python organized/debug/debug_timing_analysis.py
```

### Generating Reports
```bash
# Generate performance report
python organized/scripts/script_generate_performance_report.py

# Generate test results
python organized/scripts/script_generate_test_report.py
```

## 📋 Maintenance Tasks

### Daily
- Run regression tests
- Check performance metrics
- Review error logs

### Weekly
- Update test data
- Clean up old reports
- Review debug scripts

### Monthly
- Comprehensive performance analysis
- Framework optimization review
- Documentation updates

## 🔍 Troubleshooting

### Common Issues
1. **Import Errors**: Check Python path and dependencies
2. **Runtime Errors**: Check environment variables and configuration
3. **Performance Issues**: Check model loading and memory usage
4. **Test Failures**: Check CDP mode configuration and element extraction

### Debug Steps
1. Run debug scripts to identify issues
2. Check logs for error details
3. Verify configuration and dependencies
4. Test individual components
5. Run comprehensive tests

## 📚 Documentation

- `README.md` - Main project documentation
- `organized/PROJECT_ORGANIZATION.md` - This file
- `organized/reports/` - Analysis reports
- `src/her/` - Source code documentation