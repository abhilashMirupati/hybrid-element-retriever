#!/usr/bin/env python3
"""
Test what happens to elements when passed to pipeline
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from her.core.runner import Runner

def test_pipeline_elements():
    """Test what happens to elements when passed to pipeline."""
    print("🔍 Testing pipeline elements...")
    
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
        
        print(f"📊 Total elements in snapshot: {len(elements)}")
        
        # Check first 5 elements in snapshot
        print("🔍 First 5 elements in snapshot:")
        for i, elem in enumerate(elements[:5]):
            meta = elem.get("meta", {})
            frame_hash = meta.get("frame_hash", "MISSING")
            print(f"  Element {i+1}: tag={elem.get('tag', 'unknown')}, frame_hash={frame_hash}")
        
        # Try to resolve a simple selector
        print("\n🔍 Trying to resolve selector for 'Phones'...")
        try:
            result = runner.resolve_selector("Phones", snapshot)
            print(f"✅ Result: {result}")
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        runner._close()

if __name__ == "__main__":
    test_pipeline_elements()