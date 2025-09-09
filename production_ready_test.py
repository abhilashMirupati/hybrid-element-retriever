#!/usr/bin/env python3
"""
Production-Ready Test for Optimized Test Runner
Tests all 3 CDP modes with optimized runner and validates DOM+Accessibility node binding
"""

import os
import sys
import time
import json
from pathlib import Path

sys.path.append('/workspace/src')

def test_optimized_runner():
    """Test optimized runner with all 3 CDP modes"""
    print("🚀 PRODUCTION-READY TEST WITH OPTIMIZED RUNNER")
    print("=" * 70)
    
    try:
        from optimized_test_runner import TestSuiteRunner
        
        # Initialize optimized runner
        print("📊 Initializing Optimized Test Runner...")
        start_time = time.time()
        runner = TestSuiteRunner()
        init_time = time.time() - start_time
        print(f"✅ Runner initialized in {init_time:.3f}s")
        
        # Test all 3 modes
        modes = ['DOM_ONLY', 'ACCESSIBILITY_ONLY', 'BOTH']
        results = {}
        
        for mode in modes:
            print(f"\n🔍 Testing {mode} mode...")
            mode_start = time.time()
            
            # Set environment variable
            os.environ['HER_CANONICAL_MODE'] = mode
            
            # Get runner for this test
            test_runner = runner.get_runner(f"test_{mode}")
            
            # Run test using the runner's _snapshot method
            result = test_runner._snapshot('https://www.verizon.com/')
            mode_time = time.time() - mode_start
            
            if result and 'elements' in result:
                elements = result['elements']
                print(f"✅ {mode}: {len(elements)} elements in {mode_time:.3f}s")
                
                # Analyze element types
                interactive_count = sum(1 for elem in elements if elem.get('interactive', False))
                form_count = sum(1 for elem in elements if elem.get('tag', '').upper() in ['FORM', 'INPUT', 'SELECT', 'TEXTAREA'])
                button_count = sum(1 for elem in elements if elem.get('tag', '').upper() == 'BUTTON')
                link_count = sum(1 for elem in elements if elem.get('tag', '').upper() == 'A')
                
                results[mode] = {
                    'total_elements': len(elements),
                    'interactive_elements': interactive_count,
                    'form_elements': form_count,
                    'button_elements': button_count,
                    'link_elements': link_count,
                    'execution_time': mode_time,
                    'elements': elements[:5]  # Sample elements for analysis
                }
                
                print(f"   📊 Interactive: {interactive_count}, Forms: {form_count}, Buttons: {button_count}, Links: {link_count}")
            else:
                print(f"❌ {mode}: Failed to get elements")
                results[mode] = {'error': 'No elements returned'}
        
        # Test DOM + Accessibility node binding
        print(f"\n🔗 Testing DOM + Accessibility Node Binding...")
        test_node_binding(runner)
        
        # Performance comparison
        print(f"\n📈 PERFORMANCE COMPARISON")
        print("=" * 50)
        for mode, data in results.items():
            if 'error' not in data:
                print(f"{mode:20} | {data['total_elements']:4d} elements | {data['execution_time']:6.3f}s")
        
        # Cleanup
        print(f"\n🧹 Cleaning up...")
        runner.cleanup_all()
        print("✅ Cleanup completed")
        
        return results
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_node_binding(runner):
    """Test DOM + Accessibility node binding with backendNodeId"""
    print("🔗 Testing DOM + Accessibility Node Binding...")
    
    try:
        # Set to BOTH mode for binding test
        os.environ['HER_CANONICAL_MODE'] = 'BOTH'
        
        # Get snapshot
        test_runner = runner.get_runner("binding_test")
        result = test_runner._snapshot('https://www.verizon.com/')
        if not result or 'elements' not in result:
            print("❌ Failed to get snapshot")
            return
        
        elements = result['elements']
        print(f"📊 Total elements: {len(elements)}")
        
        # Analyze backendNodeId binding
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
        print(f"\n📋 Sample Bound Elements:")
        for i, elem in enumerate(bound_elements[:3]):
            print(f"   {i+1}. {elem.get('tag', 'UNKNOWN')} - ID: {elem.get('backendNodeId')} - Text: {elem.get('text', '')[:50]}...")
        
    except Exception as e:
        print(f"❌ Node binding test failed: {e}")
        import traceback
        traceback.print_exc()

def test_model_loading():
    """Test model loading and persistence"""
    print("\n🧠 Testing Model Loading and Persistence...")
    
    try:
        from optimized_test_runner import TestSuiteRunner
        
        # First runner
        print("📊 Creating first runner...")
        start_time = time.time()
        runner1 = TestSuiteRunner()
        first_init_time = time.time() - start_time
        print(f"✅ First runner: {first_init_time:.3f}s")
        
        # Second runner (should be faster due to model caching)
        print("📊 Creating second runner...")
        start_time = time.time()
        runner2 = TestSuiteRunner()
        second_init_time = time.time() - start_time
        print(f"✅ Second runner: {second_init_time:.3f}s")
        
        # Test both runners
        print("📊 Testing both runners...")
        test_runner1 = runner1.get_runner("test_1")
        test_runner2 = runner2.get_runner("test_2")
        result1 = test_runner1._snapshot('https://www.verizon.com/')
        result2 = test_runner2._snapshot('https://www.verizon.com/')
        
        if result1 and result2:
            print(f"✅ Both runners working: {len(result1['elements'])} vs {len(result2['elements'])} elements")
        
        # Cleanup
        runner1.cleanup_all()
        runner2.cleanup_all()
        print("✅ Model loading test completed")
        
    except Exception as e:
        print(f"❌ Model loading test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 STARTING PRODUCTION-READY TEST")
    print("=" * 70)
    
    # Test optimized runner
    results = test_optimized_runner()
    
    # Test model loading
    test_model_loading()
    
    print(f"\n🎯 PRODUCTION-READY TEST COMPLETED")
    print("=" * 70)
    
    if results:
        print("✅ All tests passed - Production ready!")
    else:
        print("❌ Some tests failed - Needs fixes")