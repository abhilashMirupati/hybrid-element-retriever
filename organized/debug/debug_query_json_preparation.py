#!/usr/bin/env python3
"""
Debug Query JSON Preparation Test
Tests how user queries are parsed into target, intent, and query JSON
for various UI automation edge cases
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

def test_query_json_preparation():
    """Test JSON preparation for various user queries"""
    
    # Set environment variables
    os.environ["HER_MODELS_DIR"] = str(Path(__file__).parent.parent.parent / "src" / "her" / "models")
    os.environ["HER_CACHE_DIR"] = str(Path(__file__).parent.parent.parent / ".her_cache")
    
    # Test cases covering various UI automation scenarios
    test_cases = [
        # Basic element selection
        {
            "query": "click the login button",
            "expected_intent": "click",
            "expected_target": "button",
            "description": "Basic button click"
        },
        {
            "query": "find the search box",
            "expected_intent": "find",
            "expected_target": "input",
            "description": "Input field search"
        },
        {
            "query": "select the dropdown menu",
            "expected_intent": "select",
            "expected_target": "select",
            "description": "Dropdown selection"
        },
        
        # Form interactions
        {
            "query": "fill in the email field with test@example.com",
            "expected_intent": "fill",
            "expected_target": "input",
            "description": "Form field filling"
        },
        {
            "query": "submit the contact form",
            "expected_intent": "submit",
            "expected_target": "form",
            "description": "Form submission"
        },
        {
            "query": "clear the password field",
            "expected_intent": "clear",
            "expected_target": "input",
            "description": "Field clearing"
        },
        
        # Navigation and links
        {
            "query": "go to the about page",
            "expected_intent": "navigate",
            "expected_target": "link",
            "description": "Page navigation"
        },
        {
            "query": "click the home link",
            "expected_intent": "click",
            "expected_target": "link",
            "description": "Link clicking"
        },
        {
            "query": "open the menu",
            "expected_intent": "open",
            "expected_target": "menu",
            "description": "Menu opening"
        },
        
        # Complex interactions
        {
            "query": "drag the slider to 50%",
            "expected_intent": "drag",
            "expected_target": "slider",
            "description": "Slider interaction"
        },
        {
            "query": "check the terms and conditions checkbox",
            "expected_intent": "check",
            "expected_target": "checkbox",
            "description": "Checkbox interaction"
        },
        {
            "query": "uncheck the newsletter subscription",
            "expected_intent": "uncheck",
            "expected_target": "checkbox",
            "description": "Checkbox unchecking"
        },
        
        # Text and content
        {
            "query": "find text containing 'Verizon'",
            "expected_intent": "find",
            "expected_target": "text",
            "description": "Text content search"
        },
        {
            "query": "get the page title",
            "expected_intent": "get",
            "expected_target": "title",
            "description": "Title extraction"
        },
        {
            "query": "read the error message",
            "expected_intent": "read",
            "expected_target": "text",
            "description": "Error message reading"
        },
        
        # Edge cases and complex queries
        {
            "query": "click the red button with 'Submit' text",
            "expected_intent": "click",
            "expected_target": "button",
            "description": "Multi-attribute element selection"
        },
        {
            "query": "find the input field for credit card number",
            "expected_intent": "find",
            "expected_target": "input",
            "description": "Specific field identification"
        },
        {
            "query": "select the option 'United States' from country dropdown",
            "expected_intent": "select",
            "expected_target": "option",
            "description": "Specific option selection"
        },
        {
            "query": "hover over the product image",
            "expected_intent": "hover",
            "expected_target": "img",
            "description": "Hover interaction"
        },
        {
            "query": "double-click the file name",
            "expected_intent": "double-click",
            "expected_target": "text",
            "description": "Double-click interaction"
        },
        {
            "query": "right-click on the image",
            "expected_intent": "right-click",
            "expected_target": "img",
            "description": "Right-click interaction"
        },
        
        # Ambiguous queries
        {
            "query": "click it",
            "expected_intent": "click",
            "expected_target": "element",
            "description": "Ambiguous element reference"
        },
        {
            "query": "find something",
            "expected_intent": "find",
            "expected_target": "element",
            "description": "Vague search query"
        },
        {
            "query": "do something",
            "expected_intent": "interact",
            "expected_target": "element",
            "description": "Very vague query"
        },
        
        # Error handling
        {
            "query": "",
            "expected_intent": "unknown",
            "expected_target": "element",
            "description": "Empty query"
        },
        {
            "query": "   ",
            "expected_intent": "unknown",
            "expected_target": "element",
            "description": "Whitespace-only query"
        },
        {
            "query": "click the non-existent element",
            "expected_intent": "click",
            "expected_target": "element",
            "description": "Non-existent element query"
        }
    ]
    
    print("🔍 QUERY JSON PREPARATION TEST")
    print("=" * 60)
    print(f"Testing {len(test_cases)} query scenarios...")
    print()
    
    # Test each query
    results = []
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i:2d}: {test_case['description']}")
        print(f"Query: '{test_case['query']}'")
        
        try:
            # Create test script
            test_script = f"""
import os
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path.cwd() / "src"))

# Set environment variables
os.environ["HER_MODELS_DIR"] = str(Path.cwd() / "src" / "her" / "models")
os.environ["HER_CACHE_DIR"] = str(Path.cwd() / ".her_cache")

