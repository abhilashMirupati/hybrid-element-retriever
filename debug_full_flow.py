#!/usr/bin/env python3
"""
Debug script to show XPaths for each step in the Verizon flow
"""
import os
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set environment variables
os.environ["HER_E2E"] = "1"

def debug_full_flow():
    """Debug the full Verizon flow with XPath output"""
    from her.runner import Runner
    
    print("🔍 Starting full flow debug session...")
    
    # Create runner
    runner = Runner(headless=False)  # Run in visible mode for debugging
    
    try:
        # Step 1: Open Verizon homepage
        print("\n📱 STEP 1: Opening https://www.verizon.com/")
        snapshot = runner._snapshot("https://www.verizon.com/")
        print("  ✅ Page loaded")
        
        # Step 2: Click on Phones btn in top
        print("\n📱 STEP 2: Clicking on Phones btn in top")
        result = runner._resolve_selector("Phones btn in top", snapshot)
        if result.get("selector"):
            print(f"  XPath: {result['selector']}")
            print(f"  Confidence: {result.get('confidence', 'N/A')}")
            runner._do_action("click", result["selector"], None, result.get("promo", {}), "Phones btn in top")
            time.sleep(3)
        else:
            print("  ❌ No selector found for Phones btn")
        
        # Step 3: Select Apple filter
        print("\n🍎 STEP 3: Selecting Apple filter")
        snapshot = runner._snapshot()
        result = runner._resolve_selector("Apple filter", snapshot)
        if result.get("selector"):
            print(f"  XPath: {result['selector']}")
            print(f"  Confidence: {result.get('confidence', 'N/A')}")
            runner._do_action("click", result["selector"], None, result.get("promo", {}), "Apple filter")
            time.sleep(3)
        else:
            print("  ❌ No selector found for Apple filter")
        
        # Step 4: Select Apple iPhone 16 Pro
        print("\n📱 STEP 4: Selecting Apple iPhone 16 Pro")
        snapshot = runner._snapshot()
        result = runner._resolve_selector("Apple iPhone 16 Pro", snapshot)
        if result.get("selector"):
            print(f"  XPath: {result['selector']}")
            print(f"  Confidence: {result.get('confidence', 'N/A')}")
            runner._do_action("click", result["selector"], None, result.get("promo", {}), "Apple iPhone 16 Pro")
            time.sleep(3)
        else:
            print("  ❌ No selector found for Apple iPhone 16 Pro")
        
        # Step 5: Validate landing page
        print("\n✅ STEP 5: Validating landing page")
        current_url = runner._page.url
        print(f"  Current URL: {current_url}")
        validation_result = runner._validate("Validate it landed on https://www.verizon.com/smartphones/apple-iphone-16-pro/")
        print(f"  Validation: {'✅' if validation_result else '❌'}")
        
        # Step 6: Select Desert Titanium
        print("\n🎨 STEP 6: Selecting Desert Titanium")
        snapshot = runner._snapshot()
        result = runner._resolve_selector("Desert Titanium", snapshot)
        if result.get("selector"):
            print(f"  XPath: {result['selector']}")
            print(f"  Confidence: {result.get('confidence', 'N/A')}")
            runner._do_action("click", result["selector"], None, result.get("promo", {}), "Desert Titanium")
            time.sleep(2)
        else:
            print("  ❌ No selector found for Desert Titanium")
        
        # Step 7: Select 512 GB
        print("\n💾 STEP 7: Selecting 512 GB")
        snapshot = runner._snapshot()
        result = runner._resolve_selector("512 GB", snapshot)
        if result.get("selector"):
            print(f"  XPath: {result['selector']}")
            print(f"  Confidence: {result.get('confidence', 'N/A')}")
            runner._do_action("click", result["selector"], None, result.get("promo", {}), "512 GB")
            time.sleep(2)
        else:
            print("  ❌ No selector found for 512 GB")
        
        # Step 8: Click Add to Cart
        print("\n🛒 STEP 8: Clicking Add to Cart")
        snapshot = runner._snapshot()
        result = runner._resolve_selector("Add to Cart", snapshot)
        if result.get("selector"):
            print(f"  XPath: {result['selector']}")
            print(f"  Confidence: {result.get('confidence', 'N/A')}")
            runner._do_action("click", result["selector"], None, result.get("promo", {}), "Add to Cart")
            time.sleep(3)
        else:
            print("  ❌ No selector found for Add to Cart")
        
        # Step 9: Validate cart confirmation
        print("\n✅ STEP 9: Validating 'Added to your cart'")
        snapshot = runner._snapshot()
        
        # Check what text actually appears
        print("  🔍 Checking for cart confirmation text...")
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
        
        found_texts = []
        for element in snapshot.get("elements", []):
            text = element.get("text", "").strip()
            if any(cart_text.lower() in text.lower() for cart_text in possible_texts):
                found_texts.append(text)
                print(f"    Found: '{text}' (Tag: {element.get('tag', 'unknown')})")
        
        if not found_texts:
            print("    No cart confirmation text found")
            print("    All visible text elements:")
            for element in snapshot.get("elements", []):
                text = element.get("text", "").strip()
                if text and element.get("visible", False) and len(text) < 100:
                    print(f"      '{text}' (Tag: {element.get('tag', 'unknown')})")
        
        # Test validation
        validation_result = runner._validate("Validate 'Added to your cart' is visible")
        print(f"  Validation: {'✅' if validation_result else '❌'}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        runner._close()

if __name__ == "__main__":
    debug_full_flow()