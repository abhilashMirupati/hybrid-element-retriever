#!/usr/bin/env python3
"""
Comprehensive Verizon Test Runner

Runs the Verizon automation test in both semantic and no-semantic modes
with hierarchy enabled by default to analyze the differences.
"""

import os
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set environment variables
os.environ["HER_CACHE_DIR"] = str(Path(".her_cache").resolve())

# Import the fixed test
from test_verizon_fixed import FixedVerizonAutomationTest


def run_test_mode(semantic_mode: bool, hierarchy_mode: bool = True):
    """Run test in a specific mode."""
    mode_name = "Semantic" if semantic_mode else "No-Semantic"
    hierarchy_name = "With Hierarchy" if hierarchy_mode else "No Hierarchy"
    
    print(f"\n{'='*100}")
    print(f"🚀 RUNNING TEST: {mode_name} Mode {hierarchy_name}")
    print(f"{'='*100}")
    
    # Run test with visible browser
    test = FixedVerizonAutomationTest(
        headless=False,
        semantic_mode=semantic_mode,
        hierarchy_mode=hierarchy_mode
    )
    
    results = test.run_verizon_test()
    
    # Print summary
    total_steps = len(results)
    successful_steps = sum(1 for r in results if r["result"].get("success", False))
    success_rate = (successful_steps/total_steps)*100
    
    print(f"\n📊 {mode_name} Mode Results:")
    print(f"   Success Rate: {success_rate:.1f}% ({successful_steps}/{total_steps})")
    print(f"   Hierarchy Mode: {hierarchy_mode}")
    
    return results, success_rate


def main():
    """Run comprehensive tests."""
    print("🚀 Starting Comprehensive Verizon Automation Test")
    print("Testing both Semantic and No-Semantic modes with Hierarchy enabled")
    print("="*100)
    
    results = {}
    
    # Test 1: Semantic Mode with Hierarchy
    print("\n🔍 TEST 1: Semantic Mode with Hierarchy")
    results["semantic_with_hierarchy"], success_rate_1 = run_test_mode(semantic_mode=True, hierarchy_mode=True)
    
    # Wait between tests
    time.sleep(5)
    
    # Test 2: No-Semantic Mode with Hierarchy  
    print("\n🔍 TEST 2: No-Semantic Mode with Hierarchy")
    results["no_semantic_with_hierarchy"], success_rate_2 = run_test_mode(semantic_mode=False, hierarchy_mode=True)
    
    # Generate comprehensive comparison
    print(f"\n{'='*100}")
    print("📊 COMPREHENSIVE COMPARISON")
    print(f"{'='*100}")
    
    print(f"Semantic Mode (Hierarchy):     {success_rate_1:.1f}% success rate")
    print(f"No-Semantic Mode (Hierarchy):  {success_rate_2:.1f}% success rate")
    
    # Detailed step-by-step comparison
    print(f"\n📋 STEP-BY-STEP COMPARISON:")
    print(f"{'Step':<4} {'Description':<40} {'Semantic':<12} {'No-Semantic':<12} {'Difference':<12}")
    print("-" * 90)
    
    semantic_results = results["semantic_with_hierarchy"]
    no_semantic_results = results["no_semantic_with_hierarchy"]
    
    for i in range(max(len(semantic_results), len(no_semantic_results))):
        step_num = i + 1
        
        # Get semantic result
        if i < len(semantic_results):
            sem_success = "✅ SUCCESS" if semantic_results[i]["result"].get("success", False) else "❌ FAILED"
            sem_desc = semantic_results[i]["step"][:38] + ".." if len(semantic_results[i]["step"]) > 40 else semantic_results[i]["step"]
        else:
            sem_success = "N/A"
            sem_desc = "N/A"
            
        # Get no-semantic result
        if i < len(no_semantic_results):
            nosem_success = "✅ SUCCESS" if no_semantic_results[i]["result"].get("success", False) else "❌ FAILED"
            nosem_desc = no_semantic_results[i]["step"][:38] + ".." if len(no_semantic_results[i]["step"]) > 40 else no_semantic_results[i]["step"]
        else:
            nosem_success = "N/A"
            nosem_desc = "N/A"
            
        # Calculate difference
        if sem_success == nosem_success:
            diff = "SAME"
        elif sem_success == "✅ SUCCESS" and nosem_success == "❌ FAILED":
            diff = "SEMANTIC BETTER"
        elif sem_success == "❌ FAILED" and nosem_success == "✅ SUCCESS":
            diff = "NO-SEMANTIC BETTER"
        else:
            diff = "DIFFERENT"
            
        print(f"{step_num:<4} {sem_desc:<40} {sem_success:<12} {nosem_success:<12} {diff:<12}")
    
    print(f"\n✅ Comprehensive test completed!")
    print(f"📄 Results saved to:")
    print(f"   - verizon_automation_results_semantic.json")
    print(f"   - verizon_automation_results_no_semantic.json")


if __name__ == "__main__":
    main()