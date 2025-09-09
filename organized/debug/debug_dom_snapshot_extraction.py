#!/usr/bin/env python3

import os
import sys
sys.path.insert(0, 'src')

# Set up environment
os.environ['HER_MODELS_DIR'] = '/workspace/src/her/models'
os.environ['HER_CACHE_DIR'] = '/workspace/.her_cache'
os.environ['HER_E2E'] = '1'

def debug_dom_snapshot():
    """Debug what elements are captured in DOM snapshot"""
    try:
        from her.runner import Runner
        
        runner = Runner(headless=True)
        
        # Take a snapshot
        print("Taking DOM snapshot...")
        snapshot = runner._snapshot("https://www.verizon.com/")
        
        elements = snapshot.get('elements', [])
        print(f"Total elements captured: {len(elements)}")
        
        # Look for elements with "Phones" text
        phones_elements = []
        for elem in elements:
            text = elem.get('text', '').lower()
            if 'phones' in text:
                phones_elements.append({
                    'text': elem.get('text', ''),
                    'tag': elem.get('tag', ''),
                    'xpath': elem.get('xpath', ''),
                    'attrs': elem.get('attrs', {}),
                    'attributes': elem.get('attributes', {})
                })
        
        print(f"\nFound {len(phones_elements)} elements with 'phones' text:")
        for i, elem in enumerate(phones_elements):
            print(f"  {i+1}. Tag: {elem['tag']} | Text: '{elem['text']}'")
            print(f"      XPath: {elem['xpath'][:100]}...")
            print(f"      Attrs: {elem['attrs']}")
            print(f"      Attributes: {elem['attributes']}")
            print()
        
        runner._close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_dom_snapshot()