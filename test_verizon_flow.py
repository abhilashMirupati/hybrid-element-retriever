#!/usr/bin/env python3
"""
Comprehensive Verizon Flow Test with Verbose Debug Logs
Tests all 3 modes with detailed logging for each step in the process
"""

import os
import sys
import time
import json
from datetime import datetime
from typing import Dict, Any, List

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from her.runner import Runner
from her.config import get_config
from her.parser.enhanced_intent import EnhancedIntentParser

def print_section(title: str, width: int = 80):
    """Print a formatted section header"""
    print(f"\n{'=' * width}")
    print(f"🔍 {title}")
    print(f"{'=' * width}")

def print_step(step_name: str, data: Any, max_length: int = 200):
    """Print a step with formatted data"""
    print(f"\n📋 {step_name}:")
    print("-" * 60)
    
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, str) and len(value) > max_length:
                print(f"   {key}: '{value[:max_length]}...' (length: {len(value)})")
            else:
                print(f"   {key}: {value}")
    elif isinstance(data, list):
        print(f"   List with {len(data)} items:")
        for i, item in enumerate(data[:5]):  # Show first 5 items
            if isinstance(item, dict):
                print(f"     {i+1}. {item}")
            else:
                print(f"     {i+1}. {item}")
        if len(data) > 5:
            print(f"     ... and {len(data) - 5} more items")
    else:
        print(f"   {data}")

