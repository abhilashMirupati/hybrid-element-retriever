#!/usr/bin/env python3
"""
🎯 HER Demo - Finding the Best XPath/Selector for Any Element

This script demonstrates how to use HER to find the best selector
for any element on a webpage using natural language.
"""

import json
import sys
from typing import List, Dict, Any


def print_banner():
    """Print a nice banner."""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║     🎯 Hybrid Element Retriever (HER) Demo 🎯           ║
    ║                                                          ║
    ║     Find the best XPath using natural language!         ║
    ╚══════════════════════════════════════════════════════════╝
    """)


def setup_client():
    """Setup and return HER client."""
    try:
        from her.cli_api import HybridClient
        print("✅ HER imported successfully")
        return HybridClient(headless=False)  # Show browser for demo
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("\n📦 Please install HER first:")
        print("   pip install playwright numpy pydantic")
        print("   python -m playwright install chromium")
        sys.exit(1)


def demo_find_best_xpath():
    """Demo: Find best XPath for common elements."""
    print("\n" + "="*60)
    print("📍 DEMO 1: Finding Best XPath/Selectors")
    print("="*60)
    
    client = setup_client()
    
    # Example website (you can change this)
    url = "https://www.google.com"
    
    # Elements to find
    elements_to_find = [
        "search box",
        "search button",
        "I'm Feeling Lucky button",
        "Gmail link",
    ]
    
    print(f"\n🌐 Analyzing: {url}\n")
    
    for element_desc in elements_to_find:
        print(f"\n🔍 Looking for: '{element_desc}'")
        print("-" * 40)
        
        try:
            results = client.query(element_desc, url=url)
            
            if results:
                best = results[0]
                print(f"✅ Found!")
                print(f"   Best Selector: {best['selector']}")
                print(f"   Confidence: {best['score']:.1%}")
                print(f"   Element Type: {best['element']['tag']}")
                
                if best['element'].get('text'):
                    print(f"   Text: {best['element']['text'][:50]}")
                
                # Show alternatives
                if len(results) > 1:
                    print(f"\n   Alternatives:")
                    for alt in results[1:3]:  # Show top 3
                        print(f"   - {alt['selector']} (confidence: {alt['score']:.1%})")
            else:
                print(f"❌ No elements found for '{element_desc}'")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    client.close()


def demo_interactive_mode():
    """Demo: Interactive mode where user can query any element."""
    print("\n" + "="*60)
    print("📍 DEMO 2: Interactive Element Finder")
    print("="*60)
    
    client = setup_client()
    
    print("\n💡 Enter a URL and describe elements in natural language!")
    print("   Example: 'the main navigation menu'")
    print("   Type 'quit' to exit\n")
    
    # Get URL
    url = input("🌐 Enter URL (or press Enter for google.com): ").strip()
    if not url:
        url = "https://www.google.com"
    
    print(f"\n📱 Opening {url}...\n")
    
    while True:
        # Get element description
        element = input("🔍 Describe element to find (or 'quit'): ").strip()
        
        if element.lower() in ['quit', 'exit', 'q']:
            break
        
        if not element:
            continue
        
        try:
            # Query for the element
            results = client.query(element, url=url)
            
            if results:
                print(f"\n✅ Found {len(results)} match(es)!\n")
                
                # Show top 3 results
                for i, result in enumerate(results[:3], 1):
                    print(f"Match #{i}:")
                    print(f"  Selector: {result['selector']}")
                    print(f"  Confidence: {result['score']:.1%}")
                    print(f"  Type: <{result['element']['tag']}>")
                    
                    # Show element details
                    elem = result['element']
                    if elem.get('text'):
                        print(f"  Text: {elem['text'][:50]}")
                    if elem.get('id'):
                        print(f"  ID: {elem['id']}")
                    if elem.get('classes'):
                        print(f"  Classes: {', '.join(elem['classes'][:3])}")
                    print()
                
                # Ask if user wants to click
                if results[0]['element']['tag'] in ['button', 'a', 'input']:
                    action = input("💫 Want to click this element? (y/n): ").strip()
                    if action.lower() == 'y':
                        action_result = client.act(f"Click {element}")
                        if action_result['status'] == 'success':
                            print("✅ Clicked successfully!")
                        else:
                            print(f"❌ Click failed: {action_result['explanation']}")
            else:
                print(f"\n❌ No elements found for '{element}'")
                print("💡 Try being more specific or using different words\n")
                
        except Exception as e:
            print(f"\n❌ Error: {e}\n")
    
    client.close()
    print("\n👋 Goodbye!")


def demo_common_scenarios():
    """Demo: Common web scraping/testing scenarios."""
    print("\n" + "="*60)
    print("📍 DEMO 3: Common Scenarios")
    print("="*60)
    
    scenarios = {
        "Login Form": [
            ("email input field", "Find email input"),
            ("password field", "Find password input"),
            ("login button", "Find submit button"),
            ("remember me checkbox", "Find checkbox"),
            ("forgot password link", "Find reset link")
        ],
        "E-commerce": [
            ("search bar", "Find search input"),
            ("add to cart button", "Find add button"),
            ("price text", "Find price element"),
            ("product image", "Find main image"),
            ("reviews section", "Find reviews")
        ],
        "Navigation": [
            ("main menu", "Find navigation"),
            ("home link", "Find home"),
            ("hamburger menu icon", "Find mobile menu"),
            ("footer links", "Find footer"),
            ("breadcrumb navigation", "Find breadcrumbs")
        ]
    }
    
    client = setup_client()
    
    print("\nSelect a scenario:")
    for i, scenario in enumerate(scenarios.keys(), 1):
        print(f"  {i}. {scenario}")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice in ['1', '2', '3']:
        scenario_name = list(scenarios.keys())[int(choice) - 1]
        elements = scenarios[scenario_name]
        
        url = input(f"\nEnter URL to test {scenario_name} elements: ").strip()
        if not url:
            print("❌ URL required")
            return
        
        print(f"\n🔍 Looking for {scenario_name} elements on {url}\n")
        
        for element_desc, description in elements:
            print(f"\n📌 {description}: '{element_desc}'")
            
            try:
                results = client.query(element_desc, url=url)
                
                if results:
                    best = results[0]
                    print(f"   ✅ Found: {best['selector']}")
                    print(f"   Confidence: {best['score']:.1%}")
                else:
                    print(f"   ❌ Not found")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
    
    client.close()


def main():
    """Main demo runner."""
    print_banner()
    
    print("\nSelect a demo:")
    print("  1. Find Best XPath (Automated)")
    print("  2. Interactive Element Finder")
    print("  3. Common Scenarios")
    print("  4. Run All Demos")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == '1':
        demo_find_best_xpath()
    elif choice == '2':
        demo_interactive_mode()
    elif choice == '3':
        demo_common_scenarios()
    elif choice == '4':
        demo_find_best_xpath()
        demo_interactive_mode()
    else:
        print("❌ Invalid choice")
    
    print("\n✨ Demo complete! Check SETUP_GUIDE.md for more examples.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()