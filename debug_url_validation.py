#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from her.runner import Runner

def debug_url_validation():
    runner = Runner()
    
    # Navigate to Verizon homepage
    print("🌐 Step 1: Navigating to Verizon homepage...")
    snapshot = runner._snapshot("https://www.verizon.com/")
    
    # Click on Phones
    print("\n🌐 Step 2: Clicking on Phones...")
    result = runner._resolve_selector("Click on Phones btn in top", snapshot)
    if result.get("selector"):
        runner._do_action("click", result["selector"], None, result.get("promo", {}))
        runner._page.wait_for_timeout(2000)
        print(f"✅ Clicked on Phones, current URL: {runner._page.url}")
    
    # Select Apple filter
    print("\n🌐 Step 3: Selecting Apple filter...")
    snapshot = runner._snapshot()
    result = runner._resolve_selector("Select Apple filter", snapshot)
    if result.get("selector"):
        runner._do_action("select", result["selector"], None, result.get("promo", {}))
        runner._page.wait_for_timeout(2000)
        print(f"✅ Selected Apple filter, current URL: {runner._page.url}")
    
    # Select Apple iPhone 16 Pro
    print("\n🌐 Step 4: Selecting Apple iPhone 16 Pro...")
    snapshot = runner._snapshot()
    result = runner._resolve_selector("Select Apple iPhone 16 Pro", snapshot)
    if result.get("selector"):
        runner._do_action("select", result["selector"], None, result.get("promo", {}))
        runner._page.wait_for_timeout(3000)  # Wait longer for product page to load
        print(f"✅ Selected iPhone 16 Pro, current URL: {runner._page.url}")
    
    # Test URL validation
    print("\n🌐 Step 5: Testing URL validation...")
    expected_url = "https://www.verizon.com/smartphones/apple-iphone-16-pro/"
    current_url = runner._page.url
    print(f"Expected URL: {expected_url}")
    print(f"Current URL: {current_url}")
    
    # Test the validation logic
    validation_result = runner._validate(f"Validate it landed on {expected_url}")
    print(f"Validation result: {validation_result}")
    
    runner._close()

if __name__ == "__main__":
    debug_url_validation()