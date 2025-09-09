#!/usr/bin/env python3

import os
import sys
sys.path.insert(0, 'src')

from her.runner import Runner

def debug_phones_click():
    """Debug the Phones button click issue"""
    runner = Runner(headless=False)  # Run in visible mode
    
    try:
        # Step 1: Open Verizon.com
        print("Step 1: Opening https://www.verizon.com/")
        snapshot = runner._snapshot("https://www.verizon.com/")
        print(f"Found {len(snapshot.get('elements', []))} elements")
        
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
        
        # Try to click the element
        if resolved.get('selector'):
            print("Attempting to click the element...")
            try:
                runner._do_action("click", resolved.get('selector'), None, resolved.get('promo', {}))
                print("Click successful!")
                
                # Wait a bit and check URL
                import time
                time.sleep(3)
                current_url = runner._page.url
                print(f"Current URL after click: {current_url}")
                
            except Exception as e:
                print(f"Click failed: {e}")
        else:
            print("No selector found!")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Don't close the browser immediately so we can see what happened
        print("\nKeeping browser open for inspection...")
        input("Press Enter to close browser...")
        runner._close()

if __name__ == "__main__":
    debug_phones_click()