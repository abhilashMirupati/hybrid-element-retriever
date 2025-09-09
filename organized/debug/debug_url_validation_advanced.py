#!/usr/bin/env python3

import os
import sys
sys.path.insert(0, 'src')

# Set up environment
os.environ['HER_MODELS_DIR'] = '/workspace/src/her/models'
os.environ['HER_CACHE_DIR'] = '/workspace/.her_cache'
os.environ['HER_E2E'] = '1'

def debug_url_after_click():
    """Debug what URL we land on after clicking iPhone 16 Pro"""
    try:
        from her.runner import Runner
        
        runner = Runner(headless=True)
        
        # Run first 4 steps
        steps = [
            "Open https://www.verizon.com/",
            "Click on Phones btn in top",
            "Select Apple filter",
            "Select Apple iPhone 16 Pro"
        ]
        
        print("Running first 4 steps...")
        results = runner.run(steps)
        
        # Check the results
        for i, result in enumerate(results):
            print(f"Step {i+1}: {result.step} - {'✅' if result.ok else '❌'}")
            if not result.ok:
                print(f"  Error: {result.info}")
        
        # Get current URL
        if runner._page:
            current_url = runner._page.url
            print(f"\nCurrent URL after step 4: {current_url}")
            
            # Test the validation
            expected_url = "https://www.verizon.com/smartphones/apple-iphone-16-pro/"
            print(f"Expected URL: {expected_url}")
            print(f"URL contains expected: {expected_url in current_url}")
            print(f"Expected contains URL: {current_url in expected_url}")
        
        runner._close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_url_after_click()