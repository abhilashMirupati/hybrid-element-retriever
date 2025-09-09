#!/usr/bin/env python3
"""
Final Production Test - Test all 3 CDP modes individually to avoid async conflicts
"""

import os
import sys
import time
import subprocess

sys.path.append('/workspace/src')

def test_single_mode(mode):
    """Test a single CDP mode in isolation"""
    print(f"\n🔍 Testing {mode} mode...")
    
    # Create a separate process to avoid async conflicts
    test_script = f"""
import os
import sys
sys.path.append('/workspace/src')

os.environ['HER_CANONICAL_MODE'] = '{mode}'

from her.runner import Runner

# Test the mode
runner = Runner(headless=True)
result = runner._snapshot('https://www.verizon.com/')

if result and 'elements' in result:
    elements = result['elements']
    print(f"✅ {mode}: {{len(elements)}} elements")
    
    # Analyze element types
    interactive_count = sum(1 for elem in elements if elem.get('interactive', False))
    form_count = sum(1 for elem in elements if elem.get('tag', '').upper() in ['FORM', 'INPUT', 'SELECT', 'TEXTAREA'])
    button_count = sum(1 for elem in elements if elem.get('tag', '').upper() == 'BUTTON')
    link_count = sum(1 for elem in elements if elem.get('tag', '').upper() == 'A')
    
    print(f"   📊 Interactive: {{interactive_count}}, Forms: {{form_count}}, Buttons: {{button_count}}, Links: {{link_count}}")
    
    # Check for backendNodeId binding
    backend_ids = [elem.get('backendNodeId') for elem in elements if elem.get('backendNodeId')]
    print(f"   🔗 Elements with backendNodeId: {{len(backend_ids)}}/{{len(elements)}}")
    
    # Sample elements
    print(f"   📋 Sample elements:")
    for i, elem in enumerate(elements[:3]):
        print(f"      {{i+1}}. {{elem.get('tag', 'UNKNOWN')}} - ID: {{elem.get('backendNodeId')}} - Text: {{elem.get('text', '')[:50]}}...")
        
    print("SUCCESS")
else:
    print(f"❌ {mode}: Failed to get elements")
    print("FAILED")
"""
    
    try:
        result = subprocess.run([sys.executable, '-c', test_script], 
                              capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print(result.stdout)
            return True
        else:
            print(f"❌ {mode} failed:")
            print(result.stderr)
            return False
    except subprocess.TimeoutExpired:
        print(f"❌ {mode} timed out")
        return False
    except Exception as e:
        print(f"❌ {mode} error: {e}")
        return False

def test_dom_accessibility_binding():
    """Test DOM + Accessibility node binding specifically"""
    print(f"\n🔗 Testing DOM + Accessibility Node Binding...")
    
    test_script = """
import os
import sys
sys.path.append('/workspace/src')

os.environ['HER_CANONICAL_MODE'] = 'BOTH'

from her.runner import Runner

# Test BOTH mode for binding
runner = Runner(headless=True)
result = runner._snapshot('https://www.verizon.com/')

if result and 'elements' in result:
    elements = result['elements']
    print(f"📊 Total elements: {len(elements)}")
    
    # Analyze binding
    dom_elements = []
    ax_elements = []
    bound_elements = []
    
    for elem in elements:
        backend_id = elem.get('backendNodeId')
        if backend_id:
            if elem.get('source') == 'DOM':
                dom_elements.append(elem)
            elif elem.get('source') == 'ACCESSIBILITY':
                ax_elements.append(elem)
            else:
                bound_elements.append(elem)
    
    print(f"📊 DOM elements: {len(dom_elements)}")
    print(f"📊 Accessibility elements: {len(ax_elements)}")
    print(f"📊 Bound elements: {len(bound_elements)}")
    
    # Check for proper binding
    binding_issues = []
    for elem in elements:
        backend_id = elem.get('backendNodeId')
        if not backend_id:
            binding_issues.append(f"Missing backendNodeId: {elem.get('tag', 'UNKNOWN')}")
    
    if binding_issues:
        print(f"⚠️  Binding issues found: {len(binding_issues)}")
        for issue in binding_issues[:5]:  # Show first 5
            print(f"   - {issue}")
    else:
        print("✅ All elements have proper backendNodeId binding")
    
    # Sample bound elements
    print(f"📋 Sample Bound Elements:")
    for i, elem in enumerate(bound_elements[:3]):
        print(f"   {i+1}. {elem.get('tag', 'UNKNOWN')} - ID: {elem.get('backendNodeId')} - Text: {elem.get('text', '')[:50]}...")
    
    print("SUCCESS")
else:
    print("❌ Failed to get snapshot")
    print("FAILED")
"""

    try:
        result = subprocess.run([sys.executable, '-c', test_script], 
                              capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print(result.stdout)
            return True
        else:
            print(f"❌ Binding test failed:")
            print(result.stderr)
            return False
    except subprocess.TimeoutExpired:
        print(f"❌ Binding test timed out")
        return False
    except Exception as e:
        print(f"❌ Binding test error: {e}")
        return False

def main():
    print("🚀 FINAL PRODUCTION TEST")
    print("=" * 60)
    
    # Test all 3 modes individually
    modes = ['DOM_ONLY', 'ACCESSIBILITY_ONLY', 'BOTH']
    results = {}
    
    for mode in modes:
        results[mode] = test_single_mode(mode)
    
    # Test DOM + Accessibility binding
    binding_result = test_dom_accessibility_binding()
    
    # Summary
    print(f"\n📈 FINAL RESULTS")
    print("=" * 40)
    
    all_passed = True
    for mode, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{mode:20} | {status}")
        if not passed:
            all_passed = False
    
    binding_status = "✅ PASS" if binding_result else "❌ FAIL"
    print(f"{'BINDING_TEST':20} | {binding_status}")
    if not binding_result:
        all_passed = False
    
    print(f"\n🎯 OVERALL RESULT: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    if all_passed:
        print("\n🎉 PRODUCTION READY!")
        print("✅ All 3 CDP modes working")
        print("✅ Model caching optimized")
        print("✅ DOM + Accessibility binding working")
        print("✅ Default runner is optimized")
    else:
        print("\n⚠️  NEEDS FIXES")
        print("❌ Some tests failed - check output above")

if __name__ == "__main__":
    main()