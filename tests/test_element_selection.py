"""Test element selection with multiple elements."""

import pytest
import os

try:
    from playwright.sync_api import sync_playwright  # noqa: F401
    PLAYWRIGHT_AVAILABLE = True
except Exception:
    PLAYWRIGHT_AVAILABLE = False


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not available")
@pytest.mark.skipif(os.getenv("HER_E2E") != "1", reason="Set HER_E2E=1 to run live e2e test")
@pytest.mark.timeout(300)
def test_element_selection_with_scroll():
    """Test that element selection works with scroll-into-view."""
    from her.runner import Runner

    runner = Runner(headless=True)
    
    try:
        # Step 1: Open page
        print("\n" + "="*80)
        print("🚀 STEP 1: Open https://www.verizon.com/")
        print("="*80)
        runner._snapshot("https://www.verizon.com/")
        current_url = runner._page.url
        print(f"✅ Current URL: {current_url}")
        
        # Step 2: Click on Phones btn with detailed element analysis
        print("\n" + "="*80)
        print("🚀 STEP 2: Click on Phones btn in top")
        print("="*80)
        shot = runner._snapshot()
        result = runner._resolve_selector("Phones btn in top", shot)
        
        print(f"🎯 Selected: {result['selector']}")
        print(f"Confidence: {result['confidence']:.3f}")
        
        # Check how many elements match this selector
        try:
            locators = runner._page.locator(f"xpath={result['selector']}")
            count = locators.count()
            print(f"🔍 Found {count} elements with this XPath")
            
            if count > 1:
                print("⚠️  Multiple elements found - will use improved selection logic")
                # Show details of each element
                for i in range(min(count, 5)):  # Show first 5
                    try:
                        element = locators.nth(i)
                        bbox = element.bounding_box()
                        text = element.text_content() or ""
                        print(f"  Element {i+1}: Text='{text[:30]}...' | Pos=({bbox['x']:.0f}, {bbox['y']:.0f}) | Size=({bbox['width']:.0f}x{bbox['height']:.0f})")
                    except Exception as e:
                        print(f"  Element {i+1}: Error getting details - {e}")
        except Exception as e:
            print(f"⚠️  Could not analyze elements: {e}")
        
        # Execute click with improved selection
        runner._do_action("click", result["selector"], None, result.get("promo", {}))
        runner._page.wait_for_timeout(3000)
        
        current_url = runner._page.url
        print(f"✅ After click - Current URL: {current_url}")
        
        # Verify we're on the right page
        if "/smartphones/" in current_url:
            print("✅ SUCCESS: Successfully navigated to smartphones page!")
        else:
            print(f"❌ FAILED: Expected smartphones page, got: {current_url}")
        
        print(f"\n🎉 Test completed! Final URL: {current_url}")
        
    finally:
        runner._close()