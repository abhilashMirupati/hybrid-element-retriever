#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from her.runner import Runner

def debug_attributes():
    runner = Runner()
    
    # Navigate to Verizon homepage
    print("🌐 Navigating to Verizon homepage...")
    snapshot = runner._snapshot("https://www.verizon.com/")
    
    # Find all A tags
    a_tags = [elem for elem in snapshot.get("elements", []) if elem.get("tag", "").lower() == "a"]
    
    print(f"\n🔍 Found {len(a_tags)} A tags:")
    for i, elem in enumerate(a_tags[:10]):  # Show first 10
        print(f"\n{i+1}. Tag: {elem.get('tag', '')}")
        print(f"   Text: '{elem.get('text', '')}'")
        print(f"   Attrs: {elem.get('attrs', {})}")
        print(f"   XPath: {elem.get('xpath', '')}")
        
        # Check if this is the Phones link
        if 'phones' in elem.get('text', '').lower():
            print(f"   *** THIS IS THE PHONES LINK ***")
            print(f"   Full element: {elem}")
    
    # Specifically look for Phones links
    phones_links = [elem for elem in a_tags if 'phones' in elem.get('text', '').lower()]
    print(f"\n🔍 Found {len(phones_links)} Phones links:")
    for i, elem in enumerate(phones_links):
        print(f"\n{i+1}. Text: '{elem.get('text', '')}'")
        print(f"   Attrs: {elem.get('attrs', {})}")
        print(f"   XPath: {elem.get('xpath', '')}")
        print(f"   Full element: {elem}")
    
    runner._close()

if __name__ == "__main__":
    debug_attributes()