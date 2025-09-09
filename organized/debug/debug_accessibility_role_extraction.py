#!/usr/bin/env python3
"""
Debug script to test role extraction from accessibility tree
"""

import os
import sys
sys.path.append('/workspace/src')

from her.bridge.cdp_bridge import CDPBridge
from her.descriptors.merge import convert_accessibility_to_element, extract_clean_text

def test_role_extraction():
    print("🔍 TESTING ROLE EXTRACTION FROM ACCESSIBILITY TREE")
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
    print(f"   Role: {sample_ax_node['role']}")
    print(f"   Name: {sample_ax_node['name']}")
    
    # Test role extraction
    role = sample_ax_node.get('role', '')
    print(f"\n🔧 Role extraction:")
    print(f"   Raw role: {role}")
    print(f"   Type: {type(role)}")
    
    if isinstance(role, dict):
        if 'value' in role:
            role = role['value']
        elif 'type' in role and 'value' in role:
            role = role['value']
        else:
            role = str(role)
    elif not isinstance(role, str):
        role = str(role) if role else ''
    
    print(f"   Extracted role: '{role}'")
    print(f"   Type after extraction: {type(role)}")
    
    # Test name extraction
    name = sample_ax_node.get('name', '')
    print(f"\n🔧 Name extraction:")
    print(f"   Raw name: {name}")
    print(f"   Type: {type(name)}")
    
    clean_name = extract_clean_text(name)
    print(f"   Clean name: '{clean_name}'")
    
    # Test element conversion
    print(f"\n🔧 Element conversion:")
    element = convert_accessibility_to_element(sample_ax_node)
    if element:
        print(f"   Tag: '{element.get('tag', '')}'")
        print(f"   Type: '{element.get('type', '')}'")
        print(f"   Text: '{element.get('text', '')}'")
        print(f"   Interactive: {element.get('interactive', False)}")
        print(f"   Attributes count: {len(element.get('attributes', {}))}")
    else:
        print("   ❌ Element conversion returned None")

if __name__ == "__main__":
    test_role_extraction()