"""Debug version of Verizon flow test with detailed logging."""

import pytest
import os

try:
    from playwright.sync_api import sync_playwright  # noqa: F401
    PLAYWRIGHT_AVAILABLE = True
except Exception:
    PLAYWRIGHT_AVAILABLE = False


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not available")
@pytest.mark.skipif(os.getenv("HER_E2E") != "1", reason="Set HER_E2E=1 to run live e2e test")
@pytest.mark.timeout(600)
def test_verizon_flow_debug():
    """Debug version with detailed step-by-step logging."""
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
        
        # Step 2: Click on Phones btn
        print("\n" + "="*80)
        print("🚀 STEP 2: Click on Phones btn in top")
        print("="*80)
        shot = runner._snapshot()
        result = runner._resolve_selector("Phones btn in top", shot)
        
        print(f"🔍 MiniLM Top-K Results:")
        for i, candidate in enumerate(result.get("candidates", [])[:5]):
            print(f"  {i+1}. Score: {candidate['score']:.3f} | Selector: {candidate['selector']}")
            print(f"     Meta: {candidate.get('meta', {})}")
        
        print(f"\n🎯 MarkupLM Selected:")
        print(f"  Selector: {result['selector']}")
        print(f"  Confidence: {result['confidence']:.3f}")
        print(f"  Reasons: {result.get('reasons', [])}")
        
        # Check if there are multiple elements
        try:
            locators = runner._page.locator(f"xpath={result['selector']}")
            count = locators.count()
            print(f"🔍 Found {count} elements with this XPath")
            if count > 1:
                print("⚠️  Multiple elements found - will use best element selection")
        except Exception as e:
            print(f"⚠️  Could not count elements: {e}")
        
        # Execute click
        runner._do_action("click", result["selector"], None, result.get("promo", {}))
        runner._page.wait_for_timeout(3000)  # Wait for navigation
        
        current_url = runner._page.url
        print(f"✅ After click - Current URL: {current_url}")
        
        # Step 3: Select Apple filter
        print("\n" + "="*80)
        print("🚀 STEP 3: Select Apple filter")
        print("="*80)
        shot = runner._snapshot()
        result = runner._resolve_selector("Apple filter", shot)
        
        print(f"🔍 MiniLM Top-K Results:")
        for i, candidate in enumerate(result.get("candidates", [])[:5]):
            print(f"  {i+1}. Score: {candidate['score']:.3f} | Selector: {candidate['selector']}")
            print(f"     Meta: {candidate.get('meta', {})}")
        
        print(f"\n🎯 MarkupLM Selected:")
        print(f"  Selector: {result['selector']}")
        print(f"  Confidence: {result['confidence']:.3f}")
        print(f"  Reasons: {result.get('reasons', [])}")
        
        # Check multiple elements
        try:
            locators = runner._page.locator(f"xpath={result['selector']}")
            count = locators.count()
            print(f"🔍 Found {count} elements with this XPath")
        except Exception as e:
            print(f"⚠️  Could not count elements: {e}")
        
        # Execute select
        runner._do_action("select", result["selector"], None, result.get("promo", {}))
        runner._page.wait_for_timeout(3000)  # Wait for filter to apply
        
        current_url = runner._page.url
        print(f"✅ After Apple filter - Current URL: {current_url}")
        
        # Step 4: Select Apple iPhone 16 Pro
        print("\n" + "="*80)
        print("🚀 STEP 4: Select Apple iPhone 16 Pro")
        print("="*80)
        shot = runner._snapshot()
        result = runner._resolve_selector("Apple iPhone 16 Pro", shot)
        
        print(f"🔍 MiniLM Top-K Results:")
        for i, candidate in enumerate(result.get("candidates", [])[:5]):
            print(f"  {i+1}. Score: {candidate['score']:.3f} | Selector: {candidate['selector']}")
            print(f"     Meta: {candidate.get('meta', {})}")
        
        print(f"\n🎯 MarkupLM Selected:")
        print(f"  Selector: {result['selector']}")
        print(f"  Confidence: {result['confidence']:.3f}")
        print(f"  Reasons: {result.get('reasons', [])}")
        
        # Check multiple elements
        try:
            locators = runner._page.locator(f"xpath={result['selector']}")
            count = locators.count()
            print(f"🔍 Found {count} elements with this XPath")
        except Exception as e:
            print(f"⚠️  Could not count elements: {e}")
        
        # Execute select
        runner._do_action("select", result["selector"], None, result.get("promo", {}))
        runner._page.wait_for_timeout(5000)  # Wait for navigation
        
        current_url = runner._page.url
        print(f"✅ After iPhone selection - Current URL: {current_url}")
        
        # Step 5: Validate URL
        print("\n" + "="*80)
        print("🚀 STEP 5: Validate it landed on https://www.verizon.com/smartphones/apple-iphone-16-pro/")
        print("="*80)
        expected_url = "https://www.verizon.com/smartphones/apple-iphone-16-pro/"
        print(f"Expected URL: {expected_url}")
        print(f"Current URL:  {current_url}")
        
        # Manual URL validation
        validation_result = runner._validate("Validate it landed on https://www.verizon.com/smartphones/apple-iphone-16-pro/")
        print(f"Validation result: {validation_result}")
        
        # Additional URL analysis
        print(f"\n🔍 URL Analysis:")
        print(f"  Expected contains 'iphone-16-pro': {'iphone-16-pro' in expected_url.lower()}")
        print(f"  Current contains 'iphone-16-pro': {'iphone-16-pro' in current_url.lower()}")
        print(f"  Expected contains 'smartphones': {'smartphones' in expected_url}")
        print(f"  Current contains 'smartphones': {'smartphones' in current_url}")
        print(f"  Expected contains 'apple': {'apple' in expected_url.lower()}")
        print(f"  Current contains 'apple': {'apple' in current_url.lower()}")
        
        if validation_result:
            print("✅ URL validation PASSED!")
        else:
            print("❌ URL validation FAILED!")
            print("This might be due to:")
            print("  - Different URL structure on the live site")
            print("  - Redirects or URL parameters")
            print("  - The page structure changed")
        
    finally:
        runner._close()