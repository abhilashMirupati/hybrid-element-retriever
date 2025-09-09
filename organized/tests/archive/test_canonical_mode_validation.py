#!/usr/bin/env python3
"""Test different canonical descriptor building modes."""

import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from her.runner import run_steps
from her.config import set_canonical_mode, CanonicalMode, print_config

def test_canonical_mode(mode: CanonicalMode, test_name: str):
    """Test a specific canonical mode."""
    print(f"\n{'='*60}")
    print(f"🧪 TESTING: {test_name}")
    print(f"📋 Mode: {mode.value}")
    print(f"{'='*60}")
    
    # Set the canonical mode
    set_canonical_mode(mode)
    print_config()
    
    # Test steps
    steps = [
        "Open https://www.verizon.com/",
        "Click on Phones btn in top"
    ]
    
    start_time = time.time()
    
    try:
        print(f"\n🚀 Starting test with {mode.value} mode...")
        run_steps(steps, headless=True)
        print(f"✅ Test PASSED with {mode.value} mode")
        return True
    except Exception as e:
        print(f"❌ Test FAILED with {mode.value} mode: {e}")
        return False
    finally:
        end_time = time.time()
        duration = end_time - start_time
        print(f"⏱️  Duration: {duration:.2f} seconds")

def main():
    """Test all canonical modes."""
    print("🔬 CANONICAL DESCRIPTOR MODE TESTING")
    print("Testing accuracy and performance with different modes")
    
    results = {}
    
    # Test DOM only mode
    results['dom_only'] = test_canonical_mode(CanonicalMode.DOM_ONLY, "DOM Only Mode")
    
    # Test Accessibility only mode  
    results['accessibility_only'] = test_canonical_mode(CanonicalMode.ACCESSIBILITY_ONLY, "Accessibility Only Mode")
    
    # Test Both mode (default)
    results['both'] = test_canonical_mode(CanonicalMode.BOTH, "Both DOM + Accessibility Mode")
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"📊 TEST RESULTS SUMMARY")
    print(f"{'='*60}")
    
    for mode, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {mode:20} : {status}")
    
    print(f"\n💡 RECOMMENDATIONS:")
    if results['both']:
        print("   ✅ BOTH mode works - use for maximum accuracy")
    elif results['dom_only']:
        print("   ⚠️  Only DOM mode works - accessibility extraction may have issues")
    elif results['accessibility_only']:
        print("   ⚠️  Only Accessibility mode works - DOM extraction may have issues")
    else:
        print("   ❌ All modes failed - check framework setup")

if __name__ == "__main__":
    main()