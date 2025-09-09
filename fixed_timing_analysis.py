#!/usr/bin/env python3
"""
Fixed Timing Analysis with Detailed Logging
Now that canonical mode bug is fixed, analyze real differences between modes
"""

import os
import time
import logging
from datetime import datetime
from her.runner import run_steps
from her.config import CanonicalMode

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/workspace/fixed_timing_analysis.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def test_mode_with_detailed_timing(mode, mode_name):
    """Test a specific mode with detailed timing and data analysis"""
    
    print(f"\n🔬 TESTING: {mode_name}")
    print("=" * 60)
    
    # Set environment variable
    os.environ['HER_CANONICAL_MODE'] = mode.value
    
    start_time = time.time()
    
    try:
        # Run the test
        result = run_steps(['Open https://www.google.com/'], headless=True)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ {mode_name} completed in {duration:.2f}s")
        
        # Analyze the result
        if result and hasattr(result, 'elements'):
            elements = result.elements
            print(f"📊 Elements extracted: {len(elements)}")
            
            # Analyze element types
            dom_elements = sum(1 for e in elements if hasattr(e, 'tag') and e.tag)
            ax_elements = sum(1 for e in elements if hasattr(e, 'ax_role') and e.ax_role)
            interactive_elements = sum(1 for e in elements if hasattr(e, 'ax_role') and e.ax_role in ['button', 'textbox', 'link', 'checkbox', 'radio', 'combobox'])
            
            print(f"   DOM elements: {dom_elements}")
            print(f"   Accessibility elements: {ax_elements}")
            print(f"   Interactive elements: {interactive_elements}")
            
            # Sample some elements
            print(f"\n📋 Sample elements:")
            for i, elem in enumerate(elements[:5]):
                tag = getattr(elem, 'tag', 'N/A')
                ax_role = getattr(elem, 'ax_role', 'N/A')
                text = getattr(elem, 'text', 'N/A')[:50] if hasattr(elem, 'text') else 'N/A'
                print(f"   {i+1}. tag='{tag}', ax_role='{ax_role}', text='{text}'")
        
        return duration, len(elements) if result and hasattr(result, 'elements') else 0
        
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        print(f"❌ {mode_name} failed after {duration:.2f}s: {e}")
        logger.error(f"{mode_name} failed: {e}")
        return duration, 0

def main():
    """Main analysis function"""
    
    print("🔬 FIXED TIMING ANALYSIS - REAL MODE DIFFERENCES")
    print("=" * 80)
    
    # Test all three modes
    modes = [
        (CanonicalMode.DOM_ONLY, "DOM Only"),
        (CanonicalMode.ACCESSIBILITY_ONLY, "Accessibility Only"),
        (CanonicalMode.BOTH, "Both DOM + Accessibility")
    ]
    
    results = {}
    
    for mode, mode_name in modes:
        duration, element_count = test_mode_with_detailed_timing(mode, mode_name)
        results[mode_name] = {
            'duration': duration,
            'element_count': element_count
        }
    
    # Summary analysis
    print(f"\n📊 SUMMARY ANALYSIS")
    print("=" * 60)
    
    for mode_name, data in results.items():
        print(f"{mode_name:20}: {data['duration']:6.2f}s, {data['element_count']:4d} elements")
    
    # Find fastest and slowest
    fastest = min(results.items(), key=lambda x: x[1]['duration'])
    slowest = max(results.items(), key=lambda x: x[1]['duration'])
    
    print(f"\n🏆 Fastest: {fastest[0]} ({fastest[1]['duration']:.2f}s)")
    print(f"🐌 Slowest: {slowest[0]} ({slowest[1]['duration']:.2f}s)")
    
    # Analyze element counts
    print(f"\n📈 ELEMENT COUNT ANALYSIS")
    print("-" * 40)
    
    dom_count = results['DOM Only']['element_count']
    ax_count = results['Accessibility Only']['element_count']
    both_count = results['Both DOM + Accessibility']['element_count']
    
    print(f"DOM Only:           {dom_count:4d} elements")
    print(f"Accessibility Only: {ax_count:4d} elements")
    print(f"Both:               {both_count:4d} elements")
    
    if both_count > max(dom_count, ax_count):
        print(f"✅ Both mode has more elements ({both_count}) than individual modes")
    else:
        print(f"⚠️  Both mode doesn't have more elements than expected")
    
    # Performance analysis
    print(f"\n⚡ PERFORMANCE ANALYSIS")
    print("-" * 40)
    
    dom_time = results['DOM Only']['duration']
    ax_time = results['Accessibility Only']['duration']
    both_time = results['Both DOM + Accessibility']['duration']
    
    print(f"DOM Only:           {dom_time:6.2f}s")
    print(f"Accessibility Only: {ax_time:6.2f}s")
    print(f"Both:               {both_time:6.2f}s")
    
    if both_time < min(dom_time, ax_time):
        print(f"✅ Both mode is fastest - this makes sense!")
    else:
        print(f"⚠️  Both mode is not fastest - this needs investigation")
    
    # Expected vs actual
    expected_both_time = max(dom_time, ax_time)  # Should be similar to slower individual mode
    actual_both_time = both_time
    difference = actual_both_time - expected_both_time
    
    print(f"\nExpected Both time: {expected_both_time:.2f}s")
    print(f"Actual Both time:   {actual_both_time:.2f}s")
    print(f"Difference:         {difference:+.2f}s")
    
    if abs(difference) < 5:  # Within 5 seconds
        print(f"✅ Both mode timing is as expected")
    else:
        print(f"⚠️  Both mode timing is unexpected (difference: {difference:+.2f}s)")

if __name__ == "__main__":
    main()