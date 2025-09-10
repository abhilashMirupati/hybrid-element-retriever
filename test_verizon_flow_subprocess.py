#!/usr/bin/env python3
"""
Comprehensive Verizon Flow Test with Subprocess Isolation
Tests all 3 modes with detailed logging for each step in the process
"""

import subprocess
import os
import time
import json
from datetime import datetime

def run_test_mode(mode_name, env_vars, test_query, url):
    """Run a test mode in a subprocess to avoid Playwright async/sync conflicts"""
    start_time = time.time()
    print(f"\n{'='*80}")
    print(f"🔍 TESTING {mode_name.upper()}")
    print(f"{'='*80}")
    
    # Create the test script as a string
    test_script = f"""
import os
import sys
import time
import json
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Set environment variables
{chr(10).join([f"os.environ['{k}'] = '{v}'" for k, v in env_vars.items()])}

from her.runner import Runner
from her.config import get_config
from her.parser.enhanced_intent import EnhancedIntentParser

def print_section(title, width=80):
    print(f"\\n{'=' * width}")
    print(f"🔍 {title}")
    print(f"{'=' * width}")

def print_step(step_name, data, max_length=200):
    print(f"\\n📋 {step_name}:")
    print("-" * 60)
    
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, str) and len(value) > max_length:
                print(f"   {key}: '{value[:max_length]}...' (length: {len(value)})")
            else:
                print(f"   {key}: {value}")
    elif isinstance(data, list):
        print(f"   List with {len(data)} items:")
        for i, item in enumerate(data[:5]):
            if isinstance(item, dict):
                print(f"     {i+1}. {item}")
            else:
                print(f"     {i+1}. {item}")
        if len(data) > 5:
            print(f"     ... and {len(data) - 5} more items")
    else:
        print(f"   {data}")

try:
    # Configuration
    print_section("CONFIGURATION")
    config = get_config()
    print_step("Environment Variables", {
        "HER_CANONICAL_MODE": os.environ.get('HER_CANONICAL_MODE'),
        "HER_USE_HIERARCHY": os.environ.get('HER_USE_HIERARCHY'),
        "HER_USE_TWO_STAGE": os.environ.get('HER_USE_TWO_STAGE'),
        "use_hierarchy": config.should_use_hierarchy(),
        "use_two_stage": config.should_use_two_stage(),
        "debug_hierarchy": config.is_hierarchy_debug_enabled()
    })
    
    # Initialize runner
    print_section("RUNNER INITIALIZATION")
    init_start = time.time()
    runner = Runner()
    init_time = time.time() - init_start
    print(f"✅ Runner initialized in {{init_time:.2f}}s")
    
    # Test query parsing
    print_section("QUERY PARSING")
    print(f"Parsing: '{test_query}'")
    parser = EnhancedIntentParser()
    parsed = parser.parse('{test_query}')
    print_step("Parsed Intent", {{
        "action": parsed.action,
        "target_phrase": parsed.target_phrase,
        "value": parsed.value,
        "confidence": parsed.confidence
    }})
    
    # Take snapshot
    print_section("DOM/ACCESSIBILITY SNAPSHOT")
    print(f"URL: {url}")
    snapshot_start = time.time()
    snapshot = runner._snapshot('{url}')
    snapshot_time = time.time() - snapshot_start
    
    elements = snapshot.get('elements', [])
    print_step("Snapshot Results", {{
        "total_elements": len(elements),
        "snapshot_time": f"{{snapshot_time:.2f}}s",
        "frame_url": snapshot.get('url', 'N/A'),
        "frame_hash": snapshot.get('frame_hash', 'N/A')
    }})
    
    # Analyze element types
    element_types = {{}}
    interactive_count = 0
    text_nodes = 0
    for el in elements:
        tag = el.get('tag', 'unknown')
        element_types[tag] = element_types.get(tag, 0) + 1
        if el.get('interactive', False):
            interactive_count += 1
        if tag == '#text':
            text_nodes += 1
    
    print_step("Element Analysis", {{
        "element_type_distribution": dict(sorted(element_types.items(), key=lambda x: x[1], reverse=True)[:10]),
        "interactive_elements": interactive_count,
        "text_nodes": text_nodes,
        "total_elements": len(elements)
    }})
    
    # Check for hierarchy context
    if config.should_use_hierarchy():
        hierarchy_elements = [el for el in elements if 'context' in el and el['context'].get('hierarchy_path')]
        print_step("Hierarchy Context", {{
            "elements_with_context": len(hierarchy_elements),
            "total_elements": len(elements),
            "context_coverage": f"{{len(hierarchy_elements)/len(elements)*100:.1f}}%" if elements else "0%"
        }})
        
        # Show sample hierarchy context
        if hierarchy_elements:
            sample = hierarchy_elements[0]
            print_step("Sample Hierarchy Context", {{
                "tag": sample.get('tag'),
                "text": sample.get('text', '')[:50] + '...',
                "hierarchy_path": sample['context'].get('hierarchy_path'),
                "depth": sample['context'].get('depth'),
                "has_children": sample['context'].get('has_children')
            }})
    
    # Test element selection
    print_section("ELEMENT SELECTION")
    print(f"Query: '{test_query}'")
    query_start = time.time()
    result = runner._resolve_selector('{test_query}', snapshot)
    query_time = time.time() - query_start
    
    print_step("Selection Results", {{
        "strategy": result.get('strategy', 'unknown'),
        "confidence": result.get('confidence', 0.0),
        "selected_selector": result.get('selector', 'N/A'),
        "query_time": f"{{query_time:.2f}}s",
        "candidates_found": len(result.get('candidates', []))
    }})
    
    # Show top candidates
    candidates = result.get('candidates', [])
    if candidates:
        print_step("Top 5 Candidates", "Detailed analysis:")
        for i, candidate in enumerate(candidates[:5]):
            print(f"   {{i+1}}. Score: {{candidate.get('score', 0.0):.3f}}")
            print(f"      XPath: {{candidate.get('xpath', 'N/A')}}")
            print(f"      Text: '{{candidate.get('text', '')[:50]}}...'")
            print(f"      Tag: {{candidate.get('tag', 'N/A')}}")
            print(f"      Interactive: {{candidate.get('interactive', False)}}")
            print(f"      Reasons: {{candidate.get('reasons', [])}}")
            print()
    
    # Check for text duplication issues
    shop_elements = [el for el in elements if 'shop' in el.get('text', '').lower()]
    duplicated_texts = [el for el in shop_elements if el.get('text', '').count('Shop') > 1]
    
    print_step("Text Quality Check", {{
        "shop_elements_found": len(shop_elements),
        "duplicated_texts": len(duplicated_texts),
        "text_quality": "GOOD" if len(duplicated_texts) == 0 else "ISSUES DETECTED"
    }})
    
    if duplicated_texts:
        print_step("Duplicated Text Examples", "Issues found:")
        for i, el in enumerate(duplicated_texts[:3]):
            print(f"   {{i+1}}. Text: '{{el.get('text', '')}}'")
            print(f"      Tag: {{el.get('tag', '')}}")
            print(f"      XPath: {{el.get('xpath', '')}}")
    
    # Cleanup
    print_section("CLEANUP")
    print("Cleaning up resources...")
    runner.cleanup_models()
    runner._browser.close()
    runner._playwright.stop()
    print("✅ Cleanup completed")
    
    total_time = time.time() - init_start
    print_section("MODE SUMMARY")
    print_step("Results", {{
        "mode": "{mode_name}",
        "total_time": f"{{total_time:.2f}}s",
        "snapshot_time": f"{{snapshot_time:.2f}}s",
        "query_time": f"{{query_time:.2f}}s",
        "elements_processed": len(elements),
        "strategy_used": result.get('strategy', 'unknown'),
        "confidence": result.get('confidence', 0.0),
        "success": result.get('selector', '') != '',
        "text_quality": len(duplicated_texts) == 0
    }})
    
    # Return results as JSON for parent process
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
        "interactive_elements": interactive_count,
        "text_nodes": text_nodes
    }}
    
    print(f"\\n🎯 FINAL_RESULT_JSON: {{json.dumps(results)}}")
    
except Exception as e:
    print(f"\\n❌ ERROR in {mode_name}: {{e}}")
    import traceback
    traceback.print_exc()
    
    # Return error results
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
        "interactive_elements": 0,
        "text_nodes": 0
    }}
    
    print(f"\\n🎯 FINAL_RESULT_JSON: {{json.dumps(error_results)}}")
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
        if line.startswith('🎯 FINAL_RESULT_JSON:'):
            try:
                json_str = line.replace('🎯 FINAL_RESULT_JSON: ', '')
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
            "interactive_elements": 0,
            "text_nodes": 0
        }
    
    return results, total_time

def main():
    """Run comprehensive tests for all 3 modes"""
    print(f"\n{'='*80}")
    print(f"🔍 COMPREHENSIVE VERIZON FLOW TEST - SUBPROCESS VERSION")
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
                "interactive_elements": 0,
                "text_nodes": 0
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
        print(f"     Text Nodes: {result.get('text_nodes', 0)}")
        print(f"     Strategy: {result.get('strategy', 'unknown')}")
        print(f"     Confidence: {result.get('confidence', 0.0):.3f}")
        print(f"     Text Quality: {text_quality}")
        if result.get("selected_selector"):
            print(f"     Selected: {result.get('selected_selector', '')[:80]}...")
        if not result.get("success", False):
            all_passed = False
    
    print(f"\n🎯 OVERALL RESULT: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    # Performance comparison
    print(f"\n{'='*80}")
    print(f"🔍 PERFORMANCE COMPARISON")
    print(f"{'='*80}")
    for mode, result in results.items():
        if result.get("success", False):
            print(f"   {mode}: {result.get('total_time', 0):.2f}s total, {result.get('query_time', 0):.2f}s query")
    
    return results

if __name__ == "__main__":
    main()