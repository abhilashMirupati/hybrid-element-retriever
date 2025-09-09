#!/usr/bin/env python3
"""
Test script for Phase 3: Enhanced Pipeline (Backward Compatible).
Tests that the query method correctly routes to standard or two-stage processing.
"""

import os
import sys
import subprocess
import time

def test_standard_mode():
    """Test with hierarchy disabled (should use standard mode)."""
    print("=" * 60)
    print("🔍 TESTING STANDARD MODE (Hierarchy Disabled)")
    print("=" * 60)
    
    # Ensure hierarchy is disabled
    env = os.environ.copy()
    env['HER_USE_HIERARCHY'] = 'false'
    env['HER_USE_TWO_STAGE'] = 'false'
    
    script = """
import sys
sys.path.append('/workspace')
from src.her.runner import Runner
from src.her.config import get_config

# Test configuration
config = get_config()
print(f"Use Hierarchy: {config.should_use_hierarchy()}")
print(f"Use Two-Stage: {config.should_use_two_stage()}")

# Test basic functionality
runner = Runner()
print("✅ Runner created successfully")

# Test query with standard mode
try:
    snapshot = runner._snapshot("https://www.verizon.com/")
    elements = snapshot.get('elements', [])
    print(f"✅ Snapshot completed: {len(elements)} elements")
    
    # Test query
    result = runner._resolve_selector("Click on the 'Shop' button", snapshot)
    print(f"✅ Query completed: {result}")
    
    # Check if standard mode was used
    if "hybrid-minilm-markuplm" in str(result):
        print("✅ Standard mode used correctly")
    else:
        print("❌ Standard mode not used")
        exit(1)
    
    print("✅ STANDARD MODE TEST PASSED")
    exit(0)
    
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)
"""
    
    result = subprocess.run([sys.executable, '-c', script], 
                          env=env, capture_output=True, text=True, cwd='/workspace')
    
    print("STDOUT:")
    print(result.stdout)
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    
    return result.returncode == 0

def test_hierarchy_only_mode():
    """Test with hierarchy enabled but two-stage disabled."""
    print("=" * 60)
    print("🔍 TESTING HIERARCHY ONLY MODE")
    print("=" * 60)
    
    # Enable hierarchy but disable two-stage
    env = os.environ.copy()
    env['HER_USE_HIERARCHY'] = 'true'
    env['HER_USE_TWO_STAGE'] = 'false'
    
    script = """
import sys
sys.path.append('/workspace')
from src.her.runner import Runner
from src.her.config import get_config

# Test configuration
config = get_config()
print(f"Use Hierarchy: {config.should_use_hierarchy()}")
print(f"Use Two-Stage: {config.should_use_two_stage()}")

# Test basic functionality
runner = Runner()
print("✅ Runner created successfully")

# Test query with hierarchy only mode
try:
    snapshot = runner._snapshot("https://www.verizon.com/")
    elements = snapshot.get('elements', [])
    print(f"✅ Snapshot completed: {len(elements)} elements")
    
    # Check if elements have context
    elements_with_context = [e for e in elements if 'context' in e]
    print(f"Elements with context: {len(elements_with_context)}")
    
    if len(elements_with_context) > 0:
        print("✅ Hierarchy context added successfully")
    else:
        print("❌ No hierarchy context found")
        exit(1)
    
    # Test query
    result = runner._resolve_selector("Click on the 'Shop' button", snapshot)
    print(f"✅ Query completed: {result}")
    
    # Check if standard mode was used (since two-stage is disabled)
    if "hybrid-minilm-markuplm" in str(result):
        print("✅ Standard mode used correctly (hierarchy context available)")
    else:
        print("❌ Standard mode not used")
        exit(1)
    
    print("✅ HIERARCHY ONLY MODE TEST PASSED")
    exit(0)
    
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)
"""
    
    result = subprocess.run([sys.executable, '-c', script], 
                          env=env, capture_output=True, text=True, cwd='/workspace')
    
    print("STDOUT:")
    print(result.stdout)
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    
    return result.returncode == 0

def test_two_stage_mode():
    """Test with both hierarchy and two-stage enabled."""
    print("=" * 60)
    print("🔍 TESTING TWO-STAGE MODE")
    print("=" * 60)
    
    # Enable both hierarchy and two-stage
    env = os.environ.copy()
    env['HER_USE_HIERARCHY'] = 'true'
    env['HER_USE_TWO_STAGE'] = 'true'
    
    script = """
import sys
sys.path.append('/workspace')
from src.her.runner import Runner
from src.her.config import get_config

# Test configuration
config = get_config()
print(f"Use Hierarchy: {config.should_use_hierarchy()}")
print(f"Use Two-Stage: {config.should_use_two_stage()}")

# Test basic functionality
runner = Runner()
print("✅ Runner created successfully")

# Test query with two-stage mode
try:
    snapshot = runner._snapshot("https://www.verizon.com/")
    elements = snapshot.get('elements', [])
    print(f"✅ Snapshot completed: {len(elements)} elements")
    
    # Check if elements have context
    elements_with_context = [e for e in elements if 'context' in e]
    print(f"Elements with context: {len(elements_with_context)}")
    
    if len(elements_with_context) > 0:
        print("✅ Hierarchy context added successfully")
    else:
        print("❌ No hierarchy context found")
        exit(1)
    
    # Test query
    result = runner._resolve_selector("Click on the 'Shop' button", snapshot)
    print(f"✅ Query completed: {result}")
    
    # Check if two-stage mode was used
    if "two-stage-markuplm" in str(result):
        print("✅ Two-stage mode used correctly")
    else:
        print("❌ Two-stage mode not used")
        exit(1)
    
    print("✅ TWO-STAGE MODE TEST PASSED")
    exit(0)
    
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)
"""
    
    result = subprocess.run([sys.executable, '-c', script], 
                          env=env, capture_output=True, text=True, cwd='/workspace')
    
    print("STDOUT:")
    print(result.stdout)
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    
    return result.returncode == 0

def main():
    """Run all Phase 3 tests."""
    print("🚀 PHASE 3 TESTING: Enhanced Pipeline (Backward Compatible)")
    print("=" * 80)
    
    start_time = time.time()
    
    # Run tests
    tests = [
        ("Standard Mode", test_standard_mode),
        ("Hierarchy Only Mode", test_hierarchy_only_mode),
        ("Two-Stage Mode", test_two_stage_mode),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        test_start = time.time()
        success = test_func()
        test_time = time.time() - test_start
        
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"\n{status} - {test_name} ({test_time:.2f}s)")
        results.append((test_name, success, test_time))
    
    # Summary
    total_time = time.time() - start_time
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    print("\n" + "="*80)
    print("📊 PHASE 3 TEST RESULTS SUMMARY")
    print("="*80)
    
    for test_name, success, test_time in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} - {test_name} ({test_time:.2f}s)")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    print(f"Total time: {total_time:.2f}s")
    
    if passed == total:
        print("🎉 PHASE 3 IMPLEMENTATION SUCCESSFUL!")
        print("✅ All tests passed - enhanced pipeline working correctly")
        print("✅ Backward compatibility maintained")
        print("✅ Two-stage processing working")
        print("✅ Ready for Phase 4")
    else:
        print("❌ PHASE 3 IMPLEMENTATION ISSUES DETECTED")
        print("🔧 Please fix failing tests before proceeding to Phase 4")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)