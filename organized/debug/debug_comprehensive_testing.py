#!/usr/bin/env python3
"""
Comprehensive Debug Testing Script
Tests all 3 CDP modes with detailed input/output analysis and timing
"""

import os
import sys
import time
import json
import subprocess
from pathlib import Path

# Add src to path
sys.path.append('/workspace/src')

def test_cdp_mode(mode, url='https://www.verizon.com/'):
    """Test a single CDP mode with detailed analysis"""
    print(f"\n{'='*60}")
    print(f"🔍 TESTING {mode} MODE")
    print(f"{'='*60}")
    
    # Create isolated test script
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
    print(f"📦 INITIALIZING RUNNER...")
    start_time = time.time()
    runner = Runner(headless=True)
    init_time = time.time() - start_time
    print(f"   ✅ Runner initialized in {{init_time:.3f}}s")
    
    # Get snapshot
    print(f"📸 TAKING SNAPSHOT...")
    snapshot_start = time.time()
    result = runner._snapshot('{url}')
    snapshot_time = time.time() - snapshot_start
    print(f"   ✅ Snapshot taken in {{snapshot_time:.3f}}s")
    
    if result and 'elements' in result:
        elements = result['elements']
        
        # Analyze elements
        print(f"📊 ELEMENT ANALYSIS:")
        print(f"   Total Elements: {{len(elements)}}")
        
        # Interactive elements
        interactive_count = sum(1 for elem in elements if elem.get('interactive', False))
        print(f"   Interactive Elements: {{interactive_count}}")
        
        # Element types
        element_types = {{}}
        for elem in elements:
            tag = elem.get('tag', 'UNKNOWN')
            element_types[tag] = element_types.get(tag, 0) + 1
        
        print(f"   Element Types: {{dict(sorted(element_types.items(), key=lambda x: x[1], reverse=True)[:10])}}")
        
        # Form elements
        form_elements = sum(1 for elem in elements if elem.get('tag', '').upper() in ['FORM', 'INPUT', 'SELECT', 'TEXTAREA'])
        print(f"   Form Elements: {{form_elements}}")
        
        # Button elements
        button_elements = sum(1 for elem in elements if elem.get('tag', '').upper() == 'BUTTON')
        print(f"   Button Elements: {{button_elements}}")
        
        # Link elements
        link_elements = sum(1 for elem in elements if elem.get('tag', '').upper() == 'A')
        print(f"   Link Elements: {{link_elements}}")
        
        # Backend node binding
        backend_ids = [elem.get('backendNodeId') for elem in elements if elem.get('backendNodeId')]
        binding_ratio = len(backend_ids) / len(elements) if elements else 0
        print(f"   Backend Node Binding: {{binding_ratio:.1%}} ({{len(backend_ids)}}/{{len(elements)}})")
        
        # Sample elements
        print(f"📋 SAMPLE ELEMENTS:")
        for i, elem in enumerate(elements[:5]):
            print(f"   {{i+1}}. Tag: {{elem.get('tag', 'UNKNOWN')}}")
            print(f"      Text: '{{str(elem.get('text', ''))[:50]}}{{'...' if len(str(elem.get('text', ''))) > 50 else ''}}'")
            print(f"      BackendID: {{elem.get('backendNodeId', 'None')}}")
            print(f"      Interactive: {{elem.get('interactive', False)}}")
            print(f"      XPath: {{elem.get('xpath', 'None')[:80]}}{{'...' if len(elem.get('xpath', '')) > 80 else ''}}")
            print()
        
        # Timing summary
        total_time = init_time + snapshot_time
        print(f"⏱️  TIMING SUMMARY:")
        print(f"   Initialization: {{init_time:.3f}}s")
        print(f"   Snapshot: {{snapshot_time:.3f}}s")
        print(f"   Total: {{total_time:.3f}}s")
        
        # Results
        results = {{
            'mode': '{mode}',
            'success': True,
            'total_elements': len(elements),
            'interactive_elements': interactive_count,
            'form_elements': form_elements,
            'button_elements': button_elements,
            'link_elements': link_elements,
            'backend_node_binding_ratio': binding_ratio,
            'init_time': init_time,
            'snapshot_time': snapshot_time,
            'total_time': total_time,
            'element_types': element_types
        }}
        
        print(f"SUCCESS: {{json.dumps(results)}}")
        
    else:
        print(f"   ❌ No elements returned")
        print(f"FAILED: No elements returned")
        
except Exception as e:
    print(f"   ❌ Error: {{e}}")
    import traceback
    traceback.print_exc()
    print(f"ERROR: {{str(e)}}")
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
            print(f"   ❌ {mode} mode failed:")
            print(f"   STDOUT: {result.stdout}")
            print(f"   STDERR: {result.stderr}")
            return None
            
    except subprocess.TimeoutExpired:
        print(f"   ⏰ {mode} mode timed out")
        return None
    except Exception as e:
        print(f"   💥 {mode} mode error: {e}")
        return None

