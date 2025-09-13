#!/usr/bin/env python3
"""
Test script to verify runner reuse and model loading optimization.
"""

import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from src.her.testing.natural_test_runner import NaturalTestRunner

def test_runner_reuse():
    """Test reusing the same runner instance for multiple tests."""
    print("🧪 Testing Runner Reuse and Model Loading...")
    
    # Create runner once
    print("📦 Creating first runner...")
    start_time = time.time()
    runner = NaturalTestRunner(headless=True)
    first_creation_time = time.time() - start_time
    print(f"✅ First runner created in {first_creation_time:.2f}s")
    
    # Run first test
    print("🚀 Running first test...")
    test_start = time.time()
    result1 = runner.run_test(
        test_name="Test 1",
        steps=["Navigate to \"https://www.google.com/\""],
        start_url="https://www.google.com/"
    )
    test1_time = time.time() - test_start
    print(f"✅ First test completed in {test1_time:.2f}s")
    
    # Run second test with same runner
    print("🚀 Running second test with same runner...")
    test_start = time.time()
    result2 = runner.run_test(
        test_name="Test 2", 
        steps=["Navigate to \"https://www.google.com/\""],
        start_url="https://www.google.com/"
    )
    test2_time = time.time() - test_start
    print(f"✅ Second test completed in {test2_time:.2f}s")
    
    # Create second runner to see if models reload
    print("📦 Creating second runner...")
    start_time = time.time()
    runner2 = NaturalTestRunner(headless=True)
    second_creation_time = time.time() - start_time
    print(f"✅ Second runner created in {second_creation_time:.2f}s")
    
    # Cleanup
    runner.runner._close()
    runner2.runner._close()
    
    print(f"\n📊 Results:")
    print(f"   First runner creation: {first_creation_time:.2f}s")
    print(f"   First test execution: {test1_time:.2f}s")
    print(f"   Second test execution: {test2_time:.2f}s")
    print(f"   Second runner creation: {second_creation_time:.2f}s")
    print(f"   Test 1 success: {result1['success']}")
    print(f"   Test 2 success: {result2['success']}")
    
    if second_creation_time < 5.0:
        print("✅ Models are properly shared between runners!")
    else:
        print("❌ Models are being reloaded for each runner!")

if __name__ == "__main__":
    test_runner_reuse()