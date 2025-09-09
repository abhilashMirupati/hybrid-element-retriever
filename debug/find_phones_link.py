#!/usr/bin/env python3

import os
import sys
sys.path.insert(0, 'src')

# Set up environment
os.environ['HER_MODELS_DIR'] = '/workspace/src/her/models'
os.environ['HER_CACHE_DIR'] = '/workspace/.her_cache'
os.environ['HER_E2E'] = '1'

def find_phones_link():
    """Find the actual Phones link in the DOM"""
    try:
        from her.runner import Runner
        
        runner = Runner(headless=True)
        
        # Take a snapshot
        print("Taking DOM snapshot...")
        snapshot = runner._snapshot("https://www.verizon.com/")
        
        elements = snapshot.get('elements', [])
        print(f"Total elements captured: {len(elements)}")
        
        # Look for the specific Phones link
        phones_links = []
        for elem in elements:
            attrs = elem.get('attrs', {}) or elem.get('attributes', {})
            text = elem.get('text', '').lower()
            
            # Check for the specific attributes
            if (attrs.get('href') == '/smartphones/' or 
                attrs.get('data-quick-link') == 'phones' or
                'phones' in text):
                phones_links.append({
                    'text': elem.get('text', ''),
                    'tag': elem.get('tag', ''),
                    'xpath': elem.get('xpath', ''),
                    'attrs': attrs,
                    'visible': elem.get('visible', False)
                })
        
        print(f"\nFound {len(phones_links)} potential Phones links:")
        for i, elem in enumerate(phones_links):
            print(f"  {i+1}. Tag: {elem['tag']} | Text: '{elem['text']}' | Visible: {elem['visible']}")
            print(f"      XPath: {elem['xpath'][:100]}...")
            print(f"      Attrs: {elem['attrs']}")
            print()
        
        runner._close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    find_phones_link()