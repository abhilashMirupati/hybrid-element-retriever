#!/usr/bin/env python3

import os
import sys
sys.path.insert(0, 'src')

# Set up environment
os.environ['HER_MODELS_DIR'] = '/workspace/src/her/models'
os.environ['HER_CACHE_DIR'] = '/workspace/.her_cache'
os.environ['HER_E2E'] = '1'

def debug_url_validation():
    """Debug URL validation"""
    try:
        from her.runner import run_steps
        
        # Test just the first 4 steps to see what URL we land on
        steps = [
            "Open https://www.verizon.com/",
            "Click on Phones btn in top",
            "Select Apple filter",
            "Select Apple iPhone 16 Pro"
        ]
        
        print("Testing first 4 steps...")
        run_steps(steps, headless=True)
        print("✅ First 4 steps completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_url_validation()