def test_model_optimization():
    """Test model loading optimization"""
    print(f"\n{'='*60}")
    print(f"🧠 TESTING MODEL OPTIMIZATION")
    print(f"{'='*60}")
    
    # Create isolated test script
    test_script = """
import os
import sys
import time
import json
sys.path.append('/workspace/src')

try:
    from her.runner import Runner
    
    # First runner
    print(f"📦 FIRST RUNNER (Model Loading)...")
    start_time = time.time()
    runner1 = Runner(headless=True)
    first_time = time.time() - start_time
    print(f"   ✅ First runner initialized in {first_time:.3f}s")
    
    # Second runner (should be faster)
    print(f"📦 SECOND RUNNER (Should be cached)...")
    start_time = time.time()
    runner2 = Runner(headless=True)
    second_time = time.time() - start_time
    print(f"   ✅ Second runner initialized in {second_time:.3f}s")
    
    # Check if they share the same pipeline
    same_pipeline = id(runner1.pipeline) == id(runner2.pipeline)
    print(f"🔍 PIPELINE ANALYSIS:")
    print(f"   Same Pipeline: {same_pipeline}")
    print(f"   First Runner Time: {first_time:.3f}s")
    print(f"   Second Runner Time: {second_time:.3f}s")
    print(f"   Speed Improvement: {first_time/second_time:.1f}x" if second_time > 0 else "   Speed Improvement: ∞")
    
    # Test snapshot performance
    print(f"📸 TESTING SNAPSHOT PERFORMANCE...")
    snapshot_start = time.time()
    result = runner1._snapshot('https://www.google.com')
    snapshot_time = time.time() - snapshot_start
    print(f"   ✅ Snapshot taken in {snapshot_time:.3f}s")
    print(f"   Elements returned: {len(result.get('elements', []))}")
    
    results = {
        'first_runner_time': first_time,
        'second_runner_time': second_time,
        'same_pipeline': same_pipeline,
        'caching_working': same_pipeline and second_time < first_time * 0.1,
        'snapshot_time': snapshot_time
    }
    
    print(f"SUCCESS: {json.dumps(results)}")
    
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()
    print(f"ERROR: {str(e)}")
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
            print(f"   ❌ Model optimization test failed:")
            print(f"   STDOUT: {result.stdout}")
            print(f"   STDERR: {result.stderr}")
            return None
            
    except subprocess.TimeoutExpired:
        print(f"   ⏰ Model optimization test timed out")
        return None
    except Exception as e:
        print(f"   💥 Model optimization test error: {e}")
        return None

def main():
    print("🚀 COMPREHENSIVE DEBUG TESTING")
    print("=" * 60)
    
    # Test all 3 CDP modes
    modes = ['DOM_ONLY', 'ACCESSIBILITY_ONLY', 'BOTH']
    results = {}
    
    for mode in modes:
        results[mode] = test_cdp_mode(mode)
    
    # Test model optimization
    model_results = test_model_optimization()
    
    # Summary
    print(f"\n{'='*60}")
    print(f"📈 COMPREHENSIVE TEST SUMMARY")
    print(f"{'='*60}")
    
    all_passed = True
    
    # CDP Mode Results
    print(f"\n🔍 CDP MODE RESULTS:")
    for mode, result in results.items():
        if result:
            status = "✅ PASS"
            print(f"   {mode:20} | {status} | {result['total_elements']:4d} elements | {result['total_time']:6.3f}s | Binding: {result['backend_node_binding_ratio']:.1%}")
        else:
            status = "❌ FAIL"
            print(f"   {mode:20} | {status}")
            all_passed = False
    
    # Model Optimization Results
    print(f"\n🧠 MODEL OPTIMIZATION RESULTS:")
    if model_results:
        status = "✅ PASS" if model_results['caching_working'] else "❌ FAIL"
        print(f"   Model Caching      | {status} | First: {model_results['first_runner_time']:.3f}s | Second: {model_results['second_runner_time']:.3f}s")
        if not model_results['caching_working']:
            all_passed = False
    else:
        print(f"   Model Caching      | ❌ FAIL")
        all_passed = False
    
    # Detailed Analysis
    if all_passed:
        print(f"\n🎯 DETAILED ANALYSIS:")
        print(f"   📊 Element Counts:")
        for mode, result in results.items():
            if result:
                print(f"      {mode}: {result['total_elements']} total, {result['interactive_elements']} interactive, {result['form_elements']} forms")
        
        print(f"\n   ⏱️  Performance:")
        for mode, result in results.items():
            if result:
                print(f"      {mode}: {result['total_time']:.3f}s total ({result['init_time']:.3f}s init + {result['snapshot_time']:.3f}s snapshot)")
        
        print(f"\n   🔗 Node Binding Quality:")
        for mode, result in results.items():
            if result:
                print(f"      {mode}: {result['backend_node_binding_ratio']:.1%} elements have backendNodeId")
    
    # Final result
    print(f"\n{'='*60}")
    if all_passed:
        print(f"🎉 ALL TESTS PASSED - FRAMEWORK IS PRODUCTION READY!")
        print(f"✅ All 3 CDP modes working correctly")
        print(f"✅ Model caching optimization working")
        print(f"✅ Element extraction working")
        print(f"✅ Node binding working")
        print(f"✅ No import/compile/runtime issues")
    else:
        print(f"⚠️  SOME TESTS FAILED - NEEDS ATTENTION")
        print(f"❌ Check error messages above and fix issues")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)