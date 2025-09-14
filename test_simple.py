#!/usr/bin/env python3
"""
Simple test to verify smart snapshot manager integration.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from src.her.testing.natural_test_runner import NaturalTestRunner

def test_simple():
    """Test the natural test runner with smart snapshot manager."""
    print("🧪 Testing Natural Test Runner with Smart Snapshot Manager...")
    
    # Create runner
    runner = NaturalTestRunner(headless=True)
    print("✅ Runner created")
    
    # Test with a simple navigation
    result = runner.run_test(
        test_name="Simple Test",
        steps=["Navigate to \"https://www.google.com/\""],
        start_url="https://www.google.com/"
    )
    
    print(f"📊 Test result: {result['success']}")
    print(f"📈 Performance stats: {result.get('performance_stats', {})}")
    
    runner.runner._close()
    print("✅ Test completed!")

if __name__ == "__main__":
    test_simple()