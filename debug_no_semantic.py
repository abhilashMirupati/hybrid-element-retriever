#!/usr/bin/env python3
"""
Debug script to test the Enhanced No-Semantic Matcher directly
"""

import os
import sys
import time
import logging
from playwright.sync_api import sync_playwright

# Add src to path
sys.path.insert(0, '/workspace/src')

# Set environment variables
os.environ["HER_USE_SEMANTIC_SEARCH"] = "false"
os.environ["HER_DEBUG"] = "true"

from her.core.runner import Runner
from her.locator.enhanced_no_semantic import EnhancedNoSemanticMatcher

# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def debug_no_semantic_matcher():
    """Debug the no-semantic matcher step by step"""
    
    print("=" * 80)
    print("DEBUGGING ENHANCED NO-SEMANTIC MATCHER")
    print("=" * 80)
    
    # Test cases from our Verizon test
    test_cases = [
        "Click on 'Shop'",
        "Click on 'Phones'", 
        "Click on 'iPhone 15'",
        "Click on 'White color'",
        "Click on 'Continue'"
    ]
    
    try:
        # Initialize runner and take snapshot
        print("\n1. Initializing runner and taking snapshot...")
        runner = Runner()
        snapshot = runner._snapshot("https://www.verizon.com")
        elements = snapshot.get('elements', [])
        print(f"Found {len(elements)} elements on page")
        
        # Test the matcher directly
        print("\n2. Testing Enhanced No-Semantic Matcher...")
        matcher = EnhancedNoSemanticMatcher()
        
        # Get the page from runner
        runner_page = runner._ensure_browser()
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n--- Test Case {i}: {test_case} ---")
            
            try:
                result = matcher.query(test_case, elements, runner_page)
                print(f"Result: {result}")
                
                # Debug: Check what elements have text matching our target
                target_text = test_case.replace("Click on ", "").replace("'", "")
                print(f"\nLooking for elements with text containing: '{target_text}'")
                
                matching_elements = []
                for elem in elements[:20]:  # Check first 20 elements
                    text = elem.get('text', '').strip()
                    if target_text.lower() in text.lower() and text:
                        matching_elements.append({
                            'tag': elem.get('tag', ''),
                            'text': text,
                            'attributes': elem.get('attributes', {})
                        })
                
                print(f"Found {len(matching_elements)} elements with matching text:")
                for elem in matching_elements:
                    print(f"  - {elem['tag']}: '{elem['text']}' (attrs: {elem['attributes']})")
                
            except Exception as e:
                print(f"Error testing {test_case}: {e}")
                import traceback
                traceback.print_exc()
            
            time.sleep(1)
        
    except Exception as e:
        print(f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_no_semantic_matcher()