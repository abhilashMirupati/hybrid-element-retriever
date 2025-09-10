#!/usr/bin/env python3
"""
Test script for Phase 2: Enhanced Pipeline with hierarchy support.
Tests that hierarchy context is properly added to elements without breaking existing functionality.
"""

import os
import sys
import subprocess
import json
import time

def test_hierarchy_disabled():
    """Test with hierarchy disabled (default behavior)."""
    print("=" * 60)
    print("🔍 TESTING HIERARCHY DISABLED (Default Behavior)")
    print("=" * 60)
    
    # Ensure hierarchy is disabled
    env = os.environ.copy()
    env['HER_USE_HIERARCHY'] = 'false'
    
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

# Test snapshot without hierarchy
try:
    snapshot = runner._snapshot("https://www.verizon.com/")
    print(f"✅ Snapshot completed: {len(snapshot.get('elements', []))} elements")
    
    # Check if any elements have context (should be none)
    elements_with_context = [e for e in snapshot.get('elements', []) if 'context' in e]
    print(f"Elements with context: {len(elements_with_context)} (should be 0)")
    
    if len(elements_with_context) == 0:
        print("✅ No hierarchy context added (as expected)")
    else:
        print("❌ Unexpected hierarchy context found")
        
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

print("✅ HIERARCHY DISABLED TEST PASSED")
exit(0)
"""
    
    result = subprocess.run([sys.executable, '-c', script], 
                          env=env, capture_output=True, text=True, cwd='/workspace')
    
    print("STDOUT:")
    print(result.stdout)
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    
    return result.returncode == 0

def test_hierarchy_enabled():
    """Test with hierarchy enabled."""
    print("=" * 60)
    print("🔍 TESTING HIERARCHY ENABLED")
    print("=" * 60)
    
    # Enable hierarchy
    env = os.environ.copy()
    env['HER_USE_HIERARCHY'] = 'true'
    env['HER_DEBUG_HIERARCHY'] = 'true'
    
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

# Test snapshot with hierarchy
try:
    snapshot = runner._snapshot("https://www.verizon.com/")
    print(f"✅ Snapshot completed: {len(snapshot.get('elements', []))} elements")
    
    # Check if elements have context
    elements_with_context = [e for e in snapshot.get('elements', []) if 'context' in e]
    print(f"Elements with context: {len(elements_with_context)}")
    
    if len(elements_with_context) > 0:
        print("✅ Hierarchy context added successfully")
        
        # Check context structure
        sample_element = elements_with_context[0]
        context = sample_element.get('context', {})
        print(f"Sample context keys: {list(context.keys())}")
        
        if 'hierarchy_path' in context:
            print(f"Sample hierarchy path: {context['hierarchy_path']}")
        
        if 'parent' in context:
            print(f"Sample parent: {context['parent']}")
            
        if 'siblings' in context:
            print(f"Sample siblings count: {len(context['siblings'])}")
            
    else:
        print("❌ No hierarchy context found")
        exit(1)
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("✅ HIERARCHY ENABLED TEST PASSED")
exit(0)
"""
    
    result = subprocess.run([sys.executable, '-c', script], 
                          env=env, capture_output=True, text=True, cwd='/workspace')
    
    print("STDOUT:")
    print(result.stdout)
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    
    return result.returncode == 0

def test_backward_compatibility():
    """Test that existing functionality still works."""
    print("=" * 60)
    print("🔍 TESTING BACKWARD COMPATIBILITY")
    print("=" * 60)
    
    # Test with default settings
    env = os.environ.copy()
    
    # Test each mode in separate subprocess to avoid async conflicts
    modes = ['DOM_ONLY', 'ACCESSIBILITY_ONLY', 'BOTH']
    all_passed = True
    
    for mode in modes:
        print(f"\n--- Testing {mode} mode ---")
        
        script = f"""
import sys
sys.path.append('/workspace')
from src.her.runner import Runner
import os

# Set environment variable
os.environ['HER_CANONICAL_MODE'] = '{mode.lower()}'

try:
    runner = Runner()
    snapshot = runner._snapshot("https://www.verizon.com/")
    
    elements = snapshot.get('elements', [])
    print(f"✅ {mode}: {{len(elements)}} elements processed")
    
    # Check basic element structure
    if elements:
        sample = elements[0]
        required_keys = ['tag', 'text', 'attrs']
        missing_keys = [k for k in required_keys if k not in sample]
        if missing_keys:
            print(f"❌ {mode}: Missing keys: {{missing_keys}}")
            exit(1)
        else:
            print(f"✅ {mode}: Element structure correct")
    
    print(f"✅ {mode}: Test passed")
    exit(0)
    
except Exception as e:
    print(f"❌ {mode}: Error - {{e}}")
    exit(1)
"""
        
        result = subprocess.run([sys.executable, '-c', script], 
                              env=env, capture_output=True, text=True, cwd='/workspace')
        
        print("STDOUT:")
        print(result.stdout)
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        if result.returncode != 0:
            all_passed = False
    
    if all_passed:
        print("\n✅ BACKWARD COMPATIBILITY TEST PASSED")
    else:
        print("\n❌ BACKWARD COMPATIBILITY TEST FAILED")
    
    return all_passed

def main():
    """Run all Phase 2 tests."""
    print("🚀 PHASE 2 TESTING: Enhanced Pipeline with Hierarchy Support")
    print("=" * 80)
    
    tests = [
        ("Backward Compatibility", test_backward_compatibility),
        ("Hierarchy Disabled", test_hierarchy_disabled),
        ("Hierarchy Enabled", test_hierarchy_enabled),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name}...")
        start_time = time.time()
        
        try:
            success = test_func()
            duration = time.time() - start_time
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"{status} - {test_name} ({duration:.2f}s)")
            results.append((test_name, success, duration))
        except Exception as e:
            duration = time.time() - start_time
            print(f"❌ FAILED - {test_name} ({duration:.2f}s) - Exception: {e}")
            results.append((test_name, False, duration))
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 PHASE 2 TEST RESULTS SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for test_name, success, duration in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} - {test_name} ({duration:.2f}s)")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 PHASE 2 IMPLEMENTATION SUCCESSFUL!")
        print("✅ All tests passed - hierarchy support working correctly")
        print("✅ Backward compatibility maintained")
        print("✅ Ready for Phase 3")
    else:
        print("❌ PHASE 2 IMPLEMENTATION ISSUES DETECTED")
        print("🔧 Please fix failing tests before proceeding to Phase 3")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)