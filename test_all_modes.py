#!/usr/bin/env python3
"""
Comprehensive test script for all 3 canonical modes:
- DOM_ONLY
- ACCESSIBILITY_ONLY  
- BOTH

This script will run the Verizon flow test for each mode and analyze the results.
"""

import os
import subprocess
import time
import json
from datetime import datetime

def run_test_with_mode(mode, test_name="test_verizon_flow.py"):
    """Run the test with a specific canonical mode"""
    print(f"\n{'='*60}")
    print(f"🧪 TESTING MODE: {mode}")
    print(f"{'='*60}")
    
    # Set environment variables
    env = os.environ.copy()
    env['HER_CANONICAL_MODE'] = mode
    env['HER_E2E'] = '1'
    
    start_time = time.time()
    
    try:
        # Run the test
        result = subprocess.run([
            'python', '-m', 'pytest', f'tests/{test_name}', '-v', '-s', '--tb=short'
        ], env=env, capture_output=True, text=True, timeout=600)  # 10 minute timeout
        
        end_time = time.time()
        duration = end_time - start_time
        
        return {
            'mode': mode,
            'success': result.returncode == 0,
            'duration': duration,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }
        
    except subprocess.TimeoutExpired:
        return {
            'mode': mode,
            'success': False,
            'duration': 600,
            'stdout': '',
            'stderr': 'Test timed out after 10 minutes',
            'returncode': -1
        }
    except Exception as e:
        return {
            'mode': mode,
            'success': False,
            'duration': 0,
            'stdout': '',
            'stderr': str(e),
            'returncode': -1
        }

def analyze_test_results(results):
    """Analyze and compare test results across modes"""
    print(f"\n{'='*80}")
    print("📊 COMPREHENSIVE ANALYSIS")
    print(f"{'='*80}")
    
    # Summary table
    print(f"\n{'Mode':<20} {'Status':<10} {'Duration':<12} {'Notes'}")
    print("-" * 80)
    
    for result in results:
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        duration = f"{result['duration']:.1f}s"
        
        # Analyze specific issues
        notes = []
        if not result['success']:
            if "text_node_click" in result['stderr']:
                notes.append("Text node selection issue")
            if "Could not click element" in result['stderr']:
                notes.append("Click failure")
            if "timeout" in result['stderr'].lower():
                notes.append("Timeout")
            if "AssertionError" in result['stderr']:
                notes.append("Assertion failed")
        
        if result['duration'] > 300:  # 5 minutes
            notes.append("Slow performance")
        
        notes_str = ", ".join(notes) if notes else "No issues"
        print(f"{result['mode']:<20} {status:<10} {duration:<12} {notes_str}")
    
    # Performance comparison
    print(f"\n📈 PERFORMANCE COMPARISON:")
    fastest = min(results, key=lambda x: x['duration'])
    slowest = max(results, key=lambda x: x['duration'])
    
    print(f"   Fastest: {fastest['mode']} ({fastest['duration']:.1f}s)")
    print(f"   Slowest: {slowest['mode']} ({slowest['duration']:.1f}s)")
    
    if fastest['duration'] > 0:
        speedup = slowest['duration'] / fastest['duration']
        print(f"   Speed difference: {speedup:.1f}x")
    
    # Success rate
    success_count = sum(1 for r in results if r['success'])
    print(f"\n🎯 SUCCESS RATE: {success_count}/{len(results)} modes passed")
    
    # Detailed analysis for each mode
    print(f"\n🔍 DETAILED ANALYSIS:")
    for result in results:
        print(f"\n--- {result['mode']} ---")
        if result['success']:
            print("✅ Test passed successfully")
        else:
            print("❌ Test failed")
            print(f"   Duration: {result['duration']:.1f}s")
            
            # Extract key error information
            stderr_lines = result['stderr'].split('\n')
            error_lines = [line for line in stderr_lines if 'FAILED' in line or 'ERROR' in line or 'AssertionError' in line]
            
            if error_lines:
                print("   Key errors:")
                for line in error_lines[:3]:  # Show first 3 errors
                    print(f"     {line.strip()}")
    
    return results

def main():
    """Main test execution"""
    print("🚀 Starting comprehensive canonical mode testing")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test all 3 modes
    modes = ['DOM_ONLY', 'ACCESSIBILITY_ONLY', 'BOTH']
    results = []
    
    for mode in modes:
        result = run_test_with_mode(mode)
        results.append(result)
        
        # Brief pause between tests
        time.sleep(2)
    
    # Analyze results
    analyze_test_results(results)
    
    # Save detailed results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_file = f'/workspace/test_results_{timestamp}.json'
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: {results_file}")
    print(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()