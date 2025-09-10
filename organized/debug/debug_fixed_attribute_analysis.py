#!/usr/bin/env python3
"""
Fixed Attribute Analysis
Tests DOM/accessibility extraction and canonical descriptor making for all 3 modes
Uses subprocess isolation to avoid Playwright async/sync conflicts
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def test_fixed_attribute_analysis():
    """Test fixed attribute capture for all 3 CDP modes"""
    
    print("🔍 FIXED ATTRIBUTE ANALYSIS")
    print("=" * 80)
    
    # Test script for each mode in isolation
    test_script_template = """
import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))
os.environ["HER_MODELS_DIR"] = str(Path.cwd() / "src" / "her" / "models")
os.environ["HER_CACHE_DIR"] = str(Path.cwd() / ".her_cache")

from her.runner import Runner
from her.config import CanonicalMode

def test_mode():
    try:
        # Set environment variable for mode
        os.environ["HER_CANONICAL_MODE"] = "{mode}"
        
        # Initialize runner
        runner = Runner(headless=True)
        runner._ensure_browser()
        runner._page.goto("https://www.verizon.com/")
        
        # Get snapshot
        snapshot = runner._snapshot()
        elements = snapshot.get('elements', [])
        
        print(f"📊 {mode_name} RESULTS:")
        print(f"   Total elements: {{len(elements)}}")
        
        # Analyze specific element types
        interactive_elements = [e for e in elements if e.get('interactive', False)]
        elements_with_roles = [e for e in elements if e.get('role')]
        elements_with_ids = [e for e in elements if e.get('attrs', {{}}).get('id')]
        elements_with_classes = [e for e in elements if e.get('attrs', {{}}).get('class')]
        elements_with_aria = [e for e in elements if any(k.startswith('aria-') for k in e.get('attrs', {{}}).keys())]
        elements_with_data = [e for e in elements if any(k.startswith('data-') for k in e.get('attrs', {{}}).keys())]
        elements_with_ax = [e for e in elements if e.get('accessibility')]
        
        print(f"   Interactive elements: {{len(interactive_elements)}}")
        print(f"   Elements with roles: {{len(elements_with_roles)}}")
        print(f"   Elements with IDs: {{len(elements_with_ids)}}")
        print(f"   Elements with classes: {{len(elements_with_classes)}}")
        print(f"   Elements with ARIA: {{len(elements_with_aria)}}")
        print(f"   Elements with data-*: {{len(elements_with_data)}}")
        print(f"   Elements with accessibility info: {{len(elements_with_ax)}}")
        
        # Analyze first 3 interactive elements
        print(f"\\n🔍 INTERACTIVE ELEMENTS ANALYSIS (First 3):")
        for i, element in enumerate(interactive_elements[:3]):
            print(f"\\n   Interactive Element {{i+1}}:")
            print(f"     Tag: '{{element.get('tag', 'N/A')}}'")
            print(f"     Text: '{{element.get('text', 'N/A')[:50]}}{'...' if len(str(element.get('text', ''))) > 50 else ''}'")
            print(f"     Role: '{{element.get('role', 'N/A')}}'")
            print(f"     BackendNodeId: {{element.get('backendNodeId', 'N/A')}}")
            
            attrs = element.get('attrs', {{}})
            print(f"     Attributes count: {{len(attrs)}}")
            if attrs:
                print(f"     Key attributes: {{list(attrs.keys())[:5]}}{'...' if len(attrs) > 5 else ''}")
            
            ax_info = element.get('accessibility', {{}})
            if ax_info:
                print(f"     Accessibility info: {{list(ax_info.keys())}}")
            else:
                print(f"     Accessibility info: None")
        
        # Return results as JSON
        results = {{
            'mode': '{mode_name}',
            'total_elements': len(elements),
            'interactive_elements': len(interactive_elements),
            'elements_with_roles': len(elements_with_roles),
            'elements_with_ids': len(elements_with_ids),
            'elements_with_classes': len(elements_with_classes),
            'elements_with_aria': len(elements_with_aria),
            'elements_with_data': len(elements_with_data),
            'elements_with_ax': len(elements_with_ax)
        }}
        
        print(f"\\n✅ {mode_name} COMPLETED")
        print(f"RESULTS_JSON: {{json.dumps(results)}}")
        
    except Exception as e:
        print(f"❌ ERROR in {mode_name}: {{e}}")
        import traceback
        traceback.print_exc()
        print(f"RESULTS_JSON: {{'mode': '{mode_name}', 'error': str(e)}}")
"""

    # Test all 3 modes
    modes = [
        ("DOM_ONLY", "DOM_ONLY"),
        ("ACCESSIBILITY_ONLY", "ACCESSIBILITY_ONLY"), 
        ("BOTH", "BOTH")
    ]
    
    results = {}
    
    for mode, mode_name in modes:
        print(f"\\n{'='*60}")
        print(f"🔍 TESTING {mode_name} MODE")
        print(f"{'='*60}")
        
        # Create test script for this mode
        test_script = test_script_template.format(mode=mode, mode_name=mode_name)
        
        # Run test in subprocess
        result = subprocess.run(
            [sys.executable, "-c", test_script],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        print("Output:")
        print(result.stdout)
        if result.stderr:
            print("Error:")
            print(result.stderr)
        
        # Extract results from output
        try:
            for line in result.stdout.split('\\n'):
                if line.startswith('RESULTS_JSON:'):
                    json_str = line.replace('RESULTS_JSON: ', '')
                    results[mode_name] = json.loads(json_str)
                    break
        except Exception as e:
            print(f"Failed to parse results for {mode_name}: {e}")
            results[mode_name] = {'mode': mode_name, 'error': str(e)}
    
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
    if 'total_elements' in both and 'total_elements' in dom_only and 'total_elements' in ax_only:
        if both['total_elements'] < max(dom_only['total_elements'], ax_only['total_elements']):
            print(f"   ⚠️  BOTH mode has fewer elements than individual modes")
            print(f"      DOM_ONLY: {dom_only['total_elements']}")
            print(f"      ACCESSIBILITY_ONLY: {ax_only['total_elements']}")
            print(f"      BOTH: {both['total_elements']}")
    
    # Check if ACCESSIBILITY_ONLY has reasonable element count
    if 'total_elements' in ax_only and ax_only['total_elements'] < 100:
        print(f"   ⚠️  ACCESSIBILITY_ONLY mode has very few elements: {ax_only['total_elements']}")
    
    # Check accessibility coverage
    if 'elements_with_ax' in both and 'total_elements' in both:
        if both['elements_with_ax'] < both['total_elements'] * 0.5:
            print(f"   ⚠️  Low accessibility coverage in BOTH mode: {both['elements_with_ax']}/{both['total_elements']}")
    
    print(f"\\n✅ FIXED ATTRIBUTE ANALYSIS COMPLETED")

if __name__ == "__main__":
    test_fixed_attribute_analysis()