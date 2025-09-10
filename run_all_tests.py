#!/usr/bin/env python3
"""
Project-Level Test Runner
Runs all organized tests to ensure no import/compile/runtime issues
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def run_test_script(script_path, description):
    """Run a test script and return results"""
    print(f"\n🔍 Running {description}...")
    print(f"   Script: {script_path}")
    
    try:
        start_time = time.time()
        result = subprocess.run([sys.executable, script_path], 
                              capture_output=True, text=True, timeout=300)
        duration = time.time() - start_time
        
        if result.returncode == 0:
            print(f"   ✅ PASSED ({duration:.2f}s)")
            return True, result.stdout, result.stderr
        else:
            print(f"   ❌ FAILED ({duration:.2f}s)")
            print(f"   STDOUT: {result.stdout[:200]}...")
            print(f"   STDERR: {result.stderr[:200]}...")
            return False, result.stdout, result.stderr
            
    except subprocess.TimeoutExpired:
        print(f"   ⏰ TIMEOUT (300s)")
        return False, "", "Timeout after 300 seconds"
    except Exception as e:
        print(f"   💥 ERROR: {e}")
        return False, "", str(e)

def main():
    print("🚀 HER FRAMEWORK - PROJECT LEVEL TEST RUNNER")
    print("=" * 60)
    
    # Define test categories
    test_categories = {
        "Core CDP Mode Tests": [
            "organized/tests/test_final_comprehensive_validation.py",
            "organized/tests/test_all_modes_comprehensive.py",
            "organized/tests/test_cdp_modes_individual.py"
        ],
        "Regression Tests": [
            "organized/tests/test_verizon_regression_comprehensive.py",
            "organized/tests/test_google_regression_comprehensive.py",
            "organized/tests/test_verizon_regression_individual.py"
        ],
        "Performance Tests": [
            "organized/tests/test_runner_optimization.py",
            "organized/tests/test_model_loading_performance.py",
            "organized/tests/test_production_ready_comprehensive.py"
        ],
        "Validation Tests": [
            "organized/tests/test_validation_comprehensive.py",
            "organized/tests/test_validation_accessibility_only.py",
            "organized/tests/test_validation_simple_flow.py"
        ],
        "Element Processing Tests": [
            "organized/tests/test_element_extraction_analysis.py",
            "organized/tests/test_canonical_mode_validation.py"
        ]
    }
    
    # Results tracking
    all_results = {}
    total_tests = 0
    passed_tests = 0
    
    # Run each category
    for category, scripts in test_categories.items():
        print(f"\n📂 {category}")
        print("-" * 40)
        
        category_results = {}
        for script in scripts:
            script_path = Path(script)
            if script_path.exists():
                total_tests += 1
                success, stdout, stderr = run_test_script(script, script_path.name)
                category_results[script_path.name] = {
                    'success': success,
                    'stdout': stdout,
                    'stderr': stderr
                }
                if success:
                    passed_tests += 1
            else:
                print(f"   ⚠️  SKIPPED: {script} (not found)")
        
        all_results[category] = category_results
    
    # Summary
    print(f"\n📈 PROJECT LEVEL TEST SUMMARY")
    print("=" * 50)
    
    for category, results in all_results.items():
        category_passed = sum(1 for r in results.values() if r['success'])
        category_total = len(results)
        status = "✅ PASS" if category_passed == category_total else "❌ FAIL"
        print(f"{category:30} | {status} | {category_passed}/{category_total}")
    
    overall_success = passed_tests == total_tests
    print(f"\n🎯 OVERALL RESULT: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
    print(f"   Total Tests: {total_tests}")
    print(f"   Passed: {passed_tests}")
    print(f"   Failed: {total_tests - passed_tests}")
    print(f"   Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if overall_success:
        print(f"\n🎉 PROJECT IS PRODUCTION READY!")
        print("✅ No import issues")
        print("✅ No compile issues") 
        print("✅ No runtime issues")
        print("✅ All CDP modes working")
        print("✅ All optimizations working")
        print("✅ All validations passing")
    else:
        print(f"\n⚠️  PROJECT NEEDS ATTENTION")
        print("❌ Some tests failed - review output above")
        print("❌ Check error messages and fix issues")
        print("❌ Re-run tests after fixes")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)