from her.runner import Runner
from her.pipeline import HybridPipeline

def test_query_parsing():
    try:
        # Initialize runner
        runner = Runner(headless=True)
        
        # Get a sample page for testing
        runner._ensure_browser()
        runner._page.goto("https://www.verizon.com/")
        
        # Get canonical tree
        snapshot = runner._snapshot("https://www.verizon.com/")
        elements = snapshot.get('elements', [])
        
        if not elements:
            return {{
                "error": "No elements found in snapshot",
                "elements_count": 0
            }}
        
        # Test query parsing
        query = "{test_case['query']}"
        
        # Parse intent and target
        intent_parser = runner.intent
        parsed_intent = intent_parser.parse_intent(query)
        parsed_target = intent_parser.parse_target(query)
        
        # Prepare query JSON (simulate what pipeline.query does)
        query_json = {{
            "user_intent": parsed_intent,
            "target": parsed_target,
            "query": query,
            "elements_count": len(elements)
        }}
        
        return {{
            "success": True,
            "query_json": query_json,
            "elements_count": len(elements)
        }}
        
    except Exception as e:
        return {{
            "error": str(e),
            "success": False
        }}

if __name__ == "__main__":
    result = test_query_parsing()
    print(json.dumps(result, indent=2))
"""
            
            # Run test in subprocess
            result = subprocess.run(
                [sys.executable, "-c", test_script],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent
            )
            
            if result.returncode == 0:
                try:
                    data = json.loads(result.stdout.strip())
                    if data.get("success"):
                        query_json = data["query_json"]
                        elements_count = data["elements_count"]
                        
                        print(f"✅ Intent: {query_json['user_intent']}")
                        print(f"✅ Target: {query_json['target']}")
                        print(f"✅ Elements: {elements_count}")
                        
                        # Check if results match expectations
                        intent_match = query_json['user_intent'] == test_case['expected_intent']
                        target_match = query_json['target'] == test_case['expected_target']
                        
                        if intent_match and target_match:
                            print("✅ EXPECTED vs ACTUAL: MATCH")
                        else:
                            print("❌ EXPECTED vs ACTUAL: MISMATCH")
                            print(f"   Expected intent: {test_case['expected_intent']}")
                            print(f"   Expected target: {test_case['expected_target']}")
                        
                        results.append({
                            "test": i,
                            "query": test_case['query'],
                            "success": True,
                            "intent_match": intent_match,
                            "target_match": target_match,
                            "parsed_intent": query_json['user_intent'],
                            "parsed_target": query_json['target'],
                            "elements_count": elements_count
                        })
                    else:
                        print(f"❌ Error: {data.get('error', 'Unknown error')}")
                        results.append({
                            "test": i,
                            "query": test_case['query'],
                            "success": False,
                            "error": data.get('error', 'Unknown error')
                        })
                except json.JSONDecodeError:
                    print(f"❌ JSON decode error: {result.stdout}")
                    results.append({
                        "test": i,
                        "query": test_case['query'],
                        "success": False,
                        "error": "JSON decode error"
                    })
            else:
                print(f"❌ Subprocess error: {result.stderr}")
                results.append({
                    "test": i,
                    "query": test_case['query'],
                    "success": False,
                    "error": result.stderr
                })
        
        except Exception as e:
            print(f"❌ Test error: {e}")
            results.append({
                "test": i,
                "query": test_case['query'],
                "success": False,
                "error": str(e)
            })
        
        print("-" * 60)
    
    # Summary
    print("\n📊 QUERY JSON PREPARATION SUMMARY")
    print("=" * 60)
    
    successful_tests = [r for r in results if r.get("success")]
    failed_tests = [r for r in results if not r.get("success")]
    
    print(f"Total Tests: {len(results)}")
    print(f"Successful: {len(successful_tests)}")
    print(f"Failed: {len(failed_tests)}")
    print()
    
    if successful_tests:
        intent_matches = [r for r in successful_tests if r.get("intent_match")]
        target_matches = [r for r in successful_tests if r.get("target_match")]
        
        print(f"Intent Matches: {len(intent_matches)}/{len(successful_tests)} ({len(intent_matches)/len(successful_tests)*100:.1f}%)")
        print(f"Target Matches: {len(target_matches)}/{len(successful_tests)} ({len(target_matches)/len(successful_tests)*100:.1f}%)")
        print()
        
        # Show successful cases
        print("✅ SUCCESSFUL CASES:")
        for result in successful_tests:
            print(f"  {result['test']:2d}. '{result['query']}'")
            print(f"      Intent: {result['parsed_intent']} | Target: {result['parsed_target']}")
            print(f"      Elements: {result['elements_count']}")
    
    if failed_tests:
        print("\n❌ FAILED CASES:")
        for result in failed_tests:
            print(f"  {result['test']:2d}. '{result['query']}'")
            print(f"      Error: {result['error']}")
    
    print(f"\n🎯 QUERY JSON PREPARATION TEST COMPLETED")
    print(f"Success Rate: {len(successful_tests)}/{len(results)} ({len(successful_tests)/len(results)*100:.1f}%)")

if __name__ == "__main__":
    test_query_json_preparation()