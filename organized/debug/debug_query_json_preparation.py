#!/usr/bin/env python3
"""
Debug Query JSON Preparation Test - Comprehensive Version
Tests how user queries are parsed into target, intent, and query JSON
for various UI automation edge cases
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def test_query_json_preparation():
    """Test JSON preparation for various user queries"""
    
    print("🔍 QUERY JSON PREPARATION TEST")
    print("=" * 60)
    
    # Test script
    test_script = """
import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))
os.environ["HER_MODELS_DIR"] = str(Path.cwd() / "src" / "her" / "models")
os.environ["HER_CACHE_DIR"] = str(Path.cwd() / ".her_cache")

from her.runner import Runner

def test_queries():
    try:
        runner = Runner(headless=True)
        runner._ensure_browser()
        runner._page.goto("https://www.verizon.com/")
        
        snapshot = runner._snapshot("https://www.verizon.com/")
        elements = snapshot.get('elements', [])
        
        test_cases = [
            {"query": "click the login button", "expected_action": "click", "expected_target": "login button"},
            {"query": "find the search box", "expected_action": "search", "expected_target": "search box"},
            {"query": "fill in the email field", "expected_action": "type", "expected_target": "email field"},
            {"query": "submit the form", "expected_action": "submit", "expected_target": "form"},
            {"query": "click the red button with Submit text", "expected_action": "click", "expected_target": "red button with Submit text"},
            {"query": "type 'test@example.com' into email field", "expected_action": "type", "expected_target": "email field"},
            {"query": "select 'United States' from country dropdown", "expected_action": "select", "expected_target": "country dropdown"},
            {"query": "check the terms and conditions checkbox", "expected_action": "check", "expected_target": "terms and conditions checkbox"},
            {"query": "go to the about page", "expected_action": "navigate", "expected_target": "about page"},
            {"query": "hover over the product image", "expected_action": "hover", "expected_target": "product image"},
            {"query": "wait for the page to load", "expected_action": "wait", "expected_target": "page to load"},
            {"query": "verify the header is visible", "expected_action": "assert", "expected_target": "header is visible"},
            {"query": "click it", "expected_action": "click", "expected_target": "it"},
            {"query": "", "expected_action": "click", "expected_target": ""},
        ]
        
        results = []
        for i, test_case in enumerate(test_cases):
            query = test_case["query"]
            expected_action = test_case["expected_action"]
            expected_target = test_case["expected_target"]
            
            try:
                # Parse intent using the correct method
                intent = runner.intent.parse(query)
                
                # Check if results match expectations
                action_match = intent.action == expected_action
                target_match = intent.target_phrase == expected_target
                
                results.append({
                    "test": i + 1,
                    "query": query,
                    "action": intent.action,
                    "target": intent.target_phrase,
                    "args": intent.args,
                    "confidence": intent.confidence,
                    "expected_action": expected_action,
                    "expected_target": expected_target,
                    "action_match": action_match,
                    "target_match": target_match,
                    "success": True
                })
            except Exception as e:
                results.append({
                    "test": i + 1,
                    "query": query,
                    "error": str(e),
                    "success": False
                })
        
        print("SUCCESS")
        print(json.dumps(results, indent=2))
        print(f"ELEMENTS_COUNT:{len(elements)}")
        
    except Exception as e:
        print("ERROR")
        print(str(e))

if __name__ == "__main__":
    test_queries()
"""
    
    # Run test
    result = subprocess.run(
        [sys.executable, "-c", test_script],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent.parent
    )
    
    if "SUCCESS" in result.stdout:
        lines = result.stdout.strip().split('\n')
        json_start = False
        json_lines = []
        
        for line in lines:
            if line.startswith('[') or line.startswith('{'):
                json_start = True
            if json_start and not line.startswith("ELEMENTS_COUNT"):
                json_lines.append(line)
        
        if json_lines:
            try:
                data = json.loads('\n'.join(json_lines))
                
                print("Query Parsing Results:")
                print("-" * 60)
                
                successful_tests = [r for r in data if r.get("success")]
                failed_tests = [r for r in data if not r.get("success")]
                
                # Show successful cases
                for item in successful_tests:
                    print(f"Test {item['test']:2d}: '{item['query']}'")
                    print(f"   Action: {item['action']} {'✅' if item['action_match'] else '❌'} (expected: {item['expected_action']})")
                    print(f"   Target: {item['target']} {'✅' if item['target_match'] else '❌'} (expected: {item['expected_target']})")
                    print(f"   Args: {item['args']}")
                    print(f"   Confidence: {item['confidence']}")
                    print()
                
                # Show failed cases
                if failed_tests:
                    print("Failed Tests:")
                    print("-" * 30)
                    for item in failed_tests:
                        print(f"Test {item['test']:2d}: '{item['query']}' -> ERROR: {item['error']}")
                
                # Summary
                action_matches = [r for r in successful_tests if r.get("action_match")]
                target_matches = [r for r in successful_tests if r.get("target_match")]
                
                print("\n📊 SUMMARY")
                print("=" * 60)
                print(f"Total Tests: {len(data)}")
                print(f"Successful: {len(successful_tests)}")
                print(f"Failed: {len(failed_tests)}")
                print(f"Action Matches: {len(action_matches)}/{len(successful_tests)} ({len(action_matches)/len(successful_tests)*100:.1f}%)")
                print(f"Target Matches: {len(target_matches)}/{len(successful_tests)} ({len(target_matches)/len(successful_tests)*100:.1f}%)")
                
                # Find elements count
                for line in lines:
                    if line.startswith("ELEMENTS_COUNT:"):
                        count = line.split(":")[1]
                        print(f"Elements found: {count}")
                        break
                        
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
    else:
        print("❌ Test failed")
        print("Error output:", result.stderr)

if __name__ == "__main__":
    test_query_json_preparation()