#!/usr/bin/env python3
"""
Debug Accessibility Structure
Check the structure of accessibility nodes and their IDs
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def debug_accessibility_structure():
    """Debug accessibility node structure"""
    
    print("🔍 DEBUGGING ACCESSIBILITY STRUCTURE")
    print("=" * 80)
    
    test_script = """
import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))
os.environ["HER_MODELS_DIR"] = str(Path.cwd() / "src" / "her" / "models")
os.environ["HER_CACHE_DIR"] = str(Path.cwd() / ".her_cache")
os.environ["HER_CANONICAL_MODE"] = "BOTH"

from her.runner import Runner
from her.bridge.cdp_bridge import capture_complete_snapshot, get_full_ax_tree

try:
    # Initialize runner
    runner = Runner(headless=True)
    runner._ensure_browser()
    runner._page.goto("https://www.verizon.com/")
    
    # Get DOM and accessibility trees directly
    snapshot = capture_complete_snapshot(runner._page)
    dom_nodes = snapshot.dom_nodes
    ax_nodes = get_full_ax_tree(runner._page)
    
    print(f"📊 RAW DATA:")
    print(f"   DOM nodes: {len(dom_nodes)}")
    print(f"   Accessibility nodes: {len(ax_nodes)}")
    
    # Check DOM node structure
    print(f"\\n🔍 DOM NODE STRUCTURE (First 3):")
    for i, node in enumerate(dom_nodes[:3]):
        print(f"\\n   DOM Node {i+1}:")
        print(f"     Keys: {list(node.keys())}")
        print(f"     backendNodeId: {node.get('backendNodeId')}")
        print(f"     nodeId: {node.get('nodeId')}")
        print(f"     nodeType: {node.get('nodeType')}")
        print(f"     nodeName: {node.get('nodeName')}")
    
    # Check accessibility node structure
    print(f"\\n🔍 ACCESSIBILITY NODE STRUCTURE (First 3):")
    for i, node in enumerate(ax_nodes[:3]):
        print(f"\\n   AX Node {i+1}:")
        print(f"     Keys: {list(node.keys())}")
        print(f"     nodeId: {node.get('nodeId')}")
        print(f"     backendNodeId: {node.get('backendNodeId')}")
        print(f"     role: {node.get('role')}")
        print(f"     name: {node.get('name')}")
    
    # Check ID matching
    print(f"\\n🔍 ID MATCHING ANALYSIS:")
    dom_backend_ids = {node.get('backendNodeId') for node in dom_nodes if node.get('backendNodeId') is not None}
    ax_node_ids = {node.get('nodeId') for node in ax_nodes if node.get('nodeId') is not None}
    ax_backend_ids = {node.get('backendNodeId') for node in ax_nodes if node.get('backendNodeId') is not None}
    
    print(f"   DOM backendNodeIds: {len(dom_backend_ids)}")
    print(f"   AX nodeIds: {len(ax_node_ids)}")
    print(f"   AX backendNodeIds: {len(ax_backend_ids)}")
    
    # Check for matches
    matches_by_nodeid = dom_backend_ids.intersection(ax_node_ids)
    matches_by_backendid = dom_backend_ids.intersection(ax_backend_ids)
    
    print(f"   Matches by nodeId: {len(matches_by_nodeid)}")
    print(f"   Matches by backendNodeId: {len(matches_by_backendid)}")
    
    # Show some examples
    print(f"\\n🔍 ID EXAMPLES:")
    print(f"   DOM backendNodeIds (first 5): {list(dom_backend_ids)[:5]}")
    print(f"   AX nodeIds (first 5): {list(ax_node_ids)[:5]}")
    print(f"   AX backendNodeIds (first 5): {list(ax_backend_ids)[:5]}")
    
    print(f"\\n✅ ACCESSIBILITY STRUCTURE DEBUG COMPLETED")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
"""
    
    # Run test
    result = subprocess.run(
        [sys.executable, "-c", test_script],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent.parent
    )
    
    print("Output:")
    print(result.stdout)
    if result.stderr:
        print("Error:")
        print(result.stderr)

if __name__ == "__main__":
    debug_accessibility_structure()