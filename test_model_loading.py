#!/usr/bin/env python3
"""
Test Model Loading Behavior
Check if models are loaded once and cached
"""

import time
import os
from her.runner import run_steps

def test_model_loading_behavior():
    """Test if models are loaded once and reused"""
    
    print("🔬 TESTING MODEL LOADING BEHAVIOR")
    print("=" * 60)
    
    # Test 1: First run (should load models)
    print("\n📋 TEST 1: First run (should load models)")
    os.environ['HER_CANONICAL_MODE'] = 'both'
    
    start_time = time.time()
    try:
        result1 = run_steps(['Open https://www.google.com/'], headless=True)
        duration1 = time.time() - start_time
        print(f"✅ First run: {duration1:.2f}s")
    except Exception as e:
        print(f"❌ First run failed: {e}")
        return
    
    # Test 2: Second run (should reuse models)
    print("\n📋 TEST 2: Second run (should reuse models)")
    start_time = time.time()
    try:
        result2 = run_steps(['Open https://www.google.com/'], headless=True)
        duration2 = time.time() - start_time
        print(f"✅ Second run: {duration2:.2f}s")
    except Exception as e:
        print(f"❌ Second run failed: {e}")
        return
    
    # Test 3: Different mode (should reuse models)
    print("\n📋 TEST 3: Different mode (should reuse models)")
    os.environ['HER_CANONICAL_MODE'] = 'dom_only'
    start_time = time.time()
    try:
        result3 = run_steps(['Open https://www.google.com/'], headless=True)
        duration3 = time.time() - start_time
        print(f"✅ Different mode: {duration3:.2f}s")
    except Exception as e:
        print(f"❌ Different mode failed: {e}")
        return
    
    # Analysis
    print(f"\n📊 ANALYSIS:")
    print(f"   First run: {duration1:.2f}s")
    print(f"   Second run: {duration2:.2f}s")
    print(f"   Different mode: {duration3:.2f}s")
    
    if duration2 < duration1 * 0.5:
        print("   ✅ Models appear to be cached (second run much faster)")
    else:
        print("   ❌ Models are being reloaded each time")
    
    if duration3 < duration1 * 0.5:
        print("   ✅ Models are shared between modes")
    else:
        print("   ❌ Models are reloaded for different modes")

if __name__ == "__main__":
    test_model_loading_behavior()