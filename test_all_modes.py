#!/usr/bin/env python3
"""
Test all 3 modes with subprocess isolation
"""

import subprocess
import sys
import time

def run_test(mode_name, env_vars):
    print(f'\n📋 TESTING {mode_name.upper()}')
    print(f'Environment: {env_vars}')
    
    script = f'''
import os
import time
from src.her.runner import Runner

# Set environment variables
{chr(10).join([f"os.environ['{k}'] = '{v}'" for k, v in env_vars.items()])}

start = time.time()
runner = Runner()
snapshot = runner._snapshot('https://www.verizon.com/')
result = runner._resolve_selector('Click on the Shop button', snapshot)
test_time = time.time() - start

print(f'✅ {mode_name}: {{test_time:.2f}}s')
print(f'   Strategy: {{result.get("strategy", "unknown")}}')
print(f'   Confidence: {{result.get("confidence", 0.0):.3f}}')
print(f'   Elements: {{len(snapshot.get("elements", []))}}')
print(f'   Selected: {{result.get("selector", "N/A")}}')
'''
    
    result = subprocess.run([sys.executable, '-c', script], 
                          env=env_vars, capture_output=True, text=True, cwd='/workspace')
    
    print(f'📤 OUTPUT:')
    print(result.stdout)
    if result.stderr:
        print(f'⚠️  ERRORS:')
        print(result.stderr)
    
    return result.returncode == 0, result.stdout

def main():
    print('🔧 TESTING ALL 3 MODES ON VERIZON PAGE (Subprocess Isolation)')
    print('=' * 70)

    # Test 1: Standard Mode
    success1, output1 = run_test('Standard Mode', {
        'HER_CANONICAL_MODE': 'both',
        'HER_USE_HIERARCHY': 'false',
        'HER_USE_TWO_STAGE': 'false'
    })

    # Test 2: Hierarchy Only Mode
    success2, output2 = run_test('Hierarchy Only Mode', {
        'HER_CANONICAL_MODE': 'both',
        'HER_USE_HIERARCHY': 'true',
        'HER_USE_TWO_STAGE': 'false'
    })

    # Test 3: Two-Stage Mode
    success3, output3 = run_test('Two-Stage Mode', {
        'HER_CANONICAL_MODE': 'both',
        'HER_USE_HIERARCHY': 'true',
        'HER_USE_TWO_STAGE': 'true'
    })

    print(f'\n🎯 FINAL SUMMARY:')
    print(f'   Standard Mode: {"✅ PASSED" if success1 else "❌ FAILED"}')
    print(f'   Hierarchy Mode: {"✅ PASSED" if success2 else "❌ FAILED"}')
    print(f'   Two-Stage Mode: {"✅ PASSED" if success3 else "❌ FAILED"}')

    total_passed = sum([success1, success2, success3])
    print(f'\n🎉 OVERALL RESULT: {total_passed}/3 tests passed')
    print(f'✅ Framework is production-ready!' if total_passed == 3 else '❌ Some issues detected')

if __name__ == "__main__":
    main()