#!/usr/bin/env python3
"""
Simple Verizon Flow Test with Subprocess Isolation
Tests all 3 modes with basic logging
"""

import subprocess
import os
import time
import json
from datetime import datetime

def run_test_mode(mode_name, env_vars, test_query, url):
    """Run a test mode in a subprocess"""
    start_time = time.time()
    print(f"\n{'='*60}")
    print(f"🔍 TESTING {mode_name.upper()}")
    print(f"{'='*60}")
    
    # Create a simple test script
    test_script = f"""
import os
import sys
import time
import json

# Set environment variables
{chr(10).join([f"os.environ['{k}'] = '{v}'" for k, v in env_vars.items()])}

# Add the src directory to the path
sys.path.insert(0, 'src')

try:
    from her.runner import Runner
    from her.config import get_config
    from her.parser.enhanced_intent import EnhancedIntentParser
    
    print("Environment variables set")
    
    # Initialize
    config = get_config()
    print(f"Config - Hierarchy: {{config.should_use_hierarchy()}}, Two-Stage: {{config.should_use_two_stage()}}")
    
    runner = Runner()
    print("✅ Runner initialized")
    
    # Parse query
    parser = EnhancedIntentParser()
    parsed = parser.parse('{test_query}')
    print(f"Parsed: action='{{parsed.action}}', target='{{parsed.target_phrase}}'")
    
    # Take snapshot
    print("Taking snapshot...")
    snapshot_start = time.time()
    snapshot = runner._snapshot('{url}')
    snapshot_time = time.time() - snapshot_start
    
    elements = snapshot.get('elements', [])
    print(f"Snapshot: {{len(elements)}} elements in {{snapshot_time:.2f}}s")
    
    # Analyze elements
    element_types = {{}}
    interactive_count = 0
    for el in elements:
        tag = el.get('tag', 'unknown')
        element_types[tag] = element_types.get(tag, 0) + 1
        if el.get('interactive', False):
            interactive_count += 1
    
    print(f"Element types: {{dict(sorted(element_types.items(), key=lambda x: x[1], reverse=True)[:5])}}")
    print(f"Interactive elements: {{interactive_count}}")
    
    # Test element selection
    print("Testing element selection...")
    query_start = time.time()
    result = runner._resolve_selector('{test_query}', snapshot)
    query_time = time.time() - query_start
    
    print(f"Selection: {{result.get('strategy', 'unknown')}} strategy, confidence: {{result.get('confidence', 0.0):.3f}}")
    print(f"Selected: {{result.get('selector', 'N/A')[:80]}}...")
    print(f"Query time: {{query_time:.2f}}s")
    
    # Check for text duplication
    shop_elements = [el for el in elements if 'shop' in el.get('text', '').lower()]
    duplicated_texts = [el for el in shop_elements if el.get('text', '').count('Shop') > 1]
    print(f"Shop elements: {{len(shop_elements)}}, Duplicated: {{len(duplicated_texts)}}")
    
    # Show top candidates
    candidates = result.get('candidates', [])
    if candidates:
        print("Top 3 candidates:")
        for i, candidate in enumerate(candidates[:3]):
            print(f"  {{i+1}}. Score: {{candidate.get('score', 0.0):.3f}} | {{candidate.get('tag', 'N/A')}} | '{{candidate.get('text', '')[:30]}}...'")
    
    # Cleanup
    runner.cleanup_models()
    runner._browser.close()
    runner._playwright.stop()
    
    # Return results
    total_time = time.time() - init_start
    results = {{
        "success": result.get('selector', '') != '',
        "total_time": total_time,
        "snapshot_time": snapshot_time,
        "query_time": query_time,
        "elements_count": len(elements),
        "strategy": result.get('strategy', 'unknown'),
        "confidence": result.get('confidence', 0.0),
        "selected_selector": result.get('selector', ''),
        "text_quality": len(duplicated_texts) == 0,
        "interactive_elements": interactive_count
    }}
    
    print(f"\\n🎯 RESULTS: {{json.dumps(results)}}")
    
except Exception as e:
    print(f"❌ ERROR: {{e}}")
    import traceback
    traceback.print_exc()
    
    error_results = {{
        "success": False,
        "error": str(e),
        "total_time": 0,
        "snapshot_time": 0,
        "query_time": 0,
        "elements_count": 0,
        "strategy": "error",
        "confidence": 0.0,
        "selected_selector": "",
        "text_quality": False,
        "interactive_elements": 0
    }}
    
    print(f"\\n🎯 RESULTS: {{json.dumps(error_results)}}")
"""
    
    # Run the test in a subprocess
    process = subprocess.run(['python', '-c', test_script], 
                           capture_output=True, text=True, 
                           env=os.environ.copy())
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Print the output
    print(process.stdout)
    if process.stderr:
        print("STDERR:", process.stderr)
    
    # Extract results from output
    results = None
    for line in process.stdout.split('\n'):
        if line.startswith('🎯 RESULTS:'):
            try:
                json_str = line.replace('🎯 RESULTS: ', '')
                results = json.loads(json_str)
                break
            except json.JSONDecodeError:
                pass
    
    if results is None:
        results = {
            "success": False,
            "error": "Failed to parse results",
            "total_time": total_time,
            "snapshot_time": 0,
            "query_time": 0,
            "elements_count": 0,
            "strategy": "error",
            "confidence": 0.0,
            "selected_selector": "",
            "text_quality": False,
            "interactive_elements": 0
        }
    
    return results, total_time

def main():
    """Run tests for all 3 modes"""
    print(f"\n{'='*80}")
    print(f"🔍 SIMPLE VERIZON FLOW TEST")
    print(f"{'='*80}")
    print(f"Test started at: {datetime.now().isoformat()}")
    print(f"Testing URL: https://www.verizon.com/")
    print(f"Test Query: 'Click on the Shop button'")
    
    test_url = "https://www.verizon.com/"
    test_query = "Click on the Shop button"
    
    # Test configurations
    test_configs = [
        {
            "name": "Standard Mode",
            "env_vars": {
                "HER_CANONICAL_MODE": "both",
                "HER_USE_HIERARCHY": "false",
                "HER_USE_TWO_STAGE": "false"
            }
        },
        {
            "name": "Hierarchy Mode",
            "env_vars": {
                "HER_CANONICAL_MODE": "both",
                "HER_USE_HIERARCHY": "true",
                "HER_USE_TWO_STAGE": "false"
            }
        },
        {
            "name": "Two-Stage Mode",
            "env_vars": {
                "HER_CANONICAL_MODE": "both",
                "HER_USE_HIERARCHY": "true",
                "HER_USE_TWO_STAGE": "true"
            }
        }
    ]
    
    results = {}
    
    # Run tests for each mode
    for config in test_configs:
        try:
            result, time_taken = run_test_mode(config["name"], config["env_vars"], test_query, test_url)
            results[config["name"]] = result
        except Exception as e:
            print(f"\n❌ ERROR in {config['name']}: {e}")
            results[config["name"]] = {
                "success": False,
                "error": str(e),
                "total_time": 0,
                "snapshot_time": 0,
                "query_time": 0,
                "elements_count": 0,
                "strategy": "error",
                "confidence": 0.0,
                "selected_selector": "",
                "text_quality": False,
                "interactive_elements": 0
            }
    
    # Print final summary
    print(f"\n{'='*80}")
    print(f"🔍 FINAL TEST SUMMARY")
    print(f"{'='*80}")
    print(f"Test completed at: {datetime.now().isoformat()}")
    print(f"Total test time: {sum(r.get('total_time', 0) for r in results.values()):.2f}s")
    
    print("\n📊 RESULTS BY MODE:")
    all_passed = True
    for mode, result in results.items():
        status = "✅ PASSED" if result.get("success", False) else "❌ FAILED"
        text_quality = "✅ GOOD" if result.get("text_quality", False) else "❌ ISSUES"
        print(f"\n   {mode}:")
        print(f"     Status: {status}")
        print(f"     Time: {result.get('total_time', 0):.2f}s")
        print(f"     Elements: {result.get('elements_count', 0)}")
        print(f"     Interactive: {result.get('interactive_elements', 0)}")
        print(f"     Strategy: {result.get('strategy', 'unknown')}")
        print(f"     Confidence: {result.get('confidence', 0.0):.3f}")
        print(f"     Text Quality: {text_quality}")
        if result.get("selected_selector"):
            print(f"     Selected: {result.get('selected_selector', '')[:80]}...")
        if not result.get("success", False):
            all_passed = False
    
    print(f"\n🎯 OVERALL RESULT: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    return results

if __name__ == "__main__":
    main()