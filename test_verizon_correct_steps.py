#!/usr/bin/env python3
"""
Test Verizon Flow with Correct Steps

This test runs the EXACT Verizon steps requested by the user:
1) Navigate to Verizon page "https://www.verizon.com/"
2) Click on "Phones" button
3) Click on "Apple" filter
4) Click on "Apple IPhone 17" device
5) Validate it landed on "https://www.verizon.com/smartphones/apple-iphone-17/"
6) Validate "Apple iPhone 17" text on pdp page
7) Click on "White" color

For each step, provides:
- Canonical element tree
- XPath used
- MarkupLM input values
- MarkupLM output
"""

import sys
import os
import time
import logging
from pathlib import Path
from typing import Dict, Any
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
        self.current_url = "https://www.verizon.com/"
    
    def goto(self, url, wait_until='domcontentloaded', timeout=30000):
        """Mock page.goto() method."""
        self.navigation_calls.append({
            'url': url,
            'wait_until': wait_until,
            'timeout': timeout
        })
        self.current_url = url
        
        # Mock successful response
        response = Mock()
        response.status = 200
        return response
    
    def locator(self, xpath):
        """Mock page.locator() method."""
        locator = Mock()
        locator.count.return_value = 1  # Assume element exists
        return locator

def test_verizon_correct_steps():
    """Test the EXACT Verizon steps requested by the user."""
    print("🚀 Testing Verizon Flow with CORRECT Steps")
    print("=" * 60)
    
    try:
        # Import the enhanced no-semantic matcher
        from src.her.locator.enhanced_no_semantic import EnhancedNoSemanticMatcher
        from src.her.locator.html_hierarchy_builder import HTMLHierarchyBuilder
        
        # Create Verizon website elements
        verizon_elements = [
            # Navigation elements
            {
                'tag': 'a',
                'text': 'Verizon',
                'attributes': {
                    'href': 'https://www.verizon.com/',
                    'class': 'nav-link',
                    'title': 'Visit Verizon'
                },
                'hierarchy': ['html', 'body', 'nav:1', 'a:1']
            },
            # Phones button
            {
                'tag': 'button',
                'text': 'Phones',
                'attributes': {
                    'id': 'phones-button',
                    'class': 'nav-button',
                    'data-testid': 'phones-nav'
                },
                'hierarchy': ['html', 'body', 'nav:1', 'button:1']
            },
            # Apple filter
            {
                'tag': 'button',
                'text': 'Apple',
                'attributes': {
                    'id': 'apple-filter',
                    'class': 'filter-btn',
                    'data-filter': 'apple'
                },
                'hierarchy': ['html', 'body', 'div:2', 'div:1', 'button:1']
            },
            # Apple iPhone 17 device
            {
                'tag': 'div',
                'text': 'Apple iPhone 17',
                'attributes': {
                    'class': 'product-item',
                    'data-product': 'apple-iphone-17',
                    'data-testid': 'iphone-17'
                },
                'hierarchy': ['html', 'body', 'div:3', 'div:1']
            },
            # White color option
            {
                'tag': 'div',
                'text': 'White',
                'attributes': {
                    'class': 'color-option',
                    'data-color': 'white',
                    'role': 'button'
                },
                'hierarchy': ['html', 'body', 'div:4', 'div:1']
            },
            # PDP page elements
            {
                'tag': 'h1',
                'text': 'Apple iPhone 17',
                'attributes': {
                    'class': 'product-title',
                    'data-testid': 'product-title'
                },
                'hierarchy': ['html', 'body', 'div:5', 'h1:1']
            }
        ]
        
        # Create matcher and HTML builder
        matcher = EnhancedNoSemanticMatcher()
        html_builder = HTMLHierarchyBuilder(max_tokens=512)
        
        # Create mock page
        mock_page = MockPage()
        
        # EXACT test steps as requested
        test_steps = [
            'Navigate to Verizon page "https://www.verizon.com/"',
            'Click on "Phones" button',
            'Click on "Apple" filter',
            'Click on "Apple iPhone 17" device',
            'Validate it landed on "https://www.verizon.com/smartphones/apple-iphone-17/"',
            'Validate "Apple iPhone 17" text on pdp page',
            'Click on "White" color'
        ]
        
        print(f"📋 Running {len(test_steps)} EXACT Verizon test steps...")
        print()
        
        results = []
        total_time = 0
        
        for i, step in enumerate(test_steps, 1):
            print(f"🔍 Step {i}: {step}")
            print("-" * 50)
            
            start_time = time.time()
            
            try:
                # Execute query
                result = matcher.query(step, verizon_elements, mock_page)
                
                execution_time = (time.time() - start_time) * 1000
                total_time += execution_time
                
                # Get canonical element tree
                element = result.get('element', {})
                canonical_tree = get_canonical_element_tree(element)
                
                # Get XPath used
                xpath = result.get('xpath', 'N/A')
                
                # Get MarkupLM input/output if available
                markup_input = get_markup_input(element, html_builder)
                markup_output = get_markup_output(result)
                
                # Display results
                success = result.get('xpath') is not None or result.get('strategy') == 'navigation-success'
                confidence = result.get('confidence', 0.0)
                strategy = result.get('strategy', 'unknown')
                
                if success:
                    print(f"   ✅ SUCCESS")
                    print(f"   📍 XPath: {xpath}")
                    print(f"   🎯 Confidence: {confidence:.3f}")
                    print(f"   🔧 Strategy: {strategy}")
                    print(f"   ⏱️  Time: {execution_time:.1f}ms")
                else:
                    print(f"   ❌ FAILED")
                    print(f"   📍 XPath: {xpath}")
                    print(f"   🎯 Confidence: {confidence:.3f}")
                    print(f"   ⚠️  Error: {result.get('error', 'Unknown error')}")
                    print(f"   ⏱️  Time: {execution_time:.1f}ms")
                
                # Display canonical element tree
                print(f"   🌳 Canonical Element Tree:")
                for line in canonical_tree.split('\n'):
                    print(f"      {line}")
                
                # Display MarkupLM input
                print(f"   📥 MarkupLM Input:")
                for key, value in markup_input.items():
                    if key == 'html':
                        print(f"      {key}: {value[:100]}..." if len(str(value)) > 100 else f"      {key}: {value}")
                    else:
                        print(f"      {key}: {value}")
                
                # Display MarkupLM output
                print(f"   📤 MarkupLM Output:")
                for key, value in markup_output.items():
                    print(f"      {key}: {value}")
                
                results.append({
                    'step': step,
                    'success': success,
                    'xpath': xpath,
                    'confidence': confidence,
                    'strategy': strategy,
                    'execution_time': execution_time,
                    'canonical_tree': canonical_tree,
                    'markup_input': markup_input,
                    'markup_output': markup_output,
                    'result': result
                })
                
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                total_time += execution_time
                print(f"   ❌ EXCEPTION: {str(e)}")
                print(f"   ⏱️  Time: {execution_time:.1f}ms")
                
                results.append({
                    'step': step,
                    'success': False,
                    'xpath': 'N/A',
                    'confidence': 0.0,
                    'strategy': 'exception',
                    'execution_time': execution_time,
                    'error': str(e)
                })
            
            print()
        
        # Summary
        successful_steps = [r for r in results if r['success']]
        failed_steps = [r for r in results if not r['success']]
        
        print("📊 VERIZON FLOW TEST SUMMARY")
        print("=" * 40)
        print(f"✅ Successful Steps: {len(successful_steps)}/{len(test_steps)}")
        print(f"❌ Failed Steps: {len(failed_steps)}/{len(test_steps)}")
        print(f"📈 Success Rate: {(len(successful_steps)/len(test_steps)*100):.1f}%")
        print(f"⏱️  Total Time: {total_time:.1f}ms")
        print(f"⚡ Avg Time per Step: {(total_time/len(test_steps)):.1f}ms")
        
        # Detailed XPath and Canonical Tree Summary
        print("\n🔍 DETAILED XPATH AND CANONICAL TREE SUMMARY")
        print("=" * 55)
        for i, result in enumerate(results, 1):
            status = "✅" if result['success'] else "❌"
            print(f"{status} Step {i}: {result['step']}")
            print(f"   XPath: {result['xpath']}")
            if 'canonical_tree' in result:
                print(f"   Canonical Tree: {result['canonical_tree'][:100]}...")
            print()
        
        return len(successful_steps) == len(test_steps)
            
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def get_canonical_element_tree(element: Dict[str, Any]) -> str:
    """Get canonical element tree representation."""
    if not element:
        return "No element found"
    
    tag = element.get('tag', 'unknown')
    text = element.get('text', '')
    attrs = element.get('attributes', {})
    hierarchy = element.get('hierarchy', [])
    
    tree_parts = []
    tree_parts.append(f"<{tag}>")
    
    if attrs:
        attr_str = " ".join([f'{k}="{v}"' for k, v in attrs.items() if v])
        if attr_str:
            tree_parts.append(f"  attributes: {attr_str}")
    
    if text:
        tree_parts.append(f"  text: '{text}'")
    
    if hierarchy:
        tree_parts.append(f"  hierarchy: {' > '.join(hierarchy)}")
    
    tree_parts.append(f"</{tag}>")
    
    return "\n".join(tree_parts)

