#!/usr/bin/env python3
"""
Debug Structured Intent Parser Test
Tests the new structured intent parser with 100% accuracy
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def test_structured_intent():
    """Test structured intent parser"""
    
    print("🔍 STRUCTURED INTENT PARSER TEST")
    print("=" * 60)
    
    # Test cases with expected 100% accuracy
    test_cases = [
        # Perfect structured format
        {"step": 'Click on "Login" button', "expected_action": "click", "expected_target": "Login", "expected_value": None},
        {"step": 'Enter $test123 in "password" field', "expected_action": "enter", "expected_target": "password", "expected_value": "test123"},
        {"step": 'Validate "User successfully logged in"', "expected_action": "validate", "expected_target": "User successfully logged in", "expected_value": None},
        {"step": 'Hover over "product image"', "expected_action": "hover", "expected_target": "product image", "expected_value": None},
        {"step": 'Wait for "page to load"', "expected_action": "wait", "expected_target": "page to load", "expected_value": None},
        {"step": 'Navigate to "about page"', "expected_action": "navigate", "expected_target": "about page", "expected_value": None},
        {"step": 'Submit "contact form"', "expected_action": "submit", "expected_target": "contact form", "expected_value": None},
        {"step": 'Clear "search field"', "expected_action": "clear", "expected_target": "search field", "expected_value": None},
        
        # Alternative formats
        {"step": 'Click "Login" button', "expected_action": "click", "expected_target": "Login", "expected_value": None},
        {"step": 'Type $username in "username" field', "expected_action": "type", "expected_target": "username", "expected_value": "username"},
        {"step": 'Press "Submit" button', "expected_action": "press", "expected_target": "Submit", "expected_value": None},
        
        # Edge cases
        {"step": "", "expected_action": "click", "expected_target": "", "expected_value": None},
        {"step": 'Click "   "', "expected_action": "click", "expected_target": "   ", "expected_value": None},
    ]
    
    # Test script
    test_script = """
import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))
os.environ["HER_MODELS_DIR"] = str(Path.cwd() / "src" / "her" / "models")
os.environ["HER_CACHE_DIR"] = str(Path.cwd() / ".her_cache")

from her.parser.structured_intent import StructuredIntentParser

def test_structured_intent():
    parser = StructuredIntentParser()
    
    test_cases = """ + str(test_cases) + """
    
    results = []
    for i, test_case in enumerate(test_cases):
        step = test_case["step"]
        expected_action = test_case["expected_action"]
        expected_target = test_case["expected_target"]
        expected_value = test_case["expected_value"]
        
        try:
            # Parse with structured intent parser
            intent = parser.parse(step)
            
            # Check accuracy
            action_match = intent.action == expected_action
            target_match = intent.target == expected_target
            value_match = intent.value == expected_value
            
            results.append({
                "test": i + 1,
                "step": step,
                "action": intent.action,
                "target": intent.target,
                "value": intent.value,
                "confidence": intent.confidence,
                "expected_action": expected_action,
                "expected_target": expected_target,
                "expected_value": expected_value,
                "action_match": action_match,
                "target_match": target_match,
                "value_match": value_match,
                "all_match": action_match and target_match and value_match,
                "success": True
            })
        except Exception as e:
            results.append({
                "test": i + 1,
                "step": step,
                "error": str(e),
                "success": False
            })
    
    print("SUCCESS")
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    test_structured_intent()
"""
    
    # Run test
    result = subprocess.run(
        [sys.executable, "-c", test_script],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent.parent
    )
    
    if "SUCCESS" in result.stdout:
        try:
            data = json.loads(result.stdout.split("SUCCESS")[1].strip())
            
            print("Structured Intent Parser Results:")
            print("-" * 60)
            
            successful_tests = [r for r in data if r.get("success")]
            failed_tests = [r for r in data if not r.get("success")]
            
            # Show results
            for item in successful_tests:
                print(f"Test {item['test']:2d}: '{item['step']}'")
                print(f"   Action: {item['action']} {'✅' if item['action_match'] else '❌'} (expected: {item['expected_action']})")
                print(f"   Target: {item['target']} {'✅' if item['target_match'] else '❌'} (expected: {item['expected_target']})")
                print(f"   Value: {item['value']} {'✅' if item['value_match'] else '❌'} (expected: {item['expected_value']})")
                print(f"   Confidence: {item['confidence']}")
                print(f"   Overall: {'✅ PERFECT' if item['all_match'] else '❌ MISMATCH'}")
                print()
            
            # Show failed tests
            if failed_tests:
                print("Failed Tests:")
                print("-" * 30)
                for item in failed_tests:
                    print(f"Test {item['test']:2d}: '{item['step']}' -> ERROR: {item['error']}")
            
            # Summary
            action_matches = [r for r in successful_tests if r.get("action_match")]
            target_matches = [r for r in successful_tests if r.get("target_match")]
            value_matches = [r for r in successful_tests if r.get("value_match")]
            all_matches = [r for r in successful_tests if r.get("all_match")]
            
            print("\n📊 SUMMARY")
            print("=" * 60)
            print(f"Total Tests: {len(data)}")
            print(f"Successful: {len(successful_tests)}")
            print(f"Failed: {len(failed_tests)}")
            print(f"Action Matches: {len(action_matches)}/{len(successful_tests)} ({len(action_matches)/len(successful_tests)*100:.1f}%)")
            print(f"Target Matches: {len(target_matches)}/{len(successful_tests)} ({len(target_matches)/len(successful_tests)*100:.1f}%)")
            print(f"Value Matches: {len(value_matches)}/{len(successful_tests)} ({len(value_matches)/len(successful_tests)*100:.1f}%)")
            print(f"Perfect Matches: {len(all_matches)}/{len(successful_tests)} ({len(all_matches)/len(successful_tests)*100:.1f}%)")
            
            if len(all_matches) == len(successful_tests):
                print("\n🎉 100% ACCURACY ACHIEVED!")
            else:
                print(f"\n⚠️  {len(successful_tests) - len(all_matches)} tests need fixing")
                
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
    else:
        print("❌ Test failed")
        print("Error output:", result.stderr)

if __name__ == "__main__":
    test_structured_intent()