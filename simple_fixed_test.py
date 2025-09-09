#!/usr/bin/env python3
"""
Simple Fixed Test - Test each mode individually to avoid async conflicts
"""

import os
import time
import subprocess
import sys

def test_mode_individually(mode, mode_name):
    """Test a specific mode by running it in a separate process"""
    
    print(f"\n🔬 TESTING: {mode_name}")
    print("=" * 60)
    
    # Create a simple test script for this mode
    test_script = f"""
import os
import time
from her.runner import Runner
from her.config import CanonicalMode

# Set environment variable
os.environ['HER_CANONICAL_MODE'] = '{mode.value}'

start_time = time.time()

try:
    # Create runner and get snapshot directly
    runner = Runner(headless=True)
    snapshot = runner._snapshot('https://www.google.com/')
    
    duration = time.time() - start_time
    
    print(f"✅ {mode_name} completed in {{duration:.2f}}s")
    
    # Analyze snapshot data
    if isinstance(snapshot, dict):
        print(f"📊 Snapshot keys: {{list(snapshot.keys())}}")
        
        if 'elements' in snapshot:
            elements = snapshot['elements']
            print(f"📊 Elements extracted: {{len(elements)}}")
            
            # Analyze element types
            dom_elements = sum(1 for e in elements if hasattr(e, 'tag') and e.tag)
            ax_elements = sum(1 for e in elements if hasattr(e, 'ax_role') and e.ax_role)
            interactive_elements = sum(1 for e in elements if hasattr(e, 'ax_role') and e.ax_role in ['button', 'textbox', 'link', 'checkbox', 'radio', 'combobox'])
            
            print(f"   DOM elements: {{dom_elements}}")
            print(f"   Accessibility elements: {{ax_elements}}")
            print(f"   Interactive elements: {{interactive_elements}}")
            
            # Sample some elements
            print(f"\\n📋 Sample elements:")
            for i, elem in enumerate(elements[:5]):
                if hasattr(elem, 'tag') and elem.tag:
                    print(f"   {{i+1}}. {{elem.tag}}: {{getattr(elem, 'text', '')[:50]}}...")
                elif hasattr(elem, 'ax_role') and elem.ax_role:
                    print(f"   {{i+1}}. {{elem.ax_role}}: {{getattr(elem, 'ax_name', '')[:50]}}...")
                else:
                    print(f"   {{i+1}}. Unknown element: {{elem}}")
        else:
            print("❌ No elements found in snapshot")
    else:
        print(f"❌ Snapshot is not a dictionary: {{type(snapshot)}}")
        
except Exception as e:
    duration = time.time() - start_time
    print(f"❌ {mode_name} failed after {{duration:.2f}}s: {{e}}")
    import traceback
    traceback.print_exc()
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
        
        print(f"⏱️  Total time: {duration:.2f}s")
        print(f"📤 Return code: {result.returncode}")
        
        if result.stdout:
            print("📤 STDOUT:")
            print(result.stdout)
        
        if result.stderr:
            print("📤 STDERR:")
            print(result.stderr)
            
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ Failed to run test after {duration:.2f}s: {e}")

def main():
    """Test all CDP modes individually"""
    
    print("🔬 SIMPLE FIXED CDP TEST")
    print("=" * 60)
    
    from her.config import CanonicalMode
    
    modes = [
        (CanonicalMode.DOM_ONLY, "DOM Only"),
        (CanonicalMode.ACCESSIBILITY_ONLY, "Accessibility Only"),
        (CanonicalMode.BOTH, "Both DOM + Accessibility")
    ]
    
    for mode, mode_name in modes:
        test_mode_individually(mode, mode_name)
    
    print(f"\n🎯 SUMMARY")
    print("=" * 60)
    print("All modes tested individually to avoid async conflicts")

if __name__ == "__main__":
    main()