#!/usr/bin/env python3
"""
Simple test script to test the Verizon flow without full model setup
"""
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set environment variables
os.environ["HER_E2E"] = "1"

def test_basic_import():
    """Test basic imports without model requirements"""
    try:
        from her.runner import Runner
        print("✅ Basic imports work")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_runner_creation():
    """Test creating a runner instance"""
    try:
        from her.runner import Runner
        runner = Runner(headless=True)
        print("✅ Runner creation works")
        return True
    except Exception as e:
        print(f"❌ Runner creation failed: {e}")
        return False

def test_browser_setup():
    """Test browser setup"""
    try:
        from her.runner import Runner
        runner = Runner(headless=True)
        page = runner._ensure_browser()
        if page:
            print("✅ Browser setup works")
            return True
        else:
            print("❌ Browser setup failed - no page")
            return False
    except Exception as e:
        print(f"❌ Browser setup failed: {e}")
        return False

def test_simple_navigation():
    """Test simple navigation without models"""
    try:
        from her.runner import Runner
        runner = Runner(headless=True)
        
        # Test opening a simple page
        snapshot = runner._snapshot("https://www.google.com")
        if snapshot and "elements" in snapshot:
            print("✅ Simple navigation works")
            return True
        else:
            print("❌ Simple navigation failed")
            return False
    except Exception as e:
        print(f"❌ Simple navigation failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing basic functionality...")
    
    tests = [
        test_basic_import,
        test_runner_creation,
        test_browser_setup,
        test_simple_navigation,
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📊 Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All basic tests passed!")
    else:
        print("⚠️  Some tests failed")