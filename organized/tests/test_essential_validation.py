#!/usr/bin/env python3
"""
Essential Validation Test
Uses the comprehensive debug script to test all essential functionality
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    print("🚀 ESSENTIAL VALIDATION TEST")
    print("=" * 50)
    
    # Run the comprehensive debug script
    debug_script = Path(__file__).parent.parent / "debug" / "debug_comprehensive_testing.py"
    
    if not debug_script.exists():
        print(f"❌ Debug script not found: {debug_script}")
        return False
    
    print(f"🔍 Running comprehensive debug test...")
    print(f"   Script: {debug_script}")
    
    try:
        result = subprocess.run([sys.executable, str(debug_script)], 
                              capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print(f"✅ ESSENTIAL VALIDATION PASSED")
            print(f"\n📊 Test Output:")
            print(result.stdout)
            return True
        else:
            print(f"❌ ESSENTIAL VALIDATION FAILED")
            print(f"\n📊 Error Output:")
            print(result.stdout)
            print(f"\n❌ Error Details:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ Test timed out after 300 seconds")
        return False
    except Exception as e:
        print(f"💥 Error running test: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)