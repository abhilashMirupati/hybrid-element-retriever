#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from her.runner import Runner

def debug_phones_page():
    runner = Runner()
    
    # Navigate to phones page
    print("🌐 Navigating to phones page...")
    snapshot = runner._snapshot("https://www.verizon.com/smartphones/")
    
    # Find all elements with "iPhone 16 Pro" text
    iphone_elements = []
    for i, elem in enumerate(snapshot.get("elements", [])):
        text = elem.get('text', '').lower()
        if 'iphone 16 pro' in text and 'iphone 16 pro max' not in text:
            iphone_elements.append((i, elem))
    
    print(f"\n🔍 Found {len(iphone_elements)} iPhone 16 Pro elements:")
    for i, (idx, elem) in enumerate(iphone_elements):
        print(f"\n{i+1}. Index: {idx}")
        print(f"   Tag: {elem.get('tag', '')}")
        print(f"   Text: '{elem.get('text', '')[:100]}...'")
        print(f"   XPath: {elem.get('xpath', '')}")
        print(f"   Attrs: {elem.get('attrs', {})}")
        
        # Check if this is clickable
        tag = elem.get('tag', '').lower()
        attrs = elem.get('attrs', {})
        is_clickable = (tag in ['a', 'button'] or 
                       attrs.get('onclick') or 
                       attrs.get('href') or
                       attrs.get('role') in ['button', 'link'])
        print(f"   Clickable: {is_clickable}")
    
    # Find all A tags
    a_tags = [elem for elem in snapshot.get("elements", []) if elem.get("tag", "").lower() == "a"]
    print(f"\n🔍 Found {len(a_tags)} A tags:")
    for i, elem in enumerate(a_tags[:10]):  # Show first 10
        print(f"\n{i+1}. Tag: {elem.get('tag', '')}")
        print(f"   Text: '{elem.get('text', '')}'")
        print(f"   Href: {elem.get('attrs', {}).get('href', 'N/A')}")
        print(f"   XPath: {elem.get('xpath', '')}")
    
    # Find iPhone A tags
    iphone_links = [elem for elem in a_tags if 'iphone' in elem.get('text', '').lower() or 'iphone' in elem.get('attrs', {}).get('href', '').lower()]
    print(f"\n🔍 Found {len(iphone_links)} iPhone A tags:")
    for i, elem in enumerate(iphone_links):
        print(f"\n{i+1}. Tag: {elem.get('tag', '')}")
        print(f"   Text: '{elem.get('text', '')}'")
        print(f"   Href: {elem.get('attrs', {}).get('href', 'N/A')}")
        print(f"   XPath: {elem.get('xpath', '')}")
    
    runner._close()

if __name__ == "__main__":
    debug_phones_page()