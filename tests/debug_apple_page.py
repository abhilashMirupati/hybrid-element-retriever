"""Debug script to see what's actually on the Apple phones page."""

import os
from her.runner import Runner

def debug_apple_page():
    runner = Runner(headless=True)
    
    try:
        # Navigate to Apple phones page
        print("🚀 Opening Apple phones page...")
        runner._snapshot("https://www.verizon.com/smartphones/apple/")
        runner._page.wait_for_timeout(5000)  # Wait longer for page to load
        
        # Take snapshot
        shot = runner._snapshot()
        elements = shot.get("elements", [])
        
        print(f"\n📊 Total elements: {len(elements)}")
        
        # Look for product-related elements
        product_elements = []
        for i, el in enumerate(elements):
            text = el.get("text", "").lower()
            tag = el.get("tag", "").lower()
            attrs = el.get("attributes", {})
            
            # Look for product indicators
            if any(keyword in text for keyword in ["iphone", "16", "pro", "max", "plus", "mini", "se"]):
                product_elements.append((i, el))
            elif tag in ["button", "a", "div"] and any(keyword in str(attrs).lower() for keyword in ["product", "card", "item", "phone"]):
                product_elements.append((i, el))
        
        print(f"\n📱 Found {len(product_elements)} product-related elements:")
        for i, (idx, el) in enumerate(product_elements[:15]):  # Show top 15
            print(f"\n{i+1}. Element {idx}:")
            print(f"   Tag: {el.get('tag', '')}")
            print(f"   Text: {el.get('text', '')[:150]}...")
            print(f"   Role: {el.get('attributes', {}).get('role', '')}")
            print(f"   Class: {el.get('attributes', {}).get('class', '')}")
            print(f"   ID: {el.get('attributes', {}).get('id', '')}")
            print(f"   Visible: {el.get('visible', False)}")
            print(f"   XPath: {el.get('xpath', '')}")
        
        # Look for clickable elements
        clickable_elements = []
        for i, el in enumerate(elements):
            tag = el.get("tag", "").lower()
            attrs = el.get("attributes", {})
            role = attrs.get("role", "").lower()
            
            if tag in ["button", "a"] or role in ["button", "link"]:
                clickable_elements.append((i, el))
        
        print(f"\n🖱️  Found {len(clickable_elements)} clickable elements:")
        for i, (idx, el) in enumerate(clickable_elements[:10]):  # Show top 10
            print(f"\n{i+1}. Element {idx}:")
            print(f"   Tag: {el.get('tag', '')}")
            print(f"   Text: {el.get('text', '')[:100]}...")
            print(f"   Role: {el.get('attributes', {}).get('role', '')}")
            print(f"   XPath: {el.get('xpath', '')}")
        
        # Check current URL
        current_url = runner._page.url
        print(f"\n🌐 Current URL: {current_url}")
        
        # Check page title
        try:
            title = runner._page.title()
            print(f"📄 Page title: {title}")
        except:
            print("📄 Could not get page title")
        
    finally:
        runner._close()

if __name__ == "__main__":
    debug_apple_page()