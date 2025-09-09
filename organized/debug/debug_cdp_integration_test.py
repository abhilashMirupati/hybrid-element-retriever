#!/usr/bin/env python3
"""Debug CDP accessibility integration."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from her.runner import Runner

def test_cdp_integration():
    """Test CDP accessibility integration."""
    print("🔍 Testing CDP Accessibility Integration...")
    
    runner = Runner()
    
    try:
        # Navigate to a simple page
        runner.navigate("https://www.verizon.com/smartphones/")
        print("✅ Navigation successful")
        
        # Test snapshot with CDP integration
        snapshot = runner._inline_snapshot()
        elements = snapshot.get("elements", [])
        
        print(f"📊 Snapshot Results:")
        print(f"   Total elements: {len(elements)}")
        
        if elements:
            # Show first few elements
            print(f"\n🔍 First 5 elements:")
            for i, elem in enumerate(elements[:5]):
                print(f"   {i+1}. Tag: {elem.get('tag', 'N/A')}")
                print(f"      Text: '{elem.get('text', '')[:50]}...'")
                print(f"      XPath: {elem.get('xpath', 'N/A')}")
                print(f"      Interactive: {elem.get('interactive', False)}")
                print(f"      Role: {elem.get('role', 'N/A')}")
                print(f"      ID: {elem.get('attrs', {}).get('id', 'N/A')}")
                print()
        
        # Look for Apple filter button specifically
        apple_elements = [e for e in elements if 'apple' in e.get('text', '').lower() and e.get('interactive', False)]
        print(f"🍎 Apple Interactive Elements: {len(apple_elements)}")
        for i, elem in enumerate(apple_elements[:3]):
            print(f"   {i+1}. Tag: {elem.get('tag', 'N/A')}")
            print(f"      Text: '{elem.get('text', '')}'")
            print(f"      XPath: {elem.get('xpath', 'N/A')}")
            print(f"      ID: {elem.get('attrs', {}).get('id', 'N/A')}")
            print()
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        runner.close()

if __name__ == "__main__":
    test_cdp_integration()