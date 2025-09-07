#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from her.runner import Runner

def debug_text_matching():
    runner = Runner()
    
    # Navigate to Verizon homepage
    print("🌐 Navigating to Verizon homepage...")
    snapshot = runner._snapshot("https://www.verizon.com/")
    
    elements = snapshot.get("elements", [])
    
    # Find all elements with "phones" text
    phones_elements = []
    for i, elem in enumerate(elements):
        text = elem.get('text', '').lower()
        if 'phones' in text:
            phones_elements.append((i, elem))
    
    print(f"\n🔍 Found {len(phones_elements)} elements with 'phones' text:")
    for i, (idx, elem) in enumerate(phones_elements):
        print(f"\n{i+1}. Index: {idx}")
        print(f"   Tag: {elem.get('tag', '')}")
        print(f"   Text: '{elem.get('text', '')}'")
        print(f"   Text (lower): '{elem.get('text', '').lower()}'")
        print(f"   Contains 'phones': {'phones' in elem.get('text', '').lower()}")
        print(f"   XPath: {elem.get('xpath', '')}")
        
        # Check if this is the exact "Phones" link
        if elem.get('tag', '').lower() == 'a' and elem.get('text', '').strip() == 'Phones':
            print(f"   *** THIS IS THE EXACT PHONES LINK ***")
    
    runner._close()

if __name__ == "__main__":
    debug_text_matching()