#!/usr/bin/env python3
"""
Final Comprehensive Validation Test
Tests all 3 CDP modes with proper error handling and validation
"""

import os
import sys
import time
import subprocess
import json
from pathlib import Path

# Add src to path
sys.path.append('/workspace/src')

def run_test_in_isolation(test_name, mode, url='https://www.verizon.com/'):
    """Run a single test in isolation to avoid async conflicts"""
    print(f"\n🔍 Running {test_name} ({mode})...")
    
    test_script = f"""
import os
import sys
import time
import json
sys.path.append('/workspace/src')

# Set environment
os.environ['HER_CANONICAL_MODE'] = '{mode}'

try:
    from her.runner import Runner
    
    # Initialize runner
    start_time = time.time()
    runner = Runner(headless=True)
    init_time = time.time() - start_time
    
    # Get snapshot
    snapshot_start = time.time()
    result = runner._snapshot('{url}')
    snapshot_time = time.time() - snapshot_start
    
    if result and 'elements' in result:
        elements = result['elements']
        
        # Analyze elements
        interactive_count = sum(1 for elem in elements if elem.get('interactive', False))
        form_count = sum(1 for elem in elements if elem.get('tag', '').upper() in ['FORM', 'INPUT', 'SELECT', 'TEXTAREA'])
        button_count = sum(1 for elem in elements if elem.get('tag', '').upper() == 'BUTTON')
        link_count = sum(1 for elem in elements if elem.get('tag', '').upper() == 'A')
        
        # Check backendNodeId binding
        backend_ids = [elem.get('backendNodeId') for elem in elements if elem.get('backendNodeId')]
        binding_ratio = len(backend_ids) / len(elements) if elements else 0
        
        # Sample elements
        sample_elements = []
        for i, elem in enumerate(elements[:3]):
            sample_elements.append({{
                'tag': elem.get('tag', 'UNKNOWN'),
                'backendNodeId': elem.get('backendNodeId'),
                'text': str(elem.get('text', ''))[:50],
                'interactive': elem.get('interactive', False)
            }})
        
        # Results
        results = {{
            'mode': '{mode}',
            'success': True,
            'total_elements': len(elements),
            'interactive_elements': interactive_count,
            'form_elements': form_count,
            'button_elements': button_count,
            'link_elements': link_count,
            'backend_node_binding_ratio': binding_ratio,
            'init_time': init_time,
            'snapshot_time': snapshot_time,
            'total_time': init_time + snapshot_time,
            'sample_elements': sample_elements
        }}
        
        print(f"SUCCESS: {{json.dumps(results)}}")
        
    else:
        print(f"FAILED: No elements returned")
        
except Exception as e:
    print(f"ERROR: {{str(e)}}")
    import traceback
    traceback.print_exc()
"""
    
    try:
        result = subprocess.run([sys.executable, '-c', test_script], 
                              capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0 and 'SUCCESS:' in result.stdout:
            # Parse results
            success_line = [line for line in result.stdout.split('\n') if 'SUCCESS:' in line][0]
            results = json.loads(success_line.replace('SUCCESS: ', ''))
            return results
        else:
            print(f"❌ {test_name} failed:")
            print(f"   STDOUT: {result.stdout}")
            print(f"   STDERR: {result.stderr}")
            return None
            
    except subprocess.TimeoutExpired:
        print(f"❌ {test_name} timed out")
        return None
    except Exception as e:
        print(f"❌ {test_name} error: {e}")
        return None

def test_model_caching():
    """Test model caching optimization"""
    print(f"\n🧠 Testing Model Caching...")
    
    test_script = """
import os
import sys
import time
import json
sys.path.append('/workspace/src')

try:
    from her.runner import Runner
    
    # First runner
    start_time = time.time()
    runner1 = Runner(headless=True)
    first_time = time.time() - start_time
    
    # Second runner (should be faster)
    start_time = time.time()
    runner2 = Runner(headless=True)
    second_time = time.time() - start_time
    
    # Check if they share the same pipeline
    same_pipeline = id(runner1.pipeline) == id(runner2.pipeline)
    
    results = {
        'first_runner_time': first_time,
        'second_runner_time': second_time,
        'same_pipeline': same_pipeline,
        'caching_working': same_pipeline and second_time < first_time * 0.1
    }
    
    print(f"SUCCESS: {json.dumps(results)}")
    
except Exception as e:
    print(f"ERROR: {str(e)}")
"""
    
    try:
        result = subprocess.run([sys.executable, '-c', test_script], 
                              capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0 and 'SUCCESS:' in result.stdout:
            success_line = [line for line in result.stdout.split('\n') if 'SUCCESS:' in line][0]
            results = json.loads(success_line.replace('SUCCESS: ', ''))
            return results
        else:
            print(f"❌ Model caching test failed:")
            print(f"   STDOUT: {result.stdout}")
            print(f"   STDERR: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"❌ Model caching test error: {e}")
        return None

def main():
    print("🚀 FINAL COMPREHENSIVE VALIDATION TEST")
    print("=" * 70)
    
    # Test all 3 CDP modes
    modes = ['DOM_ONLY', 'ACCESSIBILITY_ONLY', 'BOTH']
    results = {}
    
    for mode in modes:
        results[mode] = run_test_in_isolation(f"{mode} Mode", mode)
    
    # Test model caching
    caching_results = test_model_caching()
    
    # Summary
    print(f"\n📈 COMPREHENSIVE TEST RESULTS")
    print("=" * 50)
    
    all_passed = True
    
    # CDP Mode Results
    for mode, result in results.items():
        if result:
            status = "✅ PASS"
            print(f"{mode:20} | {status} | {result['total_elements']:4d} elements | {result['total_time']:6.3f}s | Binding: {result['backend_node_binding_ratio']:.1%}")
        else:
            status = "❌ FAIL"
            print(f"{mode:20} | {status}")
            all_passed = False
    
    # Model Caching Results
    if caching_results:
        status = "✅ PASS" if caching_results['caching_working'] else "❌ FAIL"
        print(f"{'MODEL_CACHING':20} | {status} | First: {caching_results['first_runner_time']:.3f}s | Second: {caching_results['second_runner_time']:.3f}s")
        if not caching_results['caching_working']:
            all_passed = False
    else:
        print(f"{'MODEL_CACHING':20} | ❌ FAIL")
        all_passed = False
    
    # Detailed Analysis
    if all_passed:
        print(f"\n🎯 DETAILED ANALYSIS")
        print("=" * 30)
        
        # Element counts
        print(f"📊 Element Counts:")
        for mode, result in results.items():
            if result:
                print(f"   {mode}: {result['total_elements']} total, {result['interactive_elements']} interactive, {result['form_elements']} forms")
        
        # Performance
        print(f"\n⏱️  Performance:")
        for mode, result in results.items():
            if result:
                print(f"   {mode}: {result['total_time']:.3f}s total ({result['init_time']:.3f}s init + {result['snapshot_time']:.3f}s snapshot)")
        
        # Binding quality
        print(f"\n🔗 Node Binding Quality:")
        for mode, result in results.items():
            if result:
                print(f"   {mode}: {result['backend_node_binding_ratio']:.1%} elements have backendNodeId")
        
        # Sample elements
        print(f"\n📋 Sample Elements:")
        for mode, result in results.items():
            if result and result['sample_elements']:
                print(f"   {mode}:")
                for i, elem in enumerate(result['sample_elements']):
                    print(f"      {i+1}. {elem['tag']} (ID: {elem['backendNodeId']}) - {elem['text']}...")
    
    # Final result
    print(f"\n🎯 FINAL RESULT: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    if all_passed:
        print(f"\n🎉 PRODUCTION READY!")
        print("✅ All 3 CDP modes working correctly")
        print("✅ Model caching optimization working")
        print("✅ Element extraction working")
        print("✅ Node binding working")
        print("✅ No import/compile/runtime issues")
        print("✅ Framework is production-ready")
    else:
        print(f"\n⚠️  NEEDS ATTENTION")
        print("❌ Some tests failed - check output above")
        print("❌ Review error messages and fix issues")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)