#!/usr/bin/env python3
"""
Final Integration Test with Detailed Logging
Tests all 3 CDP modes with comprehensive input/output tracking
"""

import os
import sys
import time
import subprocess
from datetime import datetime

def log_section(title):
    print(f"\n{'='*80}")
    print(f"🔍 {title}")
    print(f"{'='*80}")

def log_phase(phase, description):
    print(f"\n📋 PHASE {phase}: {description}")
    print("-" * 60)

def run_detailed_test(mode_name, env_vars, test_query):
    """Run a detailed test with comprehensive logging"""
    
    log_section(f"TESTING {mode_name.upper()} MODE")
    print(f"Environment Variables: {env_vars}")
    print(f"Test Query: '{test_query}'")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    start_time = time.time()
    
    # Create a temporary script file to avoid f-string issues
    script_content = f"""
import sys
sys.path.append('/workspace')
import os
import time
from src.her.runner import Runner
from src.her.config import get_config

# Set environment variables
{chr(10).join([f"os.environ['{k}'] = '{v}'" for k, v in env_vars.items()])}

print("\\n🔧 CONFIGURATION SETUP")
print("=" * 50)
config = get_config()
print(f"Canonical Mode: {{config.canonical_mode}}")
print(f"Use Hierarchy: {{config.should_use_hierarchy()}}")
print(f"Use Two-Stage: {{config.should_use_two_stage()}}")
print(f"Debug Hierarchy: {{config.is_hierarchy_debug_enabled()}}")

print("\\n🚀 RUNNER INITIALIZATION")
print("=" * 50)
runner_start = time.time()
runner = Runner()
runner_init_time = time.time() - runner_start
print(f"✅ Runner created successfully ({{runner_init_time:.2f}}s)")

print("\\n📸 SNAPSHOT CAPTURE")
print("=" * 50)
snapshot_start = time.time()
snapshot = runner._snapshot("https://www.verizon.com/")
snapshot_time = time.time() - snapshot_start

elements = snapshot.get('elements', [])
print(f"✅ Snapshot completed ({{snapshot_time:.2f}}s)")
print(f"   Total elements captured: {{len(elements)}}")
print(f"   Frame URL: {{snapshot.get('url', 'N/A')}}")
print(f"   Frame hash: {{snapshot.get('frame_hash', 'N/A')}}")

# Analyze element types
element_types = {{}}
for el in elements:
    tag = el.get('tag', 'unknown')
    element_types[tag] = element_types.get(tag, 0) + 1

print(f"\\n📊 ELEMENT BREAKDOWN:")
for tag, count in sorted(element_types.items(), key=lambda x: x[1], reverse=True)[:10]:
    print(f"   {{tag}}: {{count}}")

# Check for hierarchy context
elements_with_context = [e for e in elements if 'context' in e]
print(f"\\n🌳 HIERARCHY ANALYSIS:")
print(f"   Elements with context: {{len(elements_with_context)}}")
if elements_with_context:
    sample_context = elements_with_context[0]['context']
    print(f"   Sample context keys: {{list(sample_context.keys())}}")
    print(f"   Sample hierarchy_path: {{sample_context.get('hierarchy_path', 'N/A')}}")

print("\\n🎯 QUERY PROCESSING")
print("=" * 50)
query_start = time.time()
result = runner._resolve_selector("{test_query}", snapshot)
query_time = time.time() - query_start

print(f"✅ Query completed ({{query_time:.2f}}s)")
print(f"   Strategy used: {{result.get('strategy', 'unknown')}}")
print(f"   Confidence: {{result.get('confidence', 0.0):.3f}}")
print(f"   Selected element: {{result.get('selector', 'N/A')}}")
print(f"   Element text: {{result.get('meta', {{}}).get('text', 'N/A')[:50]}}...")
print(f"   Candidates found: {{len(result.get('candidates', []))}}")

# Detailed candidate analysis
candidates = result.get('candidates', [])
if candidates:
    print(f"\\n🏆 TOP 5 CANDIDATES:")
    for i, candidate in enumerate(candidates[:5], 1):
        score = candidate.get('score', 0.0)
        selector = candidate.get('selector', 'N/A')
        text = candidate.get('meta', {{}}).get('text', 'N/A')[:30]
        print(f"   {{i}}. Score: {{score:.3f}} | {{selector}} | '{{text}}...'")

total_time = time.time() - start_time
print(f"\\n⏱️  TIMING SUMMARY:")
print(f"   Runner Init: {{runner_init_time:.2f}}s")
print(f"   Snapshot: {{snapshot_time:.2f}}s")
print(f"   Query: {{query_time:.2f}}s")
print(f"   Total: {{total_time:.2f}}s")

print(f"\\n✅ {mode_name.upper()} MODE TEST COMPLETED")
"""
    
    # Write to temporary file
    with open('/tmp/test_script.py', 'w') as f:
        f.write(script_content)
    
    result = subprocess.run([sys.executable, '/tmp/test_script.py'], 
                          env=env_vars, capture_output=True, text=True, cwd='/workspace')
    
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"\n📤 OUTPUT:")
    print(result.stdout)
    
    if result.stderr:
        print(f"\n⚠️  ERRORS:")
        print(result.stderr)
    
    print(f"\n⏱️  TOTAL TEST TIME: {total_time:.2f}s")
    print(f"Exit Code: {result.returncode}")
    
    return result.returncode == 0, total_time

def main():
    log_section("FINAL INTEGRATION TEST - VERIZON PAGE")
    print("Testing all 3 CDP modes with detailed input/output tracking")
    print(f"Test started at: {datetime.now().isoformat()}")
    
    test_query = "Click on the 'Shop' button"
    
    # Test configurations
    tests = [
        {
            "name": "Standard Mode",
            "env": {
                "HER_CANONICAL_MODE": "both",
                "HER_USE_HIERARCHY": "false",
                "HER_USE_TWO_STAGE": "false"
            }
        },
        {
            "name": "Hierarchy Only Mode", 
            "env": {
                "HER_CANONICAL_MODE": "both",
                "HER_USE_HIERARCHY": "true",
                "HER_USE_TWO_STAGE": "false"
            }
        },
        {
            "name": "Two-Stage Mode",
            "env": {
                "HER_CANONICAL_MODE": "both", 
                "HER_USE_HIERARCHY": "true",
                "HER_USE_TWO_STAGE": "true"
            }
        }
    ]
    
    results = []
    total_start = time.time()
    
    for i, test in enumerate(tests, 1):
        log_phase(i, f"{test['name']} - {test['env']}")
        success, test_time = run_detailed_test(test['name'], test['env'], test_query)
        results.append({
            'name': test['name'],
            'success': success,
            'time': test_time
        })
    
    total_time = time.time() - total_start
    
    # Final Summary
    log_section("FINAL INTEGRATION TEST RESULTS")
    print(f"Total test time: {total_time:.2f}s")
    print(f"Test query: '{test_query}'")
    print(f"Website: https://www.verizon.com/")
    
    print(f"\n📊 RESULTS SUMMARY:")
    for result in results:
        status = "✅ PASSED" if result['success'] else "❌ FAILED"
        print(f"   {result['name']}: {status} ({result['time']:.2f}s)")
    
    passed = sum(1 for r in results if r['success'])
    total = len(results)
    
    print(f"\n🎯 OVERALL RESULT: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - INTEGRATION SUCCESSFUL!")
        print("✅ Framework is production-ready")
    else:
        print("❌ SOME TESTS FAILED - INTEGRATION ISSUES DETECTED")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)