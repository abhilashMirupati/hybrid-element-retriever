#!/usr/bin/env python3

import os
import sys
sys.path.insert(0, 'src')

from her.runner import Runner, run_steps

def test_verizon_flow_fixed():
    """Test the Verizon flow with fixes"""
    steps = [
        "Open https://www.verizon.com/",
        "Click on Phones btn in top",
        "Select Apple filter", 
        "Select Apple iPhone 16 Pro",
        "Validate it landed on https://www.verizon.com/smartphones/apple-iphone-16-pro/"
    ]
    
    print("Testing Verizon flow with fixes...")
    try:
        run_steps(steps, headless=True)
        print("✅ Test passed!")
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_verizon_flow_fixed()