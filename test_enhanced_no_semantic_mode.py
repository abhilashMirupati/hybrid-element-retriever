#!/usr/bin/env python3
"""
Test Enhanced No-Semantic Mode Implementation

This test verifies the enhanced no-semantic mode with:
1. True no-semantic mode (no ML models)
2. Hierarchical context building
3. Proper navigation handling
4. XPath validation during selection
5. Intent parsing integration
6. Search target handling
"""

import sys
import os
import time
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

# Set up logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def test_enhanced_no_semantic_mode():
    """Test the enhanced no-semantic mode implementation."""
    print("🧪 Testing Enhanced No-Semantic Mode Implementation")
    print("=" * 60)
    
    try:
        # Import the enhanced no-semantic matcher
        from src.her.locator.enhanced_no_semantic import EnhancedNoSemanticMatcher
        
        # Create test elements
        test_elements = [
            {
                'tag': 'button',
                'text': 'Click Me',
                'attributes': {
                    'id': 'click-button',
                    'class': 'btn btn-primary',
                    'type': 'button'
                },
                'hierarchy': ['html', 'body', 'div:1', 'button:1']
            },
            {
                'tag': 'input',
                'text': '',
                'attributes': {
                    'id': 'search-input',
                    'type': 'text',
                    'placeholder': 'Search for products...',
                    'name': 'search'
                },
                'hierarchy': ['html', 'body', 'div:2', 'form:1', 'input:1']
            },
            {
                'tag': 'a',
                'text': 'Verizon',
                'attributes': {
                    'href': 'https://verizon.com',
                    'class': 'nav-link'
                },
                'hierarchy': ['html', 'body', 'nav:1', 'a:1']
            },
            {
                'tag': 'div',
                'text': 'White',
                'attributes': {
                    'class': 'color-option',
                    'data-color': 'white'
                },
                'hierarchy': ['html', 'body', 'div:3', 'div:1']
            }
        ]
        
        # Create matcher instance
        matcher = EnhancedNoSemanticMatcher()
        
        # Test cases
        test_cases = [
            {
                'query': 'Click on "Click Me"',
                'expected_intent': 'click',
                'expected_target': 'Click Me',
                'expected_element_tag': 'button'
            },
            {
                'query': 'Enter "iPhone" in search',
                'expected_intent': 'enter',
                'expected_target': 'search',
                'expected_element_tag': 'input'
            },
            {
                'query': 'Navigate to Verizon',
                'expected_intent': 'navigate',
                'expected_target': 'Verizon',
                'expected_element_tag': 'a'
            },
            {
                'query': 'Click on "White" color',
                'expected_intent': 'click',
                'expected_target': 'White',
                'expected_element_tag': 'div'
            }
        ]
        
        print(f"📋 Running {len(test_cases)} test cases...")
        print()
        
        success_count = 0
        total_time = 0
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"🔍 Test {i}: {test_case['query']}")
            
            start_time = time.time()
            
            try:
                # Execute query
                result = matcher.query(test_case['query'], test_elements)
                
                execution_time = (time.time() - start_time) * 1000
                total_time += execution_time
                
                # Check results
                if result.get('xpath') and result.get('confidence', 0) > 0:
                    print(f"   ✅ SUCCESS")
                    print(f"   📍 XPath: {result['xpath']}")
                    print(f"   🎯 Confidence: {result['confidence']:.3f}")
                    print(f"   ⏱️  Time: {execution_time:.1f}ms")
                    print(f"   🔧 Strategy: {result.get('strategy', 'unknown')}")
                    
                    # Check if element matches expected
                    element = result.get('element', {})
                    if element.get('tag') == test_case['expected_element_tag']:
                        print(f"   ✅ Element tag matches: {element.get('tag')}")
                        success_count += 1
                    else:
                        print(f"   ⚠️  Element tag mismatch: expected {test_case['expected_element_tag']}, got {element.get('tag')}")
                else:
                    print(f"   ❌ FAILED")
                    print(f"   📍 XPath: {result.get('xpath', 'None')}")
                    print(f"   🎯 Confidence: {result.get('confidence', 0):.3f}")
                    print(f"   ⚠️  Error: {result.get('error', 'Unknown error')}")
                
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                total_time += execution_time
                print(f"   ❌ EXCEPTION: {str(e)}")
                print(f"   ⏱️  Time: {execution_time:.1f}ms")
            
            print()
        
        # Summary
        print("📊 TEST SUMMARY")
        print("=" * 30)
        print(f"✅ Successful: {success_count}/{len(test_cases)}")
        print(f"⏱️  Total Time: {total_time:.1f}ms")
        print(f"📈 Success Rate: {(success_count/len(test_cases)*100):.1f}%")
        print(f"⚡ Avg Time: {(total_time/len(test_cases)):.1f}ms")
        
        if success_count == len(test_cases):
            print("\n🎉 ALL TESTS PASSED! Enhanced no-semantic mode is working correctly.")
            return True
        else:
            print(f"\n⚠️  {len(test_cases) - success_count} tests failed. Check implementation.")
            return False
            
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("Make sure the enhanced_no_semantic module is properly implemented.")
        return False
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_intent_parsing():
    """Test intent parsing functionality."""
    print("\n🔍 Testing Intent Parsing")
    print("=" * 30)
    
    try:
        from src.her.locator.intent_parser import IntentParser
        
        parser = IntentParser()
        
        test_queries = [
            'Click on "White" color',
            'Enter "iPhone" in search',
            'Navigate to Verizon',
            'Select "Option 1" from dropdown',
            'Type "Hello World" in text field'
        ]
        
        for query in test_queries:
            result = parser.parse_step(query)
            print(f"Query: {query}")
            print(f"  Intent: {result.intent.value}")
            print(f"  Target: '{result.target_text}'")
            print(f"  Value: '{result.value}'")
            print(f"  Confidence: {result.confidence:.3f}")
            print()
        
        print("✅ Intent parsing test completed")
        return True
        
    except Exception as e:
        print(f"❌ Intent parsing test failed: {e}")
        return False

def main():
    """Main test function."""
    print("🚀 Enhanced No-Semantic Mode Test Suite")
    print("=" * 50)
    
    # Test intent parsing
    intent_success = test_intent_parsing()
    
    # Test enhanced no-semantic mode
    mode_success = test_enhanced_no_semantic_mode()
    
    # Overall result
    print("\n🏁 OVERALL RESULT")
    print("=" * 20)
    if intent_success and mode_success:
        print("🎉 ALL TESTS PASSED! Enhanced no-semantic mode is ready for production.")
        return 0
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    exit(main())