#!/usr/bin/env python3
"""
Debug script to find the exact "Phones" button on Verizon page
"""

import os
import sys
import time
import subprocess
from datetime import datetime

def debug_phones_button():
    """Debug why 'Phones' button is not being found correctly"""
    print("🔍 DEBUGGING PHONES BUTTON ON VERIZON PAGE")
    print("=" * 80)
    
    test_script = """
import os
import sys
import time
sys.path.insert(0, 'src')

# Set environment variables
os.environ['HER_CANONICAL_MODE'] = 'both'
os.environ['HER_USE_HIERARCHY'] = 'false'
os.environ['HER_USE_TWO_STAGE'] = 'false'

from her.runner import Runner

def debug_phones_search():
    try:
        print("🔧 Initializing Runner...")
        runner = Runner()
        print("✅ Runner initialized")
        
        # Take snapshot
        print("\\n📸 Taking snapshot of Verizon page...")
        snapshot = runner._snapshot('https://www.verizon.com/')
        elements = snapshot.get('elements', [])
        print(f"✅ Page loaded with {len(elements)} elements")
        
        # Search for elements containing "Phones" text
        print("\\n🔍 SEARCHING FOR 'PHONES' ELEMENTS:")
        print("=" * 60)
        
        phones_elements = []
        for i, element in enumerate(elements):
            text = element.get('text', '').lower()
            tag = element.get('tag', '')
            xpath = element.get('xpath', '')
            
            if 'phones' in text:
                phones_elements.append({
                    'index': i,
                    'tag': tag,
                    'text': element.get('text', ''),
                    'xpath': xpath,
                    'interactive': element.get('interactive', False),
                    'attrs': element.get('attrs', {})
                })
        
        print(f"Found {len(phones_elements)} elements containing 'phones':")
        for i, elem in enumerate(phones_elements[:10]):  # Show top 10
            print(f"\\n{i+1}. Tag: {elem['tag']}")
            print(f"   Text: '{elem['text']}'")
            print(f"   XPath: {elem['xpath']}")
            print(f"   Interactive: {elem['interactive']}")
            print(f"   Attrs: {elem['attrs']}")
        
        # Search for exact "Phones" text
        print("\\n\\n🎯 SEARCHING FOR EXACT 'PHONES' TEXT:")
        print("=" * 60)
        
        exact_phones = []
        for i, element in enumerate(elements):
            text = element.get('text', '').strip()
            if text == 'Phones':
                exact_phones.append({
                    'index': i,
                    'tag': element.get('tag', ''),
                    'text': text,
                    'xpath': element.get('xpath', ''),
                    'interactive': element.get('interactive', False),
                    'attrs': element.get('attrs', {})
                })
        
        print(f"Found {len(exact_phones)} elements with exact 'Phones' text:")
        for i, elem in enumerate(exact_phones):
            print(f"\\n{i+1}. Tag: {elem['tag']}")
            print(f"   Text: '{elem['text']}'")
            print(f"   XPath: {elem['xpath']}")
            print(f"   Interactive: {elem['interactive']}")
            print(f"   Attrs: {elem['attrs']}")
        
        # Search for navigation elements
        print("\\n\\n🧭 SEARCHING FOR NAVIGATION ELEMENTS:")
        print("=" * 60)
        
        nav_elements = []
        for i, element in enumerate(elements):
            tag = element.get('tag', '').lower()
            attrs = element.get('attrs', {})
            text = element.get('text', '').lower()
            
            # Look for navigation-related elements
            if (tag in ['a', 'button', 'nav'] or 
                'nav' in attrs.get('class', '').lower() or
                'menu' in attrs.get('class', '').lower() or
                'gnav' in attrs.get('id', '').lower() or
                'phones' in text):
                nav_elements.append({
                    'index': i,
                    'tag': element.get('tag', ''),
                    'text': element.get('text', ''),
                    'xpath': element.get('xpath', ''),
                    'interactive': element.get('interactive', False),
                    'attrs': attrs
                })
        
        print(f"Found {len(nav_elements)} navigation-related elements:")
        for i, elem in enumerate(nav_elements[:15]):  # Show top 15
            print(f"\\n{i+1}. Tag: {elem['tag']}")
            print(f"   Text: '{elem['text'][:50]}...'")
            print(f"   XPath: {elem['xpath'][:80]}...")
            print(f"   Interactive: {elem['interactive']}")
            print(f"   ID: {elem['attrs'].get('id', 'N/A')}")
            print(f"   Class: {elem['attrs'].get('class', 'N/A')}")
        
        # Test the actual query
        print("\\n\\n🔍 TESTING ACTUAL QUERY:")
        print("=" * 60)
        
        query = 'Click on the "Phones" button'
        result = runner._resolve_selector(query, snapshot)
        
        print(f"Query: '{query}'")
        print(f"Selected XPath: {result.get('selector', 'N/A')}")
        print(f"Confidence: {result.get('confidence', 0.0):.3f}")
        print(f"Strategy: {result.get('strategy', 'unknown')}")
        
        # Show top candidates
        candidates = result.get('candidates', [])
        if candidates:
            print(f"\\nTop 5 candidates:")
            for i, candidate in enumerate(candidates[:5]):
                text = candidate.get('text', '')[:50]
                xpath = candidate.get('xpath', '')[:80]
                score = candidate.get('score', 0.0)
                tag = candidate.get('tag', '')
                interactive = candidate.get('interactive', False)
                
                print(f"{i+1}. Score: {score:6.3f} | {tag:8s} | {'✓' if interactive else '✗'} | '{text}...'")
                print(f"     XPath: {xpath}...")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        try:
            runner.cleanup_models()
            runner._browser.close()
            runner._playwright.stop()
            print("\\n🧹 Cleanup completed")
        except:
            pass

if __name__ == "__main__":
    success = debug_phones_search()
    exit(0 if success else 1)
"""
    
    # Run the debug test
    print(f"🚀 Starting phones button debug at: {datetime.now().isoformat()}")
    process = subprocess.run(['python', '-c', test_script], 
                           capture_output=True, text=True, 
                           env=os.environ.copy())
    
    print("STDOUT:")
    print(process.stdout)
    
    if process.stderr:
        print("STDERR:")
        print(process.stderr)
    
    print(f"\\n🏁 Debug completed at: {datetime.now().isoformat()}")
    print(f"Exit code: {process.returncode}")
    
    return process.returncode == 0

def main():
    """Main debug function"""
    print("🚀 VERIZON PHONES BUTTON DEBUG")
    print("=" * 80)
    
    success = debug_phones_button()
    
    print("\\n🏁 PHONES BUTTON DEBUG COMPLETED")
    return success

if __name__ == "__main__":
    main()