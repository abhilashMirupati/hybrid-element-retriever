"""Debug script to see what iPhone elements are available."""

import os
from her.runner import Runner

def debug_iphone_elements():
    runner = Runner(headless=True)
    
    try:
        # Navigate to Apple phones page
        print("🚀 Opening Apple phones page...")
        runner._snapshot("https://www.verizon.com/smartphones/apple/")
        runner._page.wait_for_timeout(3000)
        
        # Take snapshot
        shot = runner._snapshot()
        elements = shot.get("elements", [])
        
        print(f"\n📊 Total elements: {len(elements)}")
        
        # Find iPhone-related elements
        iphone_elements = []
        for i, el in enumerate(elements):
            text = el.get("text", "").lower()
            if "iphone" in text or "16" in text or "pro" in text:
                iphone_elements.append((i, el))
        
        print(f"\n🍎 Found {len(iphone_elements)} iPhone-related elements:")
        for i, (idx, el) in enumerate(iphone_elements[:10]):  # Show top 10
            print(f"\n{i+1}. Element {idx}:")
            print(f"   Tag: {el.get('tag', '')}")
            print(f"   Text: {el.get('text', '')[:100]}...")
            print(f"   Role: {el.get('attributes', {}).get('role', '')}")
            print(f"   Class: {el.get('attributes', {}).get('class', '')}")
            print(f"   ID: {el.get('attributes', {}).get('id', '')}")
            print(f"   Visible: {el.get('visible', False)}")
            print(f"   XPath: {el.get('xpath', '')}")
        
        # Test the query
        print(f"\n🔍 Testing query: 'Apple iPhone 16 Pro'")
        result = runner._resolve_selector("Apple iPhone 16 Pro", shot)
        
        print(f"\n🎯 Selected element:")
        print(f"   Selector: {result['selector']}")
        print(f"   Confidence: {result['confidence']:.3f}")
        print(f"   Reasons: {result.get('reasons', [])}")
        
        # Show all candidates
        print(f"\n📋 All candidates:")
        for i, candidate in enumerate(result.get("candidates", [])[:10]):
            print(f"   {i+1}. Score: {candidate['score']:.3f} | {candidate['selector']}")
            meta = candidate.get('meta', {})
            print(f"      Text: {meta.get('text', '')[:50]}...")
            print(f"      Tag: {meta.get('tag', '')} | Role: {meta.get('role', '')}")
        
    finally:
        runner._close()

if __name__ == "__main__":
    debug_iphone_elements()