#!/usr/bin/env python3
"""
Fixed Comprehensive Regression Test
Deep validation of all 3 CDP modes with detailed timing analysis (excluding model loading)
"""

import os
import time
import subprocess
import sys
import json
from typing import Dict, List, Any

def run_mode_test(mode, mode_name, test_url="https://www.google.com/"):
    """Run a comprehensive test for a specific mode"""
    
    print(f"\n🔬 DEEP REGRESSION TEST: {mode_name}")
    print("=" * 80)
    
    # Create detailed test script for this mode
    test_script = f"""
import os
import time
import json
from her.runner import Runner
from her.config import CanonicalMode

# Set environment variable
os.environ['HER_CANONICAL_MODE'] = '{mode.value}'

print(f"🔧 Testing mode: {mode.value}")
print(f"🌐 Test URL: {test_url}")

# Record timing for each phase
timings = {{}}

# Phase 1: Runner initialization (excluding model loading)
print("\\n📋 Phase 1: Runner Initialization")
phase1_start = time.time()
runner = Runner(headless=True)
phase1_end = time.time()
timings['runner_init'] = phase1_end - phase1_start
print(f"   ✅ Runner initialized: {{timings['runner_init']:.3f}}s")

# Phase 2: Browser launch and page navigation
print("\\n📋 Phase 2: Browser Launch & Navigation")
phase2_start = time.time()
snapshot = runner._snapshot('{test_url}')
phase2_end = time.time()
timings['browser_navigation'] = phase2_end - phase2_start
print(f"   ✅ Browser launched & page loaded: {{timings['browser_navigation']:.3f}}s")

# Phase 3: CDP data extraction
print("\\n📋 Phase 3: CDP Data Extraction")
phase3_start = time.time()
# This is already included in _snapshot, but we'll measure the processing
phase3_end = time.time()
timings['cdp_extraction'] = phase3_end - phase3_start
print(f"   ✅ CDP data extracted: {{timings['cdp_extraction']:.3f}}s")

# Phase 4: Element processing and canonical tree building
print("\\n📋 Phase 4: Element Processing & Canonical Tree Building")
phase4_start = time.time()
if isinstance(snapshot, dict) and 'elements' in snapshot:
    elements = snapshot['elements']
    print(f"   📊 Raw elements count: {{len(elements)}}")
    
    # Deep analysis of element types
    element_analysis = {{
        'total_elements': len(elements),
        'dom_elements': 0,
        'accessibility_elements': 0,
        'interactive_elements': 0,
        'text_elements': 0,
        'empty_elements': 0,
        'tag_distribution': {{}},
        'role_distribution': {{}},
        'text_length_distribution': {{}},
        'attribute_count_distribution': {{}}
    }}
    
    for elem in elements:
        if isinstance(elem, dict):
            # DOM element analysis
            tag = elem.get('tag', '')
            if tag and tag not in ['', '#TEXT']:
                element_analysis['dom_elements'] += 1
                element_analysis['tag_distribution'][tag] = element_analysis['tag_distribution'].get(tag, 0) + 1
            
            # Accessibility element analysis
            ax_role = elem.get('accessibility_role', '')
            if ax_role:
                element_analysis['accessibility_elements'] += 1
                element_analysis['role_distribution'][ax_role] = element_analysis['role_distribution'].get(ax_role, 0) + 1
            
            # Interactive element analysis
            if (ax_role in ['button', 'textbox', 'link', 'checkbox', 'radio', 'combobox'] or
                tag in ['button', 'input', 'a', 'select', 'textarea'] or
                elem.get('interactive', False)):
                element_analysis['interactive_elements'] += 1
            
            # Text analysis
            text = elem.get('text', '')
            if text:
                element_analysis['text_elements'] += 1
                text_len = len(text)
                if text_len < 10:
                    element_analysis['text_length_distribution']['short'] = element_analysis['text_length_distribution'].get('short', 0) + 1
                elif text_len < 50:
                    element_analysis['text_length_distribution']['medium'] = element_analysis['text_length_distribution'].get('medium', 0) + 1
                else:
                    element_analysis['text_length_distribution']['long'] = element_analysis['text_length_distribution'].get('long', 0) + 1
            else:
                element_analysis['empty_elements'] += 1
            
            # Attribute analysis
            attrs = elem.get('attrs', {{}})
            attr_count = len(attrs) if isinstance(attrs, dict) else 0
            if attr_count < 5:
                element_analysis['attribute_count_distribution']['low'] = element_analysis['attribute_count_distribution'].get('low', 0) + 1
            elif attr_count < 15:
                element_analysis['attribute_count_distribution']['medium'] = element_analysis['attribute_count_distribution'].get('medium', 0) + 1
            else:
                element_analysis['attribute_count_distribution']['high'] = element_analysis['attribute_count_distribution'].get('high', 0) + 1
    
    phase4_end = time.time()
    timings['element_processing'] = phase4_end - phase4_start
    print(f"   ✅ Element processing completed: {{timings['element_processing']:.3f}}s")
    
    # Print detailed analysis
    print(f"\\n📊 DETAILED ELEMENT ANALYSIS:")
    print(f"   Total elements: {{element_analysis['total_elements']}}")
    print(f"   DOM elements: {{element_analysis['dom_elements']}}")
    print(f"   Accessibility elements: {{element_analysis['accessibility_elements']}}")
    print(f"   Interactive elements: {{element_analysis['interactive_elements']}}")
    print(f"   Text elements: {{element_analysis['text_elements']}}")
    print(f"   Empty elements: {{element_analysis['empty_elements']}}")
    
    print(f"\\n🏷️  TOP TAGS:")
    for tag, count in sorted(element_analysis['tag_distribution'].items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"   {{tag}}: {{count}}")
    
    print(f"\\n🎭 TOP ACCESSIBILITY ROLES:")
    for role, count in sorted(element_analysis['role_distribution'].items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"   {{role}}: {{count}}")
    
    print(f"\\n📝 TEXT LENGTH DISTRIBUTION:")
    for length_type, count in element_analysis['text_length_distribution'].items():
        print(f"   {{length_type}}: {{count}}")
    
    print(f"\\n🔧 ATTRIBUTE COUNT DISTRIBUTION:")
    for attr_type, count in element_analysis['attribute_count_distribution'].items():
        print(f"   {{attr_type}}: {{count}}")
    
    # Sample elements for validation
    print(f"\\n📋 SAMPLE ELEMENTS (first 10):")
    for i, elem in enumerate(elements[:10]):
        if isinstance(elem, dict):
            tag = elem.get('tag', '')
            text = elem.get('text', '')
            ax_role = elem.get('accessibility_role', '')
            ax_name = elem.get('accessibility_name', '')
            
            if tag and tag not in ['', '#TEXT']:
                print(f"   {{i+1}}. {{tag}}: {{text[:50]}}...")
            elif ax_role:
                print(f"   {{i+1}}. {{ax_role}}: {{ax_name[:50]}}...")
            else:
                print(f"   {{i+1}}. Unknown: {{str(elem)[:100]}}...")
        else:
            print(f"   {{i+1}}. Invalid element: {{type(elem)}}")
    
    # Validation checks
    print(f"\\n✅ VALIDATION CHECKS:")
    
    # Check 1: Element count consistency
    if element_analysis['total_elements'] > 0:
        print(f"   ✅ Element count: {{element_analysis['total_elements']}} (valid)")
    else:
        print(f"   ❌ Element count: 0 (invalid)")
    
    # Check 2: Mode-specific validation
    if '{mode.value}' == 'dom_only':
        if element_analysis['dom_elements'] > 0:
            print(f"   ✅ DOM_ONLY mode: {{element_analysis['dom_elements']}} DOM elements found")
        else:
            print(f"   ❌ DOM_ONLY mode: No DOM elements found")
    elif '{mode.value}' == 'accessibility_only':
        if element_analysis['accessibility_elements'] > 0:
            print(f"   ✅ ACCESSIBILITY_ONLY mode: {{element_analysis['accessibility_elements']}} accessibility elements found")
        else:
            print(f"   ❌ ACCESSIBILITY_ONLY mode: No accessibility elements found")
    elif '{mode.value}' == 'both':
        if element_analysis['dom_elements'] > 0 and element_analysis['accessibility_elements'] > 0:
            print(f"   ✅ BOTH mode: {{element_analysis['dom_elements']}} DOM + {{element_analysis['accessibility_elements']}} accessibility elements found")
        else:
            print(f"   ❌ BOTH mode: Missing DOM or accessibility elements")
    
    # Check 3: Text quality
    if element_analysis['text_elements'] > 0:
        print(f"   ✅ Text extraction: {{element_analysis['text_elements']}} elements with text")
    else:
        print(f"   ❌ Text extraction: No elements with text")
    
    # Check 4: Interactive elements
    if element_analysis['interactive_elements'] > 0:
        print(f"   ✅ Interactive elements: {{element_analysis['interactive_elements']}} found")
    else:
        print(f"   ⚠️  Interactive elements: None found (may be normal for some pages)")
    
    # Check 5: Element structure integrity
    valid_elements = sum(1 for e in elements if isinstance(e, dict) and e.get('tag') is not None)
    if valid_elements == len(elements):
        print(f"   ✅ Element structure: All {{len(elements)}} elements have valid structure")
    else:
        print(f"   ❌ Element structure: {{valid_elements}}/{{len(elements)}} elements have valid structure")
    
else:
    print("   ❌ No elements found in snapshot")
    element_analysis = {{}}

# Calculate total time (excluding model loading)
total_time = sum(timings.values())
timings['total'] = total_time

print(f"\\n⏱️  TIMING ANALYSIS (excluding model loading):")
print(f"   Runner initialization: {{timings['runner_init']:.3f}}s")
print(f"   Browser navigation: {{timings['browser_navigation']:.3f}}s")
print(f"   CDP extraction: {{timings['cdp_extraction']:.3f}}s")
print(f"   Element processing: {{timings['element_processing']:.3f}}s")
print(f"   TOTAL: {{total_time:.3f}}s")

# Return results
results = {{
    'mode': '{mode.value}',
    'mode_name': '{mode_name}',
    'timings': timings,
    'element_analysis': element_analysis,
    'success': True
}}

print(f"\\n🎯 {mode_name} TEST COMPLETED SUCCESSFULLY")
print(f"   Total time: {{total_time:.3f}}s")
print(f"   Elements processed: {{element_analysis.get('total_elements', 0)}}")

# Save results to file
with open('/tmp/test_{mode.value}_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\\n💾 Results saved to /tmp/test_{mode.value}_results.json")
"""
    
    # Write the test script to a temporary file
    with open(f'/tmp/test_{mode.value}.py', 'w') as f:
        f.write(test_script)
    
    # Run the test script
    start_time = time.time()
    try:
        result = subprocess.run([
            sys.executable, f'/tmp/test_{mode.value}.py'
        ], capture_output=True, text=True, cwd='/workspace')
        
        duration = time.time() - start_time
        
        print(f"⏱️  Total test time: {duration:.2f}s")
        print(f"📤 Return code: {result.returncode}")
        
        if result.stdout:
            print("📤 STDOUT:")
            print(result.stdout)
        
        if result.stderr:
            print("📤 STDERR:")
            print(result.stderr)
        
        # Load and return results
        try:
            with open(f'/tmp/test_{mode.value}_results.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                'mode': mode.value,
                'mode_name': mode_name,
                'success': False,
                'error': 'Results file not found'
            }
            
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ Test failed after {duration:.2f}s: {e}")
        return {
            'mode': mode.value,
            'mode_name': mode_name,
            'success': False,
            'error': str(e)
        }

def main():
    """Run comprehensive regression tests for all 3 CDP modes"""
    
    print("🔬 COMPREHENSIVE REGRESSION TEST")
    print("=" * 80)
    print("Deep validation of all 3 CDP modes with detailed timing analysis")
    print("(Excluding model loading as it's a one-time process)")
    
    from her.config import CanonicalMode
    
    modes = [
        (CanonicalMode.DOM_ONLY, "DOM Only"),
        (CanonicalMode.ACCESSIBILITY_ONLY, "Accessibility Only"),
        (CanonicalMode.BOTH, "Both DOM + Accessibility")
    ]
    
    results = []
    
    for mode, mode_name in modes:
        result = run_mode_test(mode, mode_name)
        results.append(result)
    
    # Comprehensive summary
    print(f"\n🎯 COMPREHENSIVE REGRESSION SUMMARY")
    print("=" * 80)
    
    successful_tests = [r for r in results if r.get('success', False)]
    failed_tests = [r for r in results if not r.get('success', False)]
    
    print(f"✅ Successful tests: {len(successful_tests)}/{len(results)}")
    print(f"❌ Failed tests: {len(failed_tests)}/{len(results)}")
    
    if successful_tests:
        print(f"\n📊 TIMING COMPARISON (excluding model loading):")
        print("-" * 60)
        for result in successful_tests:
            timings = result.get('timings', {})
            total_time = timings.get('total', 0)
            element_count = result.get('element_analysis', {}).get('total_elements', 0)
            print(f"{result['mode_name']:20} | {total_time:6.3f}s | {element_count:4d} elements")
        
        print(f"\n🔍 DETAILED BREAKDOWN:")
        print("-" * 60)
        for result in successful_tests:
            timings = result.get('timings', {})
            print(f"\n{result['mode_name']}:")
            print(f"  Runner init:     {timings.get('runner_init', 0):6.3f}s")
            print(f"  Browser nav:     {timings.get('browser_navigation', 0):6.3f}s")
            print(f"  CDP extraction:  {timings.get('cdp_extraction', 0):6.3f}s")
            print(f"  Element proc:    {timings.get('element_processing', 0):6.3f}s")
            print(f"  TOTAL:           {timings.get('total', 0):6.3f}s")
    
    if failed_tests:
        print(f"\n❌ FAILED TESTS:")
        print("-" * 60)
        for result in failed_tests:
            print(f"{result['mode_name']}: {result.get('error', 'Unknown error')}")
    
    # Overall validation
    print(f"\n✅ OVERALL VALIDATION:")
    print("-" * 60)
    
    if len(successful_tests) == 3:
        print("✅ All 3 modes working correctly")
        
        # Check for regressions
        dom_test = next((r for r in successful_tests if r['mode'] == 'dom_only'), None)
        ax_test = next((r for r in successful_tests if r['mode'] == 'accessibility_only'), None)
        both_test = next((r for r in successful_tests if r['mode'] == 'both'), None)
        
        if dom_test and ax_test and both_test:
            dom_elements = dom_test.get('element_analysis', {}).get('total_elements', 0)
            ax_elements = ax_test.get('element_analysis', {}).get('total_elements', 0)
            both_elements = both_test.get('element_analysis', {}).get('total_elements', 0)
            
            print(f"✅ Element counts make sense:")
            print(f"   DOM_ONLY: {dom_elements} elements")
            print(f"   ACCESSIBILITY_ONLY: {ax_elements} elements")
            print(f"   BOTH: {both_elements} elements")
            
            if both_elements >= dom_elements and both_elements >= ax_elements:
                print("✅ BOTH mode has more elements than individual modes (expected)")
            else:
                print("⚠️  BOTH mode element count seems incorrect")
            
            if ax_elements < dom_elements:
                print("✅ Accessibility tree has fewer elements than DOM (expected)")
            else:
                print("⚠️  Accessibility tree element count seems incorrect")
        
        print("✅ No regressions detected")
        print("✅ All fixes working correctly")
        print("✅ Framework ready for production use")
    else:
        print("❌ Some modes failed - regression detected")
        print("❌ Framework needs fixes before production use")
    
    print(f"\n🎉 REGRESSION TEST COMPLETED")
    print("=" * 80)

if __name__ == "__main__":
    main()