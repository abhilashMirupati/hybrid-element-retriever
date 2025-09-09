#!/usr/bin/env python3
"""
Comprehensive Fixed Test
Test all CDP modes with proper snapshot data access
"""

import os
import time
from her.runner import Runner
from her.config import CanonicalMode

def test_mode_with_snapshot(mode, mode_name):
    """Test a specific mode with proper snapshot data access"""
    
    print(f"\n🔬 TESTING: {mode_name}")
    print("=" * 60)
    
    # Set environment variable
    os.environ['HER_CANONICAL_MODE'] = mode.value
    
    start_time = time.time()
    
    try:
        # Create runner and get snapshot directly
        runner = Runner(headless=True)
        snapshot = runner._snapshot('https://www.google.com/')
        
        duration = time.time() - start_time
        
        print(f"✅ {mode_name} completed in {duration:.2f}s")
        
        # Analyze snapshot data
        if isinstance(snapshot, dict):
            print(f"📊 Snapshot keys: {list(snapshot.keys())}")
            
            if 'elements' in snapshot:
                elements = snapshot['elements']
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
                    if hasattr(elem, 'tag') and elem.tag:
                        print(f"   {i+1}. {elem.tag}: {getattr(elem, 'text', '')[:50]}...")
                    elif hasattr(elem, 'ax_role') and elem.ax_role:
                        print(f"   {i+1}. {elem.ax_role}: {getattr(elem, 'ax_name', '')[:50]}...")
                    else:
                        print(f"   {i+1}. Unknown element: {elem}")
            else:
                print("❌ No elements found in snapshot")
        else:
            print(f"❌ Snapshot is not a dictionary: {type(snapshot)}")
            
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ {mode_name} failed after {duration:.2f}s: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Test all CDP modes with proper snapshot data access"""
    
    print("🔬 COMPREHENSIVE FIXED CDP TEST")
    print("=" * 60)
    
    modes = [
        (CanonicalMode.DOM_ONLY, "DOM Only"),
        (CanonicalMode.ACCESSIBILITY_ONLY, "Accessibility Only"),
        (CanonicalMode.BOTH, "Both DOM + Accessibility")
    ]
    
    results = {}
    
    for mode, mode_name in modes:
        test_mode_with_snapshot(mode, mode_name)
    
    print(f"\n🎯 SUMMARY")
    print("=" * 60)
    print("All modes tested with proper snapshot data access")
    print("Check the output above for detailed results")

if __name__ == "__main__":
    main()