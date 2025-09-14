#!/usr/bin/env python3
"""
Simple runner for Verizon automation test
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set environment variables
os.environ["HER_USE_SEMANTIC_SEARCH"] = "true"
os.environ["HER_CACHE_DIR"] = str(Path(".her_cache").resolve())

# Import and run test
from test_verizon_automation import VerizonAutomationTest

if __name__ == "__main__":
    print("🚀 Starting Verizon Automation Test")
    print("=" * 60)
    
    # Run test with visible browser (headless=False)
    test = VerizonAutomationTest(headless=False)
    results = test.run_verizon_test()
    
    print("\n✅ Test execution completed!")
    print(f"Results saved to: verizon_automation_results.json")