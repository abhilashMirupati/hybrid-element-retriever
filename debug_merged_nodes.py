#!/usr/bin/env python3
"""
Debug script to test merged nodes structure
"""

import os
import sys
sys.path.append('/workspace/src')

from her.bridge.cdp_bridge import CDPBridge
from her.descriptors.merge import merge_dom_ax, convert_accessibility_to_element

def test_merged_nodes():
    print("🔍 TESTING MERGED NODES STRUCTURE")
    print("=" * 60)
    
    # Test with sample accessibility node
    sample_ax_node = {
        'nodeId': 4,
        'ignored': False,
        'role': {'type': 'internalRole', 'value': 'RootWebArea'},
        'name': {'type': 'computedString', 'value': 'Verizon: Wireless, Internet, TV and Phone Services | Official Site'},
        'properties': [],
        'childIds': [5, 6, 7],
        'backendDOMNodeId': 1,
        'frameId': 'main'
    }
    
    print("📊 Sample accessibility node:")
    print(f"   Keys: {list(sample_ax_node.keys())}")
    
    # Test element conversion
    element = convert_accessibility_to_element(sample_ax_node)
    if element:
        print(f"\n🔧 Converted element:")
        print(f"   Keys: {list(element.keys())}")
        print(f"   Tag: '{element.get('tag', '')}'")
        print(f"   Type: '{element.get('type', '')}'")
        print(f"   Text: '{element.get('text', '')}'")
        print(f"   Interactive: {element.get('interactive', False)}")
        print(f"   Attributes: {element.get('attributes', {})}")
    
    # Test merge with empty DOM
    print(f"\n🔧 Testing merge with empty DOM:")
    merged_nodes = merge_dom_ax([], [sample_ax_node])
    print(f"   Merged nodes count: {len(merged_nodes)}")
    
    if merged_nodes:
        first_node = merged_nodes[0]
        print(f"   First merged node keys: {list(first_node.keys())}")
        print(f"   Tag: '{first_node.get('tag', '')}'")
        print(f"   Type: '{first_node.get('type', '')}'")
        print(f"   Text: '{first_node.get('text', '')}'")
        print(f"   Interactive: {first_node.get('interactive', False)}")
        print(f"   Attributes: {first_node.get('attributes', {})}")

if __name__ == "__main__":
    test_merged_nodes()