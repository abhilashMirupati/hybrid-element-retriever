#!/usr/bin/env python3
"""Simple debug of element extraction."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from her.runner import run_steps

def test_simple():
    """Test simple element extraction."""
    print("🔍 Testing Simple Element Extraction...")
    
    try:
        # Test just the first step
        steps = [
            "Open https://www.verizon.com/",
            "Click on Phones btn in top"
        ]
        
        print("Running steps...")
        run_steps(steps, headless=True)
        print("✅ Test completed successfully")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple()