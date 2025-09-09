#!/usr/bin/env python3
"""
Debug script to test runner element processing
"""

import os
import sys
sys.path.append('/workspace/src')

from her.bridge.cdp_bridge import CDPBridge
from her.descriptors.merge import merge_dom_ax, convert_accessibility_to_element

def test_runner_processing():
    print("🔍 TESTING RUNNER ELEMENT PROCESSING")
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
    
    # Test merge
    merged_nodes = merge_dom_ax([], [sample_ax_node])
    print(f"📊 Merged nodes count: {len(merged_nodes)}")
    
    if merged_nodes:
        node = merged_nodes[0]
        print(f"\n🔧 Processing merged node:")
        print(f"   Node keys: {list(node.keys())}")
        print(f"   Tag: '{node.get('tag', '')}'")
        print(f"   Type: '{node.get('type', '')}'")
        print(f"   Text: '{node.get('text', '')}'")
        print(f"   Interactive: {node.get('interactive', False)}")
        print(f"   Attributes: {node.get('attributes', {})}")
        
        # Simulate runner processing
        print(f"\n🔧 Simulating runner processing:")
        
        # Extract basic information
        tag = node.get('tag', '')
        role = node.get('type', '')
        text = str(node.get('text', '')).strip()
        
        print(f"   Extracted tag: '{tag}'")
        print(f"   Extracted role: '{role}'")
        print(f"   Extracted text: '{text}'")
        
        # Extract attributes
        attrs = node.get('attributes', {})
        if isinstance(attrs, list):
            attrs_dict = {}
            for i in range(0, len(attrs), 2):
                if i + 1 < len(attrs):
                    attrs_dict[str(attrs[i])] = attrs[i + 1]
            attrs = attrs_dict
        
        print(f"   Processed attributes: {attrs}")
        print(f"   Attributes count: {len(attrs)}")
        
        # Check if element is interactive
        interactive = node.get('interactive', False)
        print(f"   Interactive: {interactive}")
        
        # Create element descriptor
        element = {
            'text': text,
            'tag': tag,
            'role': role or None,
            'attrs': attrs,
            'xpath': f"//{tag.lower()}" if tag else "//div",
            'bbox': node.get('bbox', {'x': 0, 'y': 0, 'width': 0, 'height': 0, 'w': 0, 'h': 0}),
            'visible': node.get('visible', True),
            'below_fold': node.get('below_fold', False),
            'interactive': interactive,
            'backendNodeId': node.get('backendNodeId'),
            'accessibility': node.get('accessibility', {})
        }
        
        print(f"\n🔧 Final element descriptor:")
        print(f"   Tag: '{element['tag']}'")
        print(f"   Role: '{element['role']}'")
        print(f"   Text: '{element['text']}'")
        print(f"   Interactive: {element['interactive']}")
        print(f"   Attributes count: {len(element['attrs'])}")

if __name__ == "__main__":
    test_runner_processing()