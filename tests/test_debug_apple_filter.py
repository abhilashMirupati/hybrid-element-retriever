"""Debug test for Apple filter selection with detailed MiniLM/MarkupLM output."""

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
def test_debug_apple_filter_selection():
    """Debug Apple filter selection with detailed output."""
    from her.runner import Runner

    runner = Runner(headless=True)
    
    try:
        print("\n" + "="*80)
        print("🔍 DEBUG: APPLE FILTER SELECTION")
        print("="*80)
        
        # Step 1: Navigate to smartphones page
        print("\n🚀 STEP 1: Navigate to smartphones page")
        runner._snapshot("https://www.verizon.com/smartphones/")
        runner._page.wait_for_timeout(3000)
        
        current_url = runner._page.url
        print(f"✅ Current URL: {current_url}")
        
        # Step 2: Get snapshot and analyze elements
        print("\n🔍 STEP 2: Analyze page elements")
        shot = runner._snapshot()
        elements = shot.get('elements', [])
        print(f"Total elements on page: {len(elements)}")
        
        # Find all Apple-related elements
        apple_elements = []
        for i, el in enumerate(elements):
            text = el.get('text', '').lower()
            attrs = el.get('attributes', {})
            if 'apple' in text or 'apple' in str(attrs).lower():
                apple_elements.append((i, el))
        
        print(f"\nFound {len(apple_elements)} Apple-related elements:")
        for i, (idx, el) in enumerate(apple_elements[:10]):
            print(f"  {i+1}. Element {idx}:")
            print(f"     Tag: {el.get('tag', '')}")
            print(f"     Text: '{el.get('text', '')[:50]}...'")
            print(f"     ID: {el.get('attributes', {}).get('id', '')}")
            print(f"     Visible: {el.get('visible', False)}")
            print(f"     XPath: {el.get('xpath', '')[:100]}...")
        
        # Step 3: Test Apple filter selection with detailed debug
        print("\n🔍 STEP 3: Test Apple filter selection")
        result = runner._resolve_selector("Apple filter", shot)
        
        print(f"\n📊 SELECTION RESULT:")
        print(f"Query: 'Apple filter'")
        print(f"Selected XPath: {result['selector']}")
        print(f"Confidence: {result['confidence']:.3f}")
        print(f"Reason: {result.get('reason', 'N/A')}")
        
        # Show all candidates
        candidates = result.get('candidates', [])
        print(f"\n📋 ALL CANDIDATES ({len(candidates)}):")
        for i, candidate in enumerate(candidates):
            print(f"  {i+1}. Score: {candidate['score']:.3f}")
            print(f"     XPath: {candidate['selector']}")
            meta = candidate.get('meta', {})
            print(f"     Tag: {meta.get('tag', '')}")
            print(f"     Text: '{meta.get('text', '')[:50]}...'")
            print(f"     ID: {meta.get('attributes', {}).get('id', '')}")
            print(f"     Reasons: {candidate.get('reasons', [])}")
        
        # Step 4: Test multiple element handling
        print(f"\n🔍 STEP 4: Test multiple element handling")
        selector = result['selector']
        locators = runner._page.locator(f"xpath={selector}")
        count = locators.count()
        print(f"XPath '{selector}' matches {count} elements")
        
        if count > 1:
            print(f"\n📊 MULTIPLE ELEMENT ANALYSIS:")
            for i in range(count):
                try:
                    element = locators.nth(i)
                    bbox = element.bounding_box()
                    text = element.text_content() or ''
                    tag = element.evaluate('el => el.tagName') or ''
                    id_attr = element.get_attribute('id') or ''
                    visible = element.is_visible()
                    
                    print(f"  Element {i+1}:")
                    print(f"    Tag: {tag}")
                    print(f"    ID: {id_attr}")
                    print(f"    Text: '{text}'")
                    print(f"    Visible: {visible}")
                    print(f"    BBox: {bbox}")
                    
                except Exception as e:
                    print(f"  Element {i+1}: Error - {e}")
            
            # Test _click_best_element directly
            print(f"\n🎯 TESTING _click_best_element:")
            runner._click_best_element(selector, "Apple filter")
            
        else:
            print(f"Only {count} element found - no multiple element handling needed")
        
        # Step 5: Check final result
        print(f"\n🔍 STEP 5: Check final result")
        current_url = runner._page.url
        print(f"Final URL: {current_url}")
        
        if "apple" in current_url.lower():
            print("✅ SUCCESS: Apple filter applied correctly!")
        else:
            print("❌ FAILED: Apple filter not applied")
        
        print(f"\n🎉 DEBUG COMPLETED!")
        
    finally:
        runner._close()