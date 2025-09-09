#!/usr/bin/env python3

import os
import sys
sys.path.insert(0, 'src')

from her.runner import Runner

def debug_phones_click():
    """Debug the Phones button click issue"""
    runner = Runner(headless=True)  # Run in headless mode
    
    try:
        # Step 1: Open Verizon.com
        print("Step 1: Opening https://www.verizon.com/")
        snapshot = runner._snapshot("https://www.verizon.com/")
        print(f"Found {len(snapshot.get('elements', []))} elements")
        
        # Look for elements with "Phones" text
        phones_elements = []
        for elem in snapshot.get('elements', []):
            text = elem.get('text', '').lower()
            if 'phones' in text:
                phones_elements.append({
                    'text': elem.get('text', ''),
                    'tag': elem.get('tag', ''),
                    'xpath': elem.get('xpath', ''),
                    'attrs': elem.get('attrs', {}),
                    'visible': elem.get('visible', False)
                })
        
        print(f"\nFound {len(phones_elements)} elements containing 'phones':")
        for i, elem in enumerate(phones_elements[:5]):  # Show first 5
            print(f"  {i+1}. Text: '{elem['text']}'")
            print(f"     Tag: {elem['tag']}")
            print(f"     Visible: {elem['visible']}")
            print(f"     XPath: {elem['xpath']}")
            print(f"     Attrs: {elem['attrs']}")
            print()
        
        # Step 2: Try to find and click Phones button
        print("\nStep 2: Looking for 'Phones' button")
        resolved = runner._resolve_selector("Click on Phones btn in top", snapshot)
        print(f"Selector: {resolved.get('selector', '')}")
        print(f"Confidence: {resolved.get('confidence', 0.0)}")
        print(f"Candidates: {len(resolved.get('candidates', []))}")
        
        # Show top 3 candidates
        for i, candidate in enumerate(resolved.get('candidates', [])[:3]):
            print(f"  {i+1}. Score: {candidate.get('score', 0.0):.3f}")
            print(f"     Selector: {candidate.get('selector', '')}")
            print(f"     Meta: {candidate.get('meta', {})}")
            print()
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        runner._close()

if __name__ == "__main__":
    debug_phones_click()