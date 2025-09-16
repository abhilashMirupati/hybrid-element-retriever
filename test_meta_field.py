#!/usr/bin/env python3
"""
Test meta field preservation
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from her.core.runner import Runner

def test_meta_field():
    """Test meta field preservation."""
    print("🔍 Testing meta field preservation...")
    
    # Set environment
    os.environ["HER_USE_SEMANTIC_SEARCH"] = "true"
    os.environ["HER_CACHE_DIR"] = str(Path(".her_cache").resolve())
    
    # Initialize runner
    runner = Runner(headless=False)
    
    try:
        # Take a snapshot
        print("📸 Taking snapshot...")
        snapshot = runner.snapshot("https://www.verizon.com/")
        elements = snapshot.get("elements", [])
        
        print(f"📊 Total elements: {len(elements)}")
        
        # Check first 5 elements for meta field
        for i, element in enumerate(elements[:5]):
            print(f"Element {i}:")
            print(f"  Has meta: {'meta' in element}")
            if 'meta' in element:
                print(f"  Meta: {element['meta']}")
            print(f"  Tag: {element.get('tag', 'N/A')}")
            print(f"  Text: {element.get('text', 'N/A')[:50]}...")
            print()
        
        # Try to resolve a simple selector
        print("🔍 Trying to resolve selector...")
        try:
            resolved = runner.resolve_selector("Shop", snapshot)
            print(f"✅ Success: {resolved}")
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        runner.close()

if __name__ == "__main__":
    test_meta_field()