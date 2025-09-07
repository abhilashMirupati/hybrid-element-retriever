#!/usr/bin/env python3

import os
import sys
sys.path.insert(0, 'src')

# Set up environment
os.environ['HER_MODELS_DIR'] = '/workspace/src/her/models'
os.environ['HER_CACHE_DIR'] = '/workspace/.her_cache'
os.environ['HER_E2E'] = '1'

def test_simple_flow():
    """Test a simple flow to verify the fixes work"""
    try:
        from her.runner import run_steps
        
        # Simple test with just opening a page and clicking
        steps = [
            "Open https://www.verizon.com/",
            "Click on Phones btn in top"
        ]
        
        print("Testing simple flow...")
        print("Steps:", steps)
        
        # Run with debug output
        os.environ['HER_DEBUG_CANDIDATES'] = '1'
        run_steps(steps, headless=True)
        print("✅ Simple test passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple_flow()