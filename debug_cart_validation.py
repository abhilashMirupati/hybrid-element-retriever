#!/usr/bin/env python3
"""
Debug script to check what text appears after clicking Add to Cart
"""
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set environment variables
os.environ["HER_E2E"] = "1"

def debug_cart_validation():
    """Debug the cart validation step"""
    from her.runner import Runner
    
    print("🔍 Starting debug session...")
    
    # Create runner
    runner = Runner(headless=False)  # Run in visible mode for debugging
    
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
            time.sleep(3)  # Wait longer for response
        
        # Check what text appears
        print("🔍 Checking for cart confirmation text...")
        snapshot = runner._snapshot()
        
        # Look for various possible texts
        possible_texts = [
            "Added to your cart",
            "Added to cart",
            "Item added to cart",
            "Added to your bag",
            "Item added to your cart",
            "Successfully added",
            "Added successfully",
            "Cart updated",
            "Item added",
            "Added",
            "Success"
        ]
        
        print("📋 Current page elements containing cart-related text:")
        for element in snapshot.get("elements", []):
            text = element.get("text", "").strip()
            if any(cart_text.lower() in text.lower() for cart_text in possible_texts):
                print(f"  Found: '{text}' (Tag: {element.get('tag', 'unknown')})")
        
        # Try to find any visible text that might be the confirmation
        print("\n🔍 All visible text elements:")
        for element in snapshot.get("elements", []):
            text = element.get("text", "").strip()
            if text and element.get("visible", False) and len(text) < 100:
                print(f"  '{text}' (Tag: {element.get('tag', 'unknown')})")
        
        # Test the validation function
        print("\n🧪 Testing validation function...")
        validation_steps = [
            "Validate 'Added to your cart' is visible",
            "Validate 'Added to cart' is visible", 
            "Validate 'Item added to cart' is visible",
            "Validate 'Added to your bag' is visible"
        ]
        
        for step in validation_steps:
            result = runner._validate(step)
            print(f"  {step}: {'✅' if result else '❌'}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        runner._close()

if __name__ == "__main__":
    debug_cart_validation()