#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, 'src')

from her.runner import Runner

def debug_elements():
    runner = Runner()
    
    try:
        # Navigate to Verizon homepage and get snapshot
        snapshot = runner._snapshot("https://www.verizon.com/")
        elements = snapshot.get("elements", [])
        
        # Find all elements with "phones" text
        phones_elements = []
        for elem in elements:
            text = elem.get('text', '').lower()
            if 'phones' in text:
                phones_elements.append({
                    'tag': elem.get('tag', ''),
                    'text': elem.get('text', ''),
                    'xpath': elem.get('xpath', ''),
                    'attributes': elem.get('attributes', {}),
                    'visible': elem.get('visible', False),
                    'role': elem.get('role', ''),
                    'raw_elem': elem  # Include full element for debugging
                })
        
        print(f"Found {len(phones_elements)} elements with 'phones' text:")
        for i, elem in enumerate(phones_elements):
            print(f"  {i+1}. Tag: {elem['tag']} | Text: '{elem['text'][:50]}...' | Visible: {elem['visible']}")
            print(f"      XPath: {elem['xpath'][:80]}...")
            print(f"      Attributes: {elem['attributes']}")
            print(f"      Role: {elem['role']}")
            if elem['tag'] == 'A':
                print(f"      RAW ELEMENT: {elem['raw_elem']}")
            print()
    
    finally:
        runner._close()

if __name__ == "__main__":
    debug_elements()