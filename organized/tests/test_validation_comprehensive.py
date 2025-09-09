#!/usr/bin/env python3

import os
import sys
sys.path.insert(0, 'src')

# Set up environment
os.environ['HER_MODELS_DIR'] = '/workspace/src/her/models'
os.environ['HER_CACHE_DIR'] = '/workspace/.her_cache'
os.environ['HER_E2E'] = '1'

def test_validation():
    """Test URL validation"""
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
        
        # Check results
        for i, result in enumerate(results):
            print(f"Step {i+1}: {result.step} - {'✅' if result.ok else '❌'}")
        
        # Test validation manually
        if runner._page:
            current_url = runner._page.url
            print(f"\nCurrent URL: {current_url}")
            
            # Test the validation logic
            expected_url = "https://www.verizon.com/smartphones/apple-iphone-16-pro/"
            print(f"Expected URL: {expected_url}")
            
            # Test both directions
            url_contains_expected = expected_url in current_url
            expected_contains_url = current_url in expected_url
            
            print(f"URL contains expected: {url_contains_expected}")
            print(f"Expected contains URL: {expected_contains_url}")
            
            # Test the actual validation method
            validation_step = "Validate it landed on https://www.verizon.com/smartphones/apple-iphone-16-pro/"
            is_valid = runner._validate(validation_step)
            print(f"Validation result: {is_valid}")
        
        runner._close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_validation()