#!/usr/bin/env python3
"""
Test with proper mandatory target and value format
"""

import subprocess
import os
import time
import json
from datetime import datetime

def run_test_with_proper_format():
    """Test with proper mandatory target and value format"""
    print(f"\n{'='*80}")
    print(f"🔍 TESTING PROPER MANDATORY FORMAT")
    print(f"{'='*80}")
    
    # Test cases with proper format
    test_cases = [
        {
            "name": "Click with mandatory target",
            "query": 'Click on the "Shop" button',
            "expected_target": "Shop",
            "expected_action": "click"
        },
        {
            "name": "Enter with mandatory target and value",
            "query": 'Enter $test123 in the "password" field',
            "expected_target": "password",
            "expected_action": "enter",
            "expected_value": "test123"
        },
        {
            "name": "Set with mandatory target and value",
            "query": 'Set the "username" field to $john_doe',
            "expected_target": "username",
            "expected_action": "set",
            "expected_value": "john_doe"
        },
        {
            "name": "Validate with mandatory target",
            "query": 'Validate that "Welcome" message is displayed',
            "expected_target": "Welcome",
            "expected_action": "validate"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n{'='*60}")
        print(f"🧪 TEST: {test_case['name']}")
        print(f"{'='*60}")
        print(f"Query: '{test_case['query']}'")
        
        # Test the parsing
        test_script = f"""
import os
import sys
sys.path.insert(0, 'src')

from her.parser.enhanced_intent import EnhancedIntentParser

try:
    parser = EnhancedIntentParser()
    parsed = parser.parse('{test_case['query']}')
    
    print(f"✅ Parsed successfully:")
    print(f"   Action: '{{parsed.action}}'")
    print(f"   Target: '{{parsed.target_phrase}}'")
    print(f"   Value: '{{parsed.value}}'")
    print(f"   Confidence: {{parsed.confidence}}")
    
    # Check if parsing matches expectations
    action_match = parsed.action == '{test_case['expected_action']}'
    target_match = parsed.target_phrase == '{test_case['expected_target']}'
    value_match = True
    if 'expected_value' in test_case:
        value_match = parsed.value == '{test_case['expected_value']}'
    
    print(f"\\n🎯 VALIDATION:")
    print(f"   Action match: {'✅' if action_match else '❌'} (expected: {test_case['expected_action']})")
    print(f"   Target match: {'✅' if target_match else '❌'} (expected: {test_case['expected_target']})")
    if 'expected_value' in test_case:
        print(f"   Value match: {'✅' if value_match else '❌'} (expected: {test_case['expected_value']})")
    
    all_match = action_match and target_match and value_match
    print(f"   Overall: {'✅ PASS' if all_match else '❌ FAIL'}")
    
except Exception as e:
    print(f"❌ ERROR: {{e}}")
    import traceback
    traceback.print_exc()
"""
        
        # Run the test
        process = subprocess.run(['python', '-c', test_script], 
                               capture_output=True, text=True, 
                               env=os.environ.copy())
        
        print(process.stdout)
        if process.stderr:
            print("STDERR:", process.stderr)

def run_element_selection_test():
    """Test element selection with proper Shop button query"""
    print(f"\n{'='*80}")
    print(f"🔍 TESTING ELEMENT SELECTION WITH PROPER QUERY")
    print(f"{'='*80}")
    
    test_script = f"""
import os
import sys
sys.path.insert(0, 'src')

# Set environment variables
os.environ['HER_CANONICAL_MODE'] = 'both'
os.environ['HER_USE_HIERARCHY'] = 'false'
os.environ['HER_USE_TWO_STAGE'] = 'false'

from her.runner import Runner
from her.parser.enhanced_intent import EnhancedIntentParser

try:
    print("🔍 Testing with proper Shop button query...")
    
    # Initialize
    runner = Runner()
    print("✅ Runner initialized")
    
    # Parse the proper query
    parser = EnhancedIntentParser()
    query = 'Click on the "Shop" button'
    parsed = parser.parse(query)
    
    print(f"\\n📋 PARSED QUERY:")
    print(f"   Original: '{query}'")
    print(f"   Action: '{parsed.action}'")
    print(f"   Target: '{parsed.target_phrase}'")
    print(f"   Value: '{parsed.value}'")
    
    # Take snapshot
    print("\\n📸 Taking snapshot...")
    snapshot = runner._snapshot('https://www.verizon.com/')
    elements = snapshot.get('elements', [])
    print(f"   Found {len(elements)} elements")
    
    # Find Shop buttons specifically
    shop_buttons = []
    for el in elements:
        text = el.get('text', '').lower()
        aria_label = el.get('attrs', {{}}).get('aria-label', '').lower()
        if 'shop' in text or 'shop' in aria_label:
            if el.get('interactive', False) and el.get('tag') == 'BUTTON':
                shop_buttons.append(el)
    
    print(f"\\n🔍 FOUND {len(shop_buttons)} INTERACTIVE SHOP BUTTONS:")
    for i, btn in enumerate(shop_buttons):
        print(f"   {i+1}. Text: '{btn.get('text', '')}'")
        print(f"      Aria-label: '{btn.get('attrs', {}).get('aria-label', '')}'")
        print(f"      XPath: {btn.get('xpath', '')}")
        print(f"      Interactive: {btn.get('interactive', False)}")
        print()
    
    # Test element selection
    print("🎯 Testing element selection...")
    result = runner._resolve_selector(query, snapshot)
    
    print(f"\\n📊 SELECTION RESULTS:")
    print(f"   Strategy: {result.get('strategy', 'unknown')}")
    print(f"   Confidence: {result.get('confidence', 0.0):.3f}")
    print(f"   Selected: {result.get('selector', 'N/A')}")
    
    # Check if it selected a Shop button
    selected_selector = result.get('selector', '')
    is_shop_button = 'shop' in selected_selector.lower() and 'close' not in selected_selector.lower()
    
    print(f"\\n✅ SELECTION VALIDATION:")
    print(f"   Selected Shop button: {'✅ YES' if is_shop_button else '❌ NO'}")
    print(f"   Avoided Close button: {'✅ YES' if 'close' not in selected_selector.lower() else '❌ NO'}")
    
    # Show top candidates
    candidates = result.get('candidates', [])
    if candidates:
        print(f"\\n🏆 TOP 5 CANDIDATES:")
        for i, candidate in enumerate(candidates[:5]):
            text = candidate.get('text', '')
            xpath = candidate.get('xpath', '')
            score = candidate.get('score', 0.0)
            is_shop = 'shop' in text.lower() and 'close' not in text.lower()
            print(f"   {i+1}. Score: {score:.3f} | Shop: {'✅' if is_shop else '❌'} | '{text[:50]}...'")
    
    # Cleanup
    runner.cleanup_models()
    runner._browser.close()
    runner._playwright.stop()
    
except Exception as e:
    print(f"❌ ERROR: {{e}}")
    import traceback
    traceback.print_exc()
"""
    
    # Run the test
    process = subprocess.run(['python', '-c', test_script], 
                           capture_output=True, text=True, 
                           env=os.environ.copy())
    
    print(process.stdout)
    if process.stderr:
        print("STDERR:", process.stderr)

def main():
    """Run all tests"""
    print(f"🚀 STARTING PROPER FORMAT TESTS")
    print(f"Started at: {datetime.now().isoformat()}")
    
    # Test 1: Parsing with proper format
    run_test_with_proper_format()
    
    # Test 2: Element selection with proper query
    run_element_selection_test()
    
    print(f"\n🏁 TESTS COMPLETED")
    print(f"Finished at: {datetime.now().isoformat()}")

if __name__ == "__main__":
    main()