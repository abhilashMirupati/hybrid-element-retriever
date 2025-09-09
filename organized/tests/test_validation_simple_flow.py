#!/usr/bin/env python3

import os
import sys
sys.path.insert(0, 'src')

# Set up environment
os.environ['HER_MODELS_DIR'] = '/workspace/src/her/models'
os.environ['HER_CACHE_DIR'] = '/workspace/.her_cache'
os.environ['HER_E2E'] = '1'

def test_validation_simple():
    """Test URL validation with a simple case"""
    try:
        from her.runner import Runner
        
        runner = Runner(headless=True)
        
        # Just open a page and test validation
        runner._snapshot("https://www.verizon.com/")
        
        # Test the validation method directly
        validation_step = "Validate it landed on https://www.verizon.com/"
        is_valid = runner._validate(validation_step)
        print(f"Validation result for verizon.com: {is_valid}")
        
        # Test with a different URL
        validation_step2 = "Validate it landed on https://www.google.com/"
        is_valid2 = runner._validate(validation_step2)
        print(f"Validation result for google.com: {is_valid2}")
        
        runner._close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_validation_simple()