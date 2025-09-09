#!/usr/bin/env python3
"""
Simple test for proper mandatory target and value format
"""

import os
import sys
sys.path.insert(0, 'src')

from her.parser.enhanced_intent import EnhancedIntentParser

def test_parsing():
    """Test parsing with proper format"""
    print("🧪 TESTING PARSING WITH PROPER FORMAT")
    print("=" * 50)
    
    test_cases = [
        {
            "query": 'Click on the "Shop" button',
            "expected_action": "click",
            "expected_target": "Shop",
            "expected_value": None
        },
        {
            "query": 'Enter $test123 in the "password" field',
            "expected_action": "enter",
            "expected_target": "password",
            "expected_value": "test123"
        },
        {
            "query": 'Set the "username" field to $john_doe',
            "expected_action": "set",
            "expected_target": "username",
            "expected_value": "john_doe"
        },
        {
            "query": 'Validate that "Welcome" message is displayed',
            "expected_action": "validate",
            "expected_target": "Welcome",
            "expected_value": None
        }
    ]
    
    parser = EnhancedIntentParser()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: '{test_case['query']}'")
        print("-" * 40)
        
        try:
            parsed = parser.parse(test_case['query'])
            
            print(f"   ✅ Parsed successfully:")
            print(f"      Action: '{parsed.action}'")
            print(f"      Target: '{parsed.target_phrase}'")
            print(f"      Value: '{parsed.value}'")
            print(f"      Confidence: {parsed.confidence}")
            
            # Check matches
            action_match = parsed.action == test_case['expected_action']
            target_match = parsed.target_phrase == test_case['expected_target']
            value_match = parsed.value == test_case['expected_value']
            
            print(f"\n   🎯 VALIDATION:")
            print(f"      Action: {'✅' if action_match else '❌'} (expected: {test_case['expected_action']})")
            print(f"      Target: {'✅' if target_match else '❌'} (expected: {test_case['expected_target']})")
            print(f"      Value: {'✅' if value_match else '❌'} (expected: {test_case['expected_value']})")
            
            all_match = action_match and target_match and value_match
            print(f"      Overall: {'✅ PASS' if all_match else '❌ FAIL'}")
            
        except Exception as e:
            print(f"   ❌ ERROR: {e}")

def test_element_selection():
    """Test element selection with proper Shop button query"""
    print("\n\n🎯 TESTING ELEMENT SELECTION")
    print("=" * 50)
    
    try:
        from her.runner import Runner
        
        # Set environment variables
        os.environ['HER_CANONICAL_MODE'] = 'both'
        os.environ['HER_USE_HIERARCHY'] = 'false'
        os.environ['HER_USE_TWO_STAGE'] = 'false'
        
        print("1. Initializing runner...")
        runner = Runner()
        print("   ✅ Runner initialized")
        
        print("\n2. Parsing proper query...")
        parser = EnhancedIntentParser()
        query = 'Click on the "Shop" button'
        parsed = parser.parse(query)
        
        print(f"   Query: '{query}'")
        print(f"   Action: '{parsed.action}'")
        print(f"   Target: '{parsed.target_phrase}'")
        
        print("\n3. Taking snapshot...")
        snapshot = runner._snapshot('https://www.verizon.com/')
        elements = snapshot.get('elements', [])
        print(f"   Found {len(elements)} elements")
        
        print("\n4. Finding Shop buttons...")
        shop_buttons = []
        for el in elements:
            text = el.get('text', '').lower()
            aria_label = el.get('attrs', {}).get('aria-label', '').lower()
            if 'shop' in text or 'shop' in aria_label:
                if el.get('interactive', False) and el.get('tag') == 'BUTTON':
                    shop_buttons.append(el)
        
        print(f"   Found {len(shop_buttons)} interactive Shop buttons:")
        for i, btn in enumerate(shop_buttons):
            print(f"      {i+1}. Text: '{btn.get('text', '')}'")
            print(f"         Aria-label: '{btn.get('attrs', {}).get('aria-label', '')}'")
            print(f"         XPath: {btn.get('xpath', '')}")
        
        print("\n5. Testing element selection...")
        result = runner._resolve_selector(query, snapshot)
        
        print(f"   Strategy: {result.get('strategy', 'unknown')}")
        print(f"   Confidence: {result.get('confidence', 0.0):.3f}")
        print(f"   Selected: {result.get('selector', 'N/A')}")
        
        # Check if it selected a Shop button (not Close)
        selected_selector = result.get('selector', '')
        is_shop_button = 'shop' in selected_selector.lower() and 'close' not in selected_selector.lower()
        
        print(f"\n   🎯 SELECTION VALIDATION:")
        print(f"      Selected Shop button: {'✅ YES' if is_shop_button else '❌ NO'}")
        print(f"      Avoided Close button: {'✅ YES' if 'close' not in selected_selector.lower() else '❌ NO'}")
        
        # Show top candidates
        candidates = result.get('candidates', [])
        if candidates:
            print(f"\n   🏆 TOP 5 CANDIDATES:")
            for i, candidate in enumerate(candidates[:5]):
                text = candidate.get('text', '')
                score = candidate.get('score', 0.0)
                is_shop = 'shop' in text.lower() and 'close' not in text.lower()
                print(f"      {i+1}. Score: {score:.3f} | Shop: {'✅' if is_shop else '❌'} | '{text[:50]}...'")
        
        # Cleanup
        print("\n6. Cleaning up...")
        runner.cleanup_models()
        runner._browser.close()
        runner._playwright.stop()
        print("   ✅ Cleanup completed")
        
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 TESTING PROPER MANDATORY FORMAT")
    print("=" * 60)
    
    # Test 1: Parsing
    test_parsing()
    
    # Test 2: Element selection
    test_element_selection()
    
    print("\n🏁 TESTS COMPLETED")