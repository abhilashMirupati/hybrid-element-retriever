#!/usr/bin/env python3

import os
import sys
sys.path.insert(0, 'src')

# Set up environment
os.environ['HER_MODELS_DIR'] = '/workspace/src/her/models'
os.environ['HER_CACHE_DIR'] = '/workspace/.her_cache'
os.environ['HER_E2E'] = '1'

def debug_dom_capture():
    """Debug what elements are actually captured in DOM snapshot"""
    try:
        from her.runner import Runner
        
        runner = Runner(headless=True)
        
        # Take a snapshot
        print("Taking DOM snapshot...")
        snapshot = runner._snapshot("https://www.verizon.com/")
        
        elements = snapshot.get('elements', [])
        print(f"Total elements captured: {len(elements)}")
        
        # Look for ALL elements with "phones" text (case insensitive)
        phones_elements = []
        for elem in elements:
            text = elem.get('text', '').lower()
            if 'phones' in text:
                phones_elements.append({
                    'text': elem.get('text', ''),
                    'tag': elem.get('tag', ''),
                    'xpath': elem.get('xpath', ''),
                    'attrs': elem.get('attrs', {}),
                    'visible': elem.get('visible', False),
                    'bbox': elem.get('bbox', {})
                })
        
        print(f"\nFound {len(phones_elements)} elements with 'phones' text:")
        for i, elem in enumerate(phones_elements):
            print(f"  {i+1}. Tag: {elem['tag']} | Text: '{elem['text'][:100]}...' | Visible: {elem['visible']}")
            print(f"      XPath: {elem['xpath']}")
            print(f"      Attrs: {elem['attrs']}")
            print(f"      BBox: {elem['bbox']}")
            print()
        
        # Look for elements with href="/smartphones/"
        smartphones_links = []
        for elem in elements:
            attrs = elem.get('attrs', {})
            if attrs.get('href') == '/smartphones/':
                smartphones_links.append({
                    'text': elem.get('text', ''),
                    'tag': elem.get('tag', ''),
                    'xpath': elem.get('xpath', ''),
                    'attrs': attrs,
                    'visible': elem.get('visible', False)
                })
        
        print(f"\nFound {len(smartphones_links)} elements with href='/smartphones/':")
        for i, elem in enumerate(smartphones_links):
            print(f"  {i+1}. Tag: {elem['tag']} | Text: '{elem['text']}' | Visible: {elem['visible']}")
            print(f"      XPath: {elem['xpath']}")
            print(f"      Attrs: {elem['attrs']}")
            print()
        
        # Look for elements with data-quick-link="phones"
        quick_link_phones = []
        for elem in elements:
            attrs = elem.get('attrs', {})
            if attrs.get('data-quick-link') == 'phones':
                quick_link_phones.append({
                    'text': elem.get('text', ''),
                    'tag': elem.get('tag', ''),
                    'xpath': elem.get('xpath', ''),
                    'attrs': attrs,
                    'visible': elem.get('visible', False)
                })
        
        print(f"\nFound {len(quick_link_phones)} elements with data-quick-link='phones':")
        for i, elem in enumerate(quick_link_phones):
            print(f"  {i+1}. Tag: {elem['tag']} | Text: '{elem['text']}' | Visible: {elem['visible']}")
            print(f"      XPath: {elem['xpath']}")
            print(f"      Attrs: {elem['attrs']}")
            print()
        
        runner._close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_dom_capture()