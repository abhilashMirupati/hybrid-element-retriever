#!/usr/bin/env python3
"""
Debug CDP Accessibility Tree Extraction
Test the CDP accessibility tree extraction directly
"""

import os
from her.runner import Runner
from her.bridge.cdp_bridge import get_full_ax_tree, capture_complete_snapshot

def debug_cdp_accessibility():
    """Debug CDP accessibility tree extraction directly"""
    
    print("🔍 DEBUGGING CDP ACCESSIBILITY TREE EXTRACTION")
    print("=" * 60)
    
    # Set environment variable for accessibility-only mode
    os.environ['HER_CANONICAL_MODE'] = 'accessibility_only'
    
    print("🔧 Testing CDP accessibility extraction on Verizon.com")
    
    # Initialize runner
    runner = Runner(headless=True)
    
    # Initialize browser and get page
    page = runner._ensure_browser()
    if not page:
        print("❌ No page available in runner")
        return
    
    # Navigate to page
    page.goto('https://www.verizon.com/')
    
    print("📄 Page loaded, testing accessibility tree extraction...")
    
    # Test direct accessibility tree extraction
    print("\n1. Testing direct get_full_ax_tree...")
    try:
        ax_nodes = get_full_ax_tree(page, include_frames=True)
        print(f"✅ Direct extraction: {len(ax_nodes)} accessibility nodes")
        
        if ax_nodes:
            print(f"📊 First node structure:")
            print(f"   Keys: {list(ax_nodes[0].keys())}")
            print(f"   Role: {ax_nodes[0].get('role')}")
            print(f"   Name: {ax_nodes[0].get('name')}")
            print(f"   NodeId: {ax_nodes[0].get('nodeId')}")
    except Exception as e:
        print(f"❌ Direct extraction failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test complete snapshot capture
    print("\n2. Testing capture_complete_snapshot...")
    try:
        snapshot = capture_complete_snapshot(page, include_frames=True)
        print(f"✅ Snapshot capture: {len(snapshot.dom_nodes)} DOM nodes, {len(snapshot.ax_nodes)} AX nodes")
        
        if snapshot.ax_nodes:
            print(f"📊 First AX node from snapshot:")
            print(f"   Keys: {list(snapshot.ax_nodes[0].keys())}")
            print(f"   Role: {snapshot.ax_nodes[0].get('role')}")
            print(f"   Name: {snapshot.ax_nodes[0].get('name')}")
            print(f"   NodeId: {snapshot.ax_nodes[0].get('nodeId')}")
        else:
            print("❌ No accessibility nodes in snapshot")
    except Exception as e:
        print(f"❌ Snapshot capture failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test the runner's _snapshot method
    print("\n3. Testing runner._snapshot...")
    try:
        snapshot = runner._snapshot('https://www.verizon.com/')
        print(f"✅ Runner snapshot: {type(snapshot)}")
        
        if isinstance(snapshot, dict):
            print(f"   Keys: {list(snapshot.keys())}")
            if 'elements' in snapshot:
                print(f"   Elements: {len(snapshot['elements'])}")
            if 'ax_nodes' in snapshot:
                print(f"   AX nodes: {len(snapshot['ax_nodes'])}")
            else:
                print("   ❌ No ax_nodes key in snapshot")
        else:
            print(f"   ❌ Snapshot is not a dict: {type(snapshot)}")
    except Exception as e:
        print(f"❌ Runner snapshot failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_cdp_accessibility()