#!/usr/bin/env python3
"""
Comprehensive test of all 3 CDP modes to ensure no regressions after MarkupLM fixes.
"""

import os
import sys
import time
import subprocess
sys.path.insert(0, 'src')

def test_mode(mode, query, description):
    """Test a specific CDP mode."""
    print(f"\n{'='*80}")
    print(f"🧪 Testing {description} Mode")
    print(f"Query: '{query}'")
    print(f"{'='*80}")
    
    # Set environment variables
    env = os.environ.copy()
    env["HER_CANONICAL_MODE"] = mode
    env["HER_DISABLE_HEURISTICS"] = "false"  # Test with heuristics enabled
    
    # Create test script
    test_script = f'''
import sys
sys.path.insert(0, 'src')

from her.runner import Runner
from her.config import get_config

def test_{mode.lower()}_mode():
    print(f"🔧 Testing {mode} mode...")
    
    config = get_config()
    print(f"Config mode: {{config.get_canonical_mode().value}}")
    
    runner = Runner()
    
    try:
        # Test query
        query = "{query}"
        print(f"\\n🎯 Test Query: '{{query}}'")
        
        # Get page snapshot
        print(f"\\n📸 Taking page snapshot...")
        snapshot = runner._snapshot("https://www.verizon.com/")
        elements = snapshot.get("elements", [])
        print(f"✅ Captured {{len(elements)}} elements")
        
        # Test element resolution
        print(f"\\n🔍 Testing element resolution...")
        result = runner._resolve_selector(query, snapshot)
        
        print(f"\\n📊 Results:")
        print(f"   Strategy: {{result.get('strategy', 'unknown')}}")
        print(f"   Selector: {{result.get('selector', 'N/A')}}")
        print(f"   Confidence: {{result.get('confidence', 'N/A')}}")
        print(f"   Meta: {{result.get('meta', {{}}).get('text', 'N/A')}}")
        print(f"   Tag: {{result.get('meta', {{}}).get('tag', 'N/A')}}")
        
        # Check if result is valid
        if result.get('selector') and result.get('selector') != 'N/A' and result.get('selector') != '':
            print(f"✅ {mode} mode working correctly")
            return True
        else:
            print(f"❌ {mode} mode failed - no valid selector")
            return False
            
    except Exception as e:
        print(f"❌ {mode} mode error: {{e}}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        Runner.cleanup_models()

if __name__ == "__main__":
    success = test_{mode.lower()}_mode()
    exit(0 if success else 1)
'''
    
    # Write and run test script
    script_path = f"/tmp/test_{mode.lower()}_mode.py"
    with open(script_path, 'w') as f:
        f.write(test_script)
    
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            env=env,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        success = result.returncode == 0
        print(f"✅ {mode} mode test {'PASSED' if success else 'FAILED'}")
        return success
        
    except subprocess.TimeoutExpired:
        print(f"❌ {mode} mode test TIMEOUT")
        return False
    except Exception as e:
        print(f"❌ {mode} mode test ERROR: {e}")
        return False
    finally:
        # Clean up
        try:
            os.remove(script_path)
        except:
            pass

def test_all_modes():
    """Test all 3 CDP modes."""
    print("🚀 Comprehensive Test of All 3 CDP Modes")
    print("=" * 80)
    
    # Test cases
    test_cases = [
        ("DOM", "Click on the Phones button", "DOM Only"),
        ("ACCESSIBILITY", "Click on the Phones button", "Accessibility Only"), 
        ("BOTH", "Click on the Phones button", "DOM + Accessibility"),
    ]
    
    results = {}
    
    for mode, query, description in test_cases:
        success = test_mode(mode, query, description)
        results[mode] = success
        time.sleep(2)  # Brief pause between tests
    
    # Summary
    print(f"\n{'='*80}")
    print("📊 TEST SUMMARY")
    print(f"{'='*80}")
    
    all_passed = True
    for mode, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"   {mode:15} : {status}")
        if not success:
            all_passed = False
    
    print(f"\n🎯 Overall Result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    return all_passed

if __name__ == "__main__":
    success = test_all_modes()
    exit(0 if success else 1)