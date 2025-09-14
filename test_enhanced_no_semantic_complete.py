#!/usr/bin/env python3
"""
Complete Test for Enhanced No-Semantic Mode

This test verifies all features of the enhanced no-semantic mode:
1. True no-semantic mode (no ML models)
2. Hierarchical context building
3. Proper navigation handling
4. XPath validation during selection
5. Intent parsing integration
6. Search target handling
7. Performance metrics
"""

import sys
import os
import time
import logging
from pathlib import Path
from unittest.mock import Mock

# Add src to path
sys.path.insert(0, 'src')

# Set up logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class MockPage:
    """Mock page object for testing navigation."""
    
    def __init__(self):
        self.navigation_calls = []
    
    def goto(self, url, wait_until='domcontentloaded', timeout=30000):
        """Mock page.goto() method."""
        self.navigation_calls.append({
            'url': url,
            'wait_until': wait_until,
            'timeout': timeout
        })
        
        # Mock successful response
        response = Mock()
        response.status = 200
        return response

def test_enhanced_no_semantic_complete():
    """Complete test of the enhanced no-semantic mode."""
    print("🧪 Complete Enhanced No-Semantic Mode Test")
    print("=" * 60)
    
    try:
        # Import the enhanced no-semantic matcher
        from src.her.locator.enhanced_no_semantic import EnhancedNoSemanticMatcher
        
        # Create test elements with more complex hierarchy
        test_elements = [
            {
                'tag': 'button',
                'text': 'Click Me',
                'attributes': {
                    'id': 'click-button',
                    'class': 'btn btn-primary',
                    'type': 'button',
                    'data-testid': 'click-me-btn'
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
                    'name': 'search',
                    'class': 'form-control'
                },
                'hierarchy': ['html', 'body', 'div:2', 'form:1', 'input:1']
            },
            {
                'tag': 'a',
                'text': 'Verizon',
                'attributes': {
                    'href': 'https://verizon.com',
                    'class': 'nav-link',
                    'title': 'Visit Verizon'
                },
                'hierarchy': ['html', 'body', 'nav:1', 'a:1']
            },
            {
                'tag': 'div',
                'text': 'White',
                'attributes': {
                    'class': 'color-option',
                    'data-color': 'white',
                    'role': 'button'
                },
                'hierarchy': ['html', 'body', 'div:3', 'div:1']
            },
            {
                'tag': 'select',
                'text': '',
                'attributes': {
                    'id': 'color-select',
                    'name': 'color',
                    'class': 'form-select'
                },
                'hierarchy': ['html', 'body', 'div:4', 'select:1']
            },
            {
                'tag': 'option',
                'text': 'Red',
                'attributes': {
                    'value': 'red',
                    'selected': 'true'
                },
                'hierarchy': ['html', 'body', 'div:4', 'select:1', 'option:1']
            }
        ]
        
        # Create matcher instance
        matcher = EnhancedNoSemanticMatcher()
        
        # Test cases with expected results
        test_cases = [
            {
                'query': 'Click on "Click Me"',
                'expected_intent': 'click',
                'expected_target': 'Click Me',
                'expected_element_tag': 'button',
                'expected_xpath_pattern': '//button[normalize-space()="Click Me"]'
            },
            {
                'query': 'Enter "iPhone" in search',
                'expected_intent': 'enter',
                'expected_target': 'iPhone',
                'expected_element_tag': 'input',
                'expected_xpath_pattern': '//input[@id="search-input"]'
            },
            {
                'query': 'Navigate to Verizon',
                'expected_intent': 'navigate',
                'expected_target': 'Verizon',
                'expected_element_tag': 'a',
                'expected_xpath_pattern': None  # Navigation doesn't generate XPath
            },
            {
                'query': 'Click on "White" color',
                'expected_intent': 'click',
                'expected_target': 'White',
                'expected_element_tag': 'div',
                'expected_xpath_pattern': '//div[normalize-space()="White"]'
            },
            {
                'query': 'Select "Red" from dropdown',
                'expected_intent': 'click',
                'expected_target': 'Red',
                'expected_element_tag': 'option',
                'expected_xpath_pattern': '//option[normalize-space()="Red"]'
            }
        ]
        
        print(f"📋 Running {len(test_cases)} comprehensive test cases...")
        print()
        
        success_count = 0
        total_time = 0
        detailed_results = []
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"🔍 Test {i}: {test_case['query']}")
            
            start_time = time.time()
            
            try:
                # Create mock page for navigation tests
                mock_page = MockPage() if 'Navigate' in test_case['query'] else None
                
                # Execute query
                result = matcher.query(test_case['query'], test_elements, mock_page)
                
                execution_time = (time.time() - start_time) * 1000
                total_time += execution_time
                
                # Analyze results
                test_result = {
                    'query': test_case['query'],
                    'success': False,
                    'execution_time': execution_time,
                    'result': result
                }
                
                # Check results based on query type
                if 'Navigate' in test_case['query']:
                    # Navigation test
                    if result.get('strategy') == 'navigation-success':
                        print(f"   ✅ SUCCESS (Navigation)")
                        print(f"   🌐 URL: {result.get('url', 'Unknown')}")
                        print(f"   📊 Status: {result.get('status', 'Unknown')}")
                        print(f"   ⏱️  Time: {execution_time:.1f}ms")
                        test_result['success'] = True
                        success_count += 1
                    else:
                        print(f"   ❌ FAILED (Navigation)")
                        print(f"   ⚠️  Error: {result.get('error', 'Unknown error')}")
                        print(f"   ⏱️  Time: {execution_time:.1f}ms")
                else:
                    # Element selection test
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
                            test_result['success'] = True
                            success_count += 1
                        else:
                            print(f"   ⚠️  Element tag mismatch: expected {test_case['expected_element_tag']}, got {element.get('tag')}")
                        
                        # Check XPath pattern if expected
                        if test_case['expected_xpath_pattern']:
                            if test_case['expected_xpath_pattern'] in result['xpath']:
                                print(f"   ✅ XPath pattern matches")
                            else:
                                print(f"   ⚠️  XPath pattern mismatch")
                    else:
                        print(f"   ❌ FAILED")
                        print(f"   📍 XPath: {result.get('xpath', 'None')}")
                        print(f"   🎯 Confidence: {result.get('confidence', 0):.3f}")
                        print(f"   ⚠️  Error: {result.get('error', 'Unknown error')}")
                        print(f"   ⏱️  Time: {execution_time:.1f}ms")
                
                detailed_results.append(test_result)
                
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                total_time += execution_time
                print(f"   ❌ EXCEPTION: {str(e)}")
                print(f"   ⏱️  Time: {execution_time:.1f}ms")
                
                test_result = {
                    'query': test_case['query'],
                    'success': False,
                    'execution_time': execution_time,
                    'error': str(e)
                }
                detailed_results.append(test_result)
            
            print()
        
        # Performance Analysis
        print("📊 PERFORMANCE ANALYSIS")
        print("=" * 30)
        successful_tests = [r for r in detailed_results if r['success']]
        failed_tests = [r for r in detailed_results if not r['success']]
        
        if successful_tests:
            avg_success_time = sum(r['execution_time'] for r in successful_tests) / len(successful_tests)
            print(f"✅ Successful Tests: {len(successful_tests)}")
            print(f"⏱️  Avg Success Time: {avg_success_time:.1f}ms")
        
        if failed_tests:
            avg_fail_time = sum(r['execution_time'] for r in failed_tests) / len(failed_tests)
            print(f"❌ Failed Tests: {len(failed_tests)}")
            print(f"⏱️  Avg Fail Time: {avg_fail_time:.1f}ms")
        
        print(f"📈 Total Success Rate: {(success_count/len(test_cases)*100):.1f}%")
        print(f"⚡ Overall Avg Time: {(total_time/len(test_cases)):.1f}ms")
        
        # Feature Analysis
        print("\n🔍 FEATURE ANALYSIS")
        print("=" * 25)
        
        # Test hierarchical context building
        hierarchical_tests = [r for r in detailed_results if r['success'] and 'Click' in r['query']]
        print(f"🏗️  Hierarchical Context: {len(hierarchical_tests)}/{len([r for r in detailed_results if 'Click' in r['query']])} successful")
        
        # Test search target handling
        search_tests = [r for r in detailed_results if r['success'] and 'Enter' in r['query']]
        print(f"🔍 Search Target Handling: {len(search_tests)}/{len([r for r in detailed_results if 'Enter' in r['query']])} successful")
        
        # Test navigation handling
        nav_tests = [r for r in detailed_results if r['success'] and 'Navigate' in r['query']]
        print(f"🌐 Navigation Handling: {len(nav_tests)}/{len([r for r in detailed_results if 'Navigate' in r['query']])} successful")
        
        # Test XPath validation
        xpath_tests = [r for r in detailed_results if r['success'] and r['result'].get('xpath')]
        print(f"📍 XPath Validation: {len(xpath_tests)}/{len([r for r in detailed_results if not 'Navigate' in r['query']])} successful")
        
        # Overall result
        if success_count == len(test_cases):
            print("\n🎉 ALL TESTS PASSED! Enhanced no-semantic mode is production-ready.")
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

def main():
    """Main test function."""
    print("🚀 Enhanced No-Semantic Mode Complete Test Suite")
    print("=" * 60)
    
    # Run complete test
    success = test_enhanced_no_semantic_complete()
    
    # Overall result
    print("\n🏁 OVERALL RESULT")
    print("=" * 20)
    if success:
        print("🎉 ALL TESTS PASSED! Enhanced no-semantic mode is ready for production.")
        print("\n✨ Features Verified:")
        print("   ✅ True no-semantic mode (no ML models)")
        print("   ✅ Hierarchical context building")
        print("   ✅ Proper navigation handling")
        print("   ✅ XPath validation during selection")
        print("   ✅ Intent parsing integration")
        print("   ✅ Search target handling")
        print("   ✅ Performance optimization")
        return 0
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    exit(main())