def test_mode(mode_name: str, env_vars: Dict[str, str], test_query: str, url: str):
    """Test a specific mode with comprehensive logging"""
    print_section(f"TESTING {mode_name.upper()}")
    
    # Set environment variables
    for key, value in env_vars.items():
        os.environ[key] = value
    
    # Re-initialize config to pick up new env vars
    config = get_config()
    print_step("Configuration", {
        "HER_CANONICAL_MODE": os.environ.get('HER_CANONICAL_MODE'),
        "HER_USE_HIERARCHY": os.environ.get('HER_USE_HIERARCHY'),
        "HER_USE_TWO_STAGE": os.environ.get('HER_USE_TWO_STAGE'),
        "use_hierarchy": config.should_use_hierarchy(),
        "use_two_stage": config.should_use_two_stage(),
        "debug_hierarchy": config.is_hierarchy_debug_enabled()
    })
    
    # Initialize runner
    print_step("Runner Initialization", "Starting...")
    start_time = time.time()
    runner = Runner()
    init_time = time.time() - start_time
    print(f"   ✅ Runner initialized in {init_time:.2f}s")
    
    # Test query parsing
    print_step("Query Parsing", f"Parsing: '{test_query}'")
    parser = EnhancedIntentParser()
    parsed = parser.parse(test_query)
    print_step("Parsed Intent", {
        "action": parsed.action,
        "target_phrase": parsed.target_phrase,
        "value": parsed.value,
        "confidence": parsed.confidence
    })
    
    # Take snapshot
    print_step("DOM/Accessibility Snapshot", f"URL: {url}")
    snapshot_start = time.time()
    snapshot = runner._snapshot(url)
    snapshot_time = time.time() - snapshot_start
    
    elements = snapshot.get('elements', [])
    print_step("Snapshot Results", {
        "total_elements": len(elements),
        "snapshot_time": f"{snapshot_time:.2f}s",
        "frame_url": snapshot.get('url', 'N/A'),
        "frame_hash": snapshot.get('frame_hash', 'N/A')
    })
    
    # Analyze element types
    element_types = {}
    interactive_count = 0
    text_nodes = 0
    for el in elements:
        tag = el.get('tag', 'unknown')
        element_types[tag] = element_types.get(tag, 0) + 1
        if el.get('interactive', False):
            interactive_count += 1
        if tag == '#text':
            text_nodes += 1
    
    print_step("Element Analysis", {
        "element_type_distribution": dict(sorted(element_types.items(), key=lambda x: x[1], reverse=True)[:10]),
        "interactive_elements": interactive_count,
        "text_nodes": text_nodes,
        "total_elements": len(elements)
    })
    
    # Check for hierarchy context
    if config.should_use_hierarchy():
        hierarchy_elements = [el for el in elements if 'context' in el and el['context'].get('hierarchy_path')]
        print_step("Hierarchy Context", {
            "elements_with_context": len(hierarchy_elements),
            "total_elements": len(elements),
            "context_coverage": f"{len(hierarchy_elements)/len(elements)*100:.1f}%" if elements else "0%"
        })
        
        # Show sample hierarchy context
        if hierarchy_elements:
            sample = hierarchy_elements[0]
            print_step("Sample Hierarchy Context", {
                "tag": sample.get('tag'),
                "text": sample.get('text', '')[:50] + '...',
                "hierarchy_path": sample['context'].get('hierarchy_path'),
                "depth": sample['context'].get('depth'),
                "has_children": sample['context'].get('has_children')
            })
    
    # Test element selection
    print_step("Element Selection", f"Query: '{test_query}'")
    query_start = time.time()
    result = runner._resolve_selector(test_query, snapshot)
    query_time = time.time() - query_start
    
    print_step("Selection Results", {
        "strategy": result.get('strategy', 'unknown'),
        "confidence": result.get('confidence', 0.0),
        "selected_selector": result.get('selector', 'N/A'),
        "query_time": f"{query_time:.2f}s",
        "candidates_found": len(result.get('candidates', []))
    })
    
    # Show top candidates
    candidates = result.get('candidates', [])
    if candidates:
        print_step("Top 5 Candidates", "Detailed analysis:")
        for i, candidate in enumerate(candidates[:5]):
            print(f"   {i+1}. Score: {candidate.get('score', 0.0):.3f}")
            print(f"      XPath: {candidate.get('xpath', 'N/A')}")
            print(f"      Text: '{candidate.get('text', '')[:50]}...'")
            print(f"      Tag: {candidate.get('tag', 'N/A')}")
            print(f"      Interactive: {candidate.get('interactive', False)}")
            print(f"      Reasons: {candidate.get('reasons', [])}")
            print()
    
    # Check for text duplication issues
    shop_elements = [el for el in elements if 'shop' in el.get('text', '').lower()]
    duplicated_texts = [el for el in shop_elements if el.get('text', '').count('Shop') > 1]
    
    print_step("Text Quality Check", {
        "shop_elements_found": len(shop_elements),
        "duplicated_texts": len(duplicated_texts),
        "text_quality": "GOOD" if len(duplicated_texts) == 0 else "ISSUES DETECTED"
    })
    
    if duplicated_texts:
        print_step("Duplicated Text Examples", "Issues found:")
        for i, el in enumerate(duplicated_texts[:3]):
            print(f"   {i+1}. Text: '{el.get('text', '')}'")
            print(f"      Tag: {el.get('tag', '')}")
            print(f"      XPath: {el.get('xpath', '')}")
    
    # Cleanup
    print_step("Cleanup", "Cleaning up resources...")
    runner.cleanup_models()
    runner._browser.close()
    runner._playwright.stop()
    print("   ✅ Cleanup completed")
    
    total_time = time.time() - start_time
    print_step("Mode Summary", {
        "mode": mode_name,
        "total_time": f"{total_time:.2f}s",
        "snapshot_time": f"{snapshot_time:.2f}s",
        "query_time": f"{query_time:.2f}s",
        "elements_processed": len(elements),
        "strategy_used": result.get('strategy', 'unknown'),
        "confidence": result.get('confidence', 0.0),
        "success": result.get('selector', '') != ''
    })
    
    return {
        "success": result.get('selector', '') != '',
        "total_time": total_time,
        "snapshot_time": snapshot_time,
        "query_time": query_time,
        "elements_count": len(elements),
        "strategy": result.get('strategy', 'unknown'),
        "confidence": result.get('confidence', 0.0),
        "selected_selector": result.get('selector', ''),
        "text_quality": len(duplicated_texts) == 0
    }

def main():
    """Run comprehensive tests for all 3 modes"""
    print_section("COMPREHENSIVE VERIZON FLOW TEST")
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
            result = test_mode(config["name"], config["env_vars"], test_query, test_url)
            results[config["name"]] = result
        except Exception as e:
            print(f"\n❌ ERROR in {config['name']}: {e}")
            import traceback
            traceback.print_exc()
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
                "text_quality": False
            }
    
    # Print final summary
    print_section("FINAL TEST SUMMARY")
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
        print(f"     Strategy: {result.get('strategy', 'unknown')}")
        print(f"     Confidence: {result.get('confidence', 0.0):.3f}")
        print(f"     Text Quality: {text_quality}")
        if result.get("selected_selector"):
            print(f"     Selected: {result.get('selected_selector', '')[:80]}...")
        if not result.get("success", False):
            all_passed = False
    
    print(f"\n🎯 OVERALL RESULT: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    # Performance comparison
    print_section("PERFORMANCE COMPARISON")
    for mode, result in results.items():
        if result.get("success", False):
            print(f"   {mode}: {result.get('total_time', 0):.2f}s total, {result.get('query_time', 0):.2f}s query")
    
    return results

if __name__ == "__main__":
    main()