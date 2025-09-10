#!/usr/bin/env python3
"""
Focused Attribute Analysis
Tests DOM/accessibility extraction and canonical descriptor making for all 3 modes
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def test_focused_attribute_analysis():
    """Test focused attribute capture for all 3 CDP modes"""
    
    print("🔍 FOCUSED ATTRIBUTE ANALYSIS")
    print("=" * 80)
    
    # Test script for focused analysis
    test_script = """
import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))
os.environ["HER_MODELS_DIR"] = str(Path.cwd() / "src" / "her" / "models")
os.environ["HER_CACHE_DIR"] = str(Path.cwd() / ".her_cache")

from her.runner import Runner
from her.config import CanonicalMode

def analyze_attributes():
    try:
        # Test all 3 modes
        modes = [
            (CanonicalMode.DOM_ONLY, "DOM_ONLY"),
            (CanonicalMode.ACCESSIBILITY_ONLY, "ACCESSIBILITY_ONLY"), 
            (CanonicalMode.BOTH, "BOTH")
        ]
        
        results = {}
        
        for mode, mode_name in modes:
            print(f"\\n{'='*60}")
            print(f"🔍 TESTING {mode_name} MODE")
            print(f"{'='*60}")
            
            # Set environment variable for mode
            os.environ["HER_CANONICAL_MODE"] = mode.value
            
            # Initialize runner
            runner = Runner(headless=True)
            runner._ensure_browser()
            runner._page.goto("https://www.verizon.com/")
            
            # Get snapshot
            snapshot = runner._snapshot()
            elements = snapshot.get('elements', [])
            
            print(f"\\n📊 {mode_name} RESULTS:")
            print(f"   Total elements: {len(elements)}")
            
            # Analyze specific element types
            print(f"\\n🔍 ELEMENT TYPE ANALYSIS:")
            
            # Count elements with different attribute types
            interactive_elements = [e for e in elements if e.get('interactive', False)]
            elements_with_roles = [e for e in elements if e.get('role')]
            elements_with_ids = [e for e in elements if e.get('attrs', {}).get('id')]
            elements_with_classes = [e for e in elements if e.get('attrs', {}).get('class')]
            elements_with_aria = [e for e in elements if any(k.startswith('aria-') for k in e.get('attrs', {}).keys())]
            elements_with_data = [e for e in elements if any(k.startswith('data-') for k in e.get('attrs', {}).keys())]
            
            print(f"   Interactive elements: {len(interactive_elements)}")
            print(f"   Elements with roles: {len(elements_with_roles)}")
            print(f"   Elements with IDs: {len(elements_with_ids)}")
            print(f"   Elements with classes: {len(elements_with_classes)}")
            print(f"   Elements with ARIA: {len(elements_with_aria)}")
            print(f"   Elements with data-*: {len(elements_with_data)}")
            
            # Check accessibility tree coverage
            elements_with_ax = [e for e in elements if e.get('accessibility')]
            print(f"   Elements with accessibility info: {len(elements_with_ax)}")
            
            # Analyze first 5 interactive elements in detail
            print(f"\\n🔍 INTERACTIVE ELEMENTS ANALYSIS (First 5):")
            for i, element in enumerate(interactive_elements[:5]):
                print(f"\\n   Interactive Element {i+1}:")
                print(f"     Tag: '{element.get('tag', 'N/A')}'")
                print(f"     Text: '{element.get('text', 'N/A')[:50]}{'...' if len(str(element.get('text', ''))) > 50 else ''}'")
                print(f"     Role: '{element.get('role', 'N/A')}'")
                print(f"     BackendNodeId: {element.get('backendNodeId', 'N/A')}")
                
                # Analyze attributes
                attrs = element.get('attrs', {})
                print(f"     Attributes count: {len(attrs)}")
                if attrs:
                    print(f"     Key attributes: {list(attrs.keys())[:10]}{'...' if len(attrs) > 10 else ''}")
                
                # Analyze accessibility info
                ax_info = element.get('accessibility', {})
                if ax_info:
                    print(f"     Accessibility info: {list(ax_info.keys())}")
                else:
                    print(f"     Accessibility info: None")
            
            # Store results
            results[mode_name] = {
                'total_elements': len(elements),
                'interactive_elements': len(interactive_elements),
                'elements_with_roles': len(elements_with_roles),
                'elements_with_ids': len(elements_with_ids),
                'elements_with_classes': len(elements_with_classes),
                'elements_with_aria': len(elements_with_aria),
                'elements_with_data': len(elements_with_data),
                'elements_with_ax': len(elements_with_ax)
            }
        
        # Compare results across modes
        print(f"\\n{'='*80}")
        print(f"📊 COMPARATIVE ANALYSIS")
        print(f"{'='*80}")
        
        for mode_name, data in results.items():
            print(f"\\n{mode_name}:")
            for key, value in data.items():
                print(f"   {key}: {value}")
        
        # Check for potential issues
        print(f"\\n🔍 POTENTIAL ISSUES ANALYSIS:")
        
        dom_only = results.get('DOM_ONLY', {})
        ax_only = results.get('ACCESSIBILITY_ONLY', {})
        both = results.get('BOTH', {})
        
        # Check if BOTH mode has more elements than individual modes
        if both['total_elements'] < max(dom_only['total_elements'], ax_only['total_elements']):
            print(f"   ⚠️  BOTH mode has fewer elements than individual modes")
            print(f"      DOM_ONLY: {dom_only['total_elements']}")
            print(f"      ACCESSIBILITY_ONLY: {ax_only['total_elements']}")
            print(f"      BOTH: {both['total_elements']}")
        
        # Check if ACCESSIBILITY_ONLY has reasonable element count
        if ax_only['total_elements'] < 100:
            print(f"   ⚠️  ACCESSIBILITY_ONLY mode has very few elements: {ax_only['total_elements']}")
        
        # Check accessibility coverage
        if both['elements_with_ax'] < both['total_elements'] * 0.5:
            print(f"   ⚠️  Low accessibility coverage in BOTH mode: {both['elements_with_ax']}/{both['total_elements']}")
        
        print(f"\\n✅ FOCUSED ATTRIBUTE ANALYSIS COMPLETED")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_attributes()
"""
    
    # Run test
    result = subprocess.run(
        [sys.executable, "-c", test_script],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent.parent
    )
    
    print("Raw output:")
    print(result.stdout)
    print("Raw error:")
    print(result.stderr)

if __name__ == "__main__":
    test_focused_attribute_analysis()