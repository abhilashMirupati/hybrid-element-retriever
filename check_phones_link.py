#!/usr/bin/env python3

import os
import sys
sys.path.insert(0, 'src')

# Set up environment
os.environ['HER_MODELS_DIR'] = '/workspace/src/her/models'
os.environ['HER_CACHE_DIR'] = '/workspace/.her_cache'
os.environ['HER_E2E'] = '1'

def check_phones_link():
    """Check if the exact Phones link exists on the page"""
    try:
        from her.runner import Runner
        
        runner = Runner(headless=True)
        
        # Take a snapshot of the page
        print("Opening https://www.verizon.com/...")
        snapshot = runner._snapshot("https://www.verizon.com/")
        
        elements = snapshot.get('elements', [])
        print(f"Total elements captured: {len(elements)}")
        print(f"Current URL: {runner._page.url}")
        
        # Look for the EXACT Phones link
        target_phones_link = {
            'tag': 'A',
            'href': '/smartphones/',
            'data-quick-link': 'phones',
            'text': 'Phones'
        }
        
        found_phones_links = []
        for elem in elements:
            if elem.get('tag', '').upper() == 'A':
                attrs = elem.get('attrs', {})
                text = elem.get('text', '').strip()
                
                # Check if this matches our target
                if (attrs.get('href') == '/smartphones/' and 
                    attrs.get('data-quick-link') == 'phones' and
                    text == 'Phones'):
                    found_phones_links.append({
                        'text': text,
                        'tag': elem.get('tag', ''),
                        'xpath': elem.get('xpath', ''),
                        'attrs': attrs,
                        'visible': elem.get('visible', False),
                        'bbox': elem.get('bbox', {})
                    })
        
        print(f"\n🎯 Found {len(found_phones_links)} EXACT Phones links:")
        for i, elem in enumerate(found_phones_links):
            print(f"  {i+1}. ✅ EXACT MATCH FOUND!")
            print(f"      Tag: {elem['tag']}")
            print(f"      Text: '{elem['text']}'")
            print(f"      Href: {elem['attrs'].get('href', '')}")
            print(f"      Data-quick-link: {elem['attrs'].get('data-quick-link', '')}")
            print(f"      Visible: {elem['visible']}")
            print(f"      XPath: {elem['xpath']}")
            print(f"      BBox: {elem['bbox']}")
            print(f"      All Attrs: {elem['attrs']}")
            print()
        
        if not found_phones_links:
            print("❌ EXACT Phones link NOT FOUND!")
            print("\nLooking for similar links...")
            
            # Look for any links with href="/smartphones/"
            smartphones_links = []
            for elem in elements:
                if elem.get('tag', '').upper() == 'A':
                    attrs = elem.get('attrs', {})
                    if attrs.get('href') == '/smartphones/':
                        smartphones_links.append({
                            'text': elem.get('text', '').strip(),
                            'tag': elem.get('tag', ''),
                            'xpath': elem.get('xpath', ''),
                            'attrs': attrs,
                            'visible': elem.get('visible', False)
                        })
            
            print(f"Found {len(smartphones_links)} links with href='/smartphones/':")
            for i, elem in enumerate(smartphones_links):
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
    check_phones_link()