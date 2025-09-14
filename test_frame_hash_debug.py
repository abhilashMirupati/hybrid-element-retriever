#!/usr/bin/env python3
"""
Debug frame_hash issue specifically
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from her.core.runner import Runner

def test_frame_hash_issue():
    """Test the frame_hash issue specifically."""
    print("🔍 Testing frame_hash issue...")
    
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
        
        # Check frame_hash in first 10 elements
        print("🔍 Checking frame_hash in first 10 elements:")
        for i, elem in enumerate(elements[:10]):
            meta = elem.get("meta", {})
            frame_hash = meta.get("frame_hash", "MISSING")
            print(f"  Element {i+1}: tag={elem.get('tag', 'unknown')}, frame_hash={frame_hash}")
            
        # Check if any elements are missing frame_hash
        missing_count = 0
        for elem in elements:
            meta = elem.get("meta", {})
            if "frame_hash" not in meta:
                missing_count += 1
                
        print(f"📊 Elements missing frame_hash: {missing_count}/{len(elements)}")
        
        if missing_count > 0:
            print("❌ Frame_hash issue confirmed!")
            return False
        else:
            print("✅ All elements have frame_hash!")
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        runner._close()

if __name__ == "__main__":
    test_frame_hash_issue()