def get_markup_input(element: Dict[str, Any], html_builder) -> Dict[str, Any]:
    """Get MarkupLM input values."""
    if not element:
        return {"html": "", "target_element": {}, "token_count": 0, "truncated": False}
    
    # Create a mock context for HTML building
    from src.her.locator.html_hierarchy_builder import HTMLHierarchyContext
    context = HTMLHierarchyContext(
        target_element=element,
        parent_elements=[],
        sibling_elements=[],
        html_context="",
        token_count=0,
        truncated=False,
        hierarchy_path=element.get('hierarchy', [])
    )
    
    # Build HTML context
    context.html_context = html_builder._build_html_structure(element, [], [])
    context.token_count = html_builder._count_tokens(context.html_context)
    
    return html_builder.get_markup_input(context)

def get_markup_output(result: Dict[str, Any]) -> Dict[str, Any]:
    """Get MarkupLM output values."""
    return {
        'markup_score': result.get('confidence', 0.0),
        'processed': True,
        'strategy': result.get('strategy', 'unknown')
    }

def main():
    """Main test function."""
    print("🚀 Verizon Flow with CORRECT Steps Test")
    print("=" * 50)
    
    # Run Verizon flow test
    success = test_verizon_correct_steps()
    
    # Overall result
    print("\n🏁 OVERALL RESULT")
    print("=" * 20)
    if success:
        print("🎉 All Verizon steps completed successfully!")
        return 0
    else:
        print("❌ Some steps failed. Check the details above.")
        return 1

if __name__ == "__main__":
    exit(main())