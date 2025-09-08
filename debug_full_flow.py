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

def check_and_select_element(runner, result, step_name):
    """Check element count and find unique element if needed"""
    if not result.get("selector"):
        print(f"  ❌ No selector found for {step_name}")
        return False
    
    print(f"  XPath: {result['selector']}")
    print(f"  Confidence: {result.get('confidence', 'N/A')}")
    
    # Check element count and find unique if needed
    try:
        locators = runner._page.locator(f"xpath={result['selector']}")
        count = locators.count()
        print(f"  Element count: {count}")
        
        if count > 1:
            print(f"  ⚠️  Multiple elements found ({count}), finding unique...")
            # Find the best unique element
            best_element = None
            best_score = -1
            
            for i in range(count):
                try:
                    element = locators.nth(i)
                    if element.is_visible():
                        # Get element properties for scoring
                        bbox = element.bounding_box()
                        if bbox and bbox['width'] > 0 and bbox['height'] > 0:
                            # Score based on size and position
                            score = bbox['width'] * bbox['height']
                            if bbox['y'] >= 0:  # Not off-screen
                                score += 1000
                            
                            print(f"    Element {i+1}: Size={bbox['width']:.0f}x{bbox['height']:.0f}, Score={score:.0f}")
                            
                            if score > best_score:
                                best_score = score
                                best_element = element
                except Exception as e:
                    print(f"    Element {i+1}: Error - {e}")
            
            if best_element:
                print(f"  ✅ Selected best element with score: {best_score:.0f}")
            else:
                print(f"  ❌ No suitable element found")
                return False
        elif count == 1:
            print(f"  ✅ Single element found")
        else:
            print(f"  ❌ No elements found")
            return False
            
    except Exception as e:
        print(f"  ⚠️  Error checking element count: {e}")
        return False
    
    return True

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
        if check_and_select_element(runner, result, "Phones btn"):
            runner._do_action("click", result["selector"], None, result.get("promo", {}), "Phones btn in top")
            time.sleep(3)
        
        # Step 3: Select Apple filter
        print("\n🍎 STEP 3: Selecting Apple filter")
        snapshot = runner._snapshot()
        result = runner._resolve_selector("Apple filter", snapshot)
        if check_and_select_element(runner, result, "Apple filter"):
            runner._do_action("click", result["selector"], None, result.get("promo", {}), "Apple filter")
            time.sleep(3)
        
        # Step 4: Select Apple iPhone 16 Pro
        print("\n📱 STEP 4: Selecting Apple iPhone 16 Pro")
        snapshot = runner._snapshot()
        result = runner._resolve_selector("Apple iPhone 16 Pro", snapshot)
        if check_and_select_element(runner, result, "Apple iPhone 16 Pro"):
            runner._do_action("click", result["selector"], None, result.get("promo", {}), "Apple iPhone 16 Pro")
            time.sleep(3)
        
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
        if check_and_select_element(runner, result, "Desert Titanium"):
            runner._do_action("click", result["selector"], None, result.get("promo", {}), "Desert Titanium")
            time.sleep(2)
        
        # Step 7: Select 512 GB
        print("\n💾 STEP 7: Selecting 512 GB")
        snapshot = runner._snapshot()
        result = runner._resolve_selector("512 GB", snapshot)
        if check_and_select_element(runner, result, "512 GB"):
            runner._do_action("click", result["selector"], None, result.get("promo", {}), "512 GB")
            time.sleep(2)
        
        # Step 8: Click Add to Cart
        print("\n🛒 STEP 8: Clicking Add to Cart")
        snapshot = runner._snapshot()
        result = runner._resolve_selector("Add to Cart", snapshot)
        if check_and_select_element(runner, result, "Add to Cart"):
            runner._do_action("click", result["selector"], None, result.get("promo", {}), "Add to Cart")
            time.sleep(3)
        
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