#!/usr/bin/env python3
"""
Debug script to find navigation elements and understand page structure
"""
import os
import sys
from pathlib import Path
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set environment variables
os.environ["HER_E2E"] = "1"

def debug_navigation_elements():
    """Debug navigation elements on Verizon page"""
    from her.runner import Runner
    
    print("🔍 Debugging navigation elements...")
    
    runner = Runner(headless=False)  # Run visible to see what's happening
    
    try:
        # Navigate to Verizon homepage
        print("📱 Navigating to Verizon homepage...")
        snapshot = runner._snapshot("https://www.verizon.com/")
        
        # Wait for page to fully load
        print("⏳ Waiting for page to load...")
        time.sleep(5)
        
        # Get fresh snapshot after waiting
        snapshot = runner._snapshot()
        elements = snapshot.get('elements', [])
        print(f"Total elements after wait: {len(elements)}")
        
        # Look for navigation-related elements
        print("\n🔍 Looking for navigation elements...")
        
        # Check for common navigation patterns
        nav_keywords = ['menu', 'nav', 'button', 'link', 'phone', 'smartphone', 'mobile', 'device', 'shop', 'products']
        
        for keyword in nav_keywords:
            matches = []
            for i, element in enumerate(elements):
                text = element.get('text', '').strip().lower()
                tag = element.get('tag', '').lower()
                xpath = element.get('xpath', '')
                attributes = element.get('attributes', {})
                
                if keyword in text or keyword in tag or any(keyword in str(v).lower() for v in attributes.values()):
                    matches.append({
                        'index': i,
                        'text': element.get('text', '')[:100],
                        'tag': tag,
                        'xpath': xpath[:100],
                        'attributes': attributes
                    })
            
            if matches:
                print(f"\n📋 '{keyword}' matches ({len(matches)}):")
                for match in matches[:5]:  # Show top 5
                    print(f"  - Tag: {match['tag']:8s} | Text: '{match['text']}'")
                    print(f"    XPath: {match['xpath']}")
                    if match['attributes']:
                        print(f"    Attrs: {match['attributes']}")
        
        # Look for interactive elements
        print("\n🔍 Looking for interactive elements...")
        interactive_tags = ['button', 'a', 'input', 'select', 'div', 'span']
        interactive_elements = []
        
        for element in elements:
            tag = element.get('tag', '').lower()
            attributes = element.get('attributes', {})
            text = element.get('text', '').strip()
            
            # Check if element is likely interactive
            is_interactive = (
                tag in interactive_tags and (
                    'onclick' in attributes or
                    'href' in attributes or
                    'role' in attributes or
                    'tabindex' in attributes or
                    'aria-label' in attributes or
                    'data-testid' in attributes or
                    'class' in attributes and any(cls in str(attributes['class']).lower() 
                                                for cls in ['button', 'link', 'menu', 'nav', 'click'])
                )
            )
            
            if is_interactive and text:
                interactive_elements.append({
                    'text': text[:50],
                    'tag': tag,
                    'xpath': element.get('xpath', '')[:100],
                    'attributes': attributes
                })
        
        print(f"Found {len(interactive_elements)} interactive elements:")
        for elem in interactive_elements[:20]:
            print(f"  - {elem['tag']:8s}: '{elem['text']}'")
            print(f"    XPath: {elem['xpath']}")
        
        # Look for menu/header structure
        print("\n🔍 Looking for header/menu structure...")
        header_elements = []
        for element in elements:
            tag = element.get('tag', '').lower()
            attributes = element.get('attributes', {})
            text = element.get('text', '').strip()
            
            if (tag in ['header', 'nav', 'div', 'ul', 'li'] and 
                any(keyword in str(attributes.get('class', '')).lower() 
                    for keyword in ['header', 'nav', 'menu', 'gnav', 'top'])):
                header_elements.append({
                    'text': text[:50],
                    'tag': tag,
                    'xpath': element.get('xpath', '')[:100],
                    'class': attributes.get('class', ''),
                    'id': attributes.get('id', '')
                })
        
        print(f"Found {len(header_elements)} header/menu elements:")
        for elem in header_elements[:15]:
            print(f"  - {elem['tag']:8s}: '{elem['text']}' | Class: {elem['class'][:30]}")
            print(f"    XPath: {elem['xpath']}")
        
        return elements
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        try:
            runner._page.close()
        except:
            pass

if __name__ == "__main__":
    print("🚀 Starting navigation debugging...")
    elements = debug_navigation_elements()
    print(f"\n🎯 Found {len(elements)} total elements")