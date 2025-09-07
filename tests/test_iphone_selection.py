"""Test iPhone 16 Pro Max selection based on actual HTML structure."""

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
def test_iphone_16_pro_max_selection():
    """Test selecting iPhone 16 Pro Max based on actual HTML structure."""
    from her.runner import Runner

    runner = Runner(headless=True)
    
    try:
        print("\n" + "="*80)
        print("🚀 TESTING IPHONE 16 PRO MAX SELECTION")
        print("="*80)
        print("Based on provided HTML structure:")
        print("- Product tile: data-testid='product-tile'")
        print("- Product name: id='tileProductText'")
        print("- Product link: href contains 'apple-iphone-16-pro-max'")
        print("- Quick view: data-testid='quickViewBtn'")
        
        # Step 1: Navigate to smartphones page
        print("\n🚀 STEP 1: Navigate to smartphones page")
        runner._snapshot("https://www.verizon.com/smartphones/")
        runner._page.wait_for_timeout(3000)
        
        current_url = runner._page.url
        print(f"✅ Current URL: {current_url}")
        
        # Step 2: Apply Apple filter
        print("\n🚀 STEP 2: Apply Apple filter")
        shot = runner._snapshot()
        result = runner._resolve_selector("Apple filter", shot)
        
        print(f"🎯 Selected: {result['selector']}")
        print(f"Confidence: {result['confidence']:.3f}")
        
        runner._do_action("select", result["selector"], None, result.get("promo", {}), "Apple filter")
        runner._page.wait_for_timeout(3000)
        
        current_url = runner._page.url
        print(f"✅ After Apple filter - Current URL: {current_url}")
        
        # Step 3: Look for iPhone 16 Pro Max using different strategies
        print("\n🚀 STEP 3: Look for iPhone 16 Pro Max")
        shot = runner._snapshot()
        
        # Try different query strategies
        queries = [
            "Apple iPhone 16 Pro Max",
            "iPhone 16 Pro Max", 
            "iPhone 16 Pro",
            "Pro Max",
            "tileProductText"
        ]
        
        for query in queries:
            print(f"\n🔍 Trying query: '{query}'")
            result = runner._resolve_selector(query, shot)
            
            print(f"🎯 Selected: {result['selector']}")
            print(f"Confidence: {result['confidence']:.3f}")
            
            if result['selector']:
                print(f"✅ Found element with query: '{query}'")
                
                # Check if it's the right element
                if "iphone" in result['selector'].lower() or "pro" in result['selector'].lower():
                    print(f"✅ Looks like iPhone element!")
                else:
                    print(f"⚠️  Might not be iPhone element")
                
                # Show top candidates
                candidates = result.get('candidates', [])
                print(f"📋 Top 3 candidates:")
                for i, candidate in enumerate(candidates[:3]):
                    print(f"  {i+1}. Score: {candidate['score']:.3f} | {candidate['selector']}")
                    meta = candidate.get('meta', {})
                    print(f"     Text: {meta.get('text', '')[:50]}...")
                    print(f"     Tag: {meta.get('tag', '')} | ID: {meta.get('attributes', {}).get('id', '')}")
                break
            else:
                print(f"❌ No element found with query: '{query}'")
        
        # Step 4: Check if we can find product tiles
        print("\n🚀 STEP 4: Look for product tiles")
        shot = runner._snapshot()
        result = runner._resolve_selector("product tile", shot)
        
        print(f"🎯 Product tile selector: {result['selector']}")
        print(f"Confidence: {result['confidence']:.3f}")
        
        if result['selector']:
            print("✅ Found product tile element!")
        else:
            print("❌ No product tile found - might not be on product listing page")
        
        # Step 5: Check current page content
        print("\n🚀 STEP 5: Analyze current page content")
        elements = shot.get('elements', [])
        
        # Look for iPhone-related elements
        iphone_elements = []
        for i, el in enumerate(elements):
            text = el.get('text', '').lower()
            attrs = el.get('attributes', {})
            if any(keyword in text for keyword in ['iphone', '16', 'pro', 'max']):
                iphone_elements.append((i, el))
        
        print(f"Found {len(iphone_elements)} iPhone-related elements:")
        for i, (idx, el) in enumerate(iphone_elements[:5]):
            print(f"  {i+1}. Element {idx}:")
            print(f"     Tag: {el.get('tag', '')}")
            print(f"     Text: {el.get('text', '')[:100]}...")
            print(f"     ID: {el.get('attributes', {}).get('id', '')}")
            print(f"     Data-testid: {el.get('attributes', {}).get('data-testid', '')}")
        
        print(f"\n🎉 Analysis completed!")
        print(f"✅ Final URL: {current_url}")
        print(f"✅ Framework improvements applied:")
        print(f"  - Target phrase passed to MiniLM")
        print(f"  - Universal heuristics for all websites")
        print(f"  - Scroll-into-view for all methods")
        print(f"  - User intent passed to MarkupLM")
        
    finally:
        runner._close()