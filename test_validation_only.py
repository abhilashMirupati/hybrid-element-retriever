#!/usr/bin/env python3
"""
Test script to verify the validation step works correctly
"""
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set environment variables
os.environ["HER_E2E"] = "1"

def test_validation_only():
    """Test just the validation step"""
    from her.runner import Runner
    
    print("🔍 Testing validation step only...")
    
    # Create runner
    runner = Runner(headless=True)
    
    try:
        # Navigate to the iPhone page directly
        print("📱 Navigating to iPhone 16 Pro page...")
        snapshot = runner._snapshot("https://www.verizon.com/smartphones/apple-iphone-16-pro/")
        
        # Wait for page to load
        import time
        time.sleep(5)
        
        # Select Desert Titanium
        print("🎨 Selecting Desert Titanium...")
        runner._snapshot()  # Get current state
        result = runner._resolve_selector("Desert Titanium", runner._snapshot())
        if result.get("selector"):
            runner._do_action("click", result["selector"], None, result.get("promo", {}), "Desert Titanium")
            time.sleep(2)
        
        # Select 512 GB
        print("💾 Selecting 512 GB...")
        runner._snapshot()  # Get current state
        result = runner._resolve_selector("512 GB", runner._snapshot())
        if result.get("selector"):
            runner._do_action("click", result["selector"], None, result.get("promo", {}), "512 GB")
            time.sleep(2)
        
        # Click Add to Cart
        print("🛒 Clicking Add to Cart...")
        runner._snapshot()  # Get current state
        result = runner._resolve_selector("Add to Cart", runner._snapshot())
        if result.get("selector"):
            runner._do_action("click", result["selector"], None, result.get("promo", {}), "Add to Cart")
            time.sleep(5)  # Wait longer for cart confirmation
        
        # Test validation
        print("✅ Testing validation...")
        validation_result = runner._validate("Validate 'Added to your cart'")
        print(f"Validation result: {validation_result}")
        
        # Also test the specific validation method
        print("🔍 Testing specific validation method...")
        snapshot = runner._snapshot()
        validation_result2 = runner._validate("'Added to your cart'", snapshot)
        print(f"Specific validation result: {validation_result2}")
        
        return validation_result
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        runner.close()

if __name__ == "__main__":
    result = test_validation_only()
    print(f"\n🎯 Final result: {'✅ PASSED' if result else '❌ FAILED'}")