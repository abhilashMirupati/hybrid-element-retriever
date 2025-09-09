#!/usr/bin/env python3
"""
Debug Accessibility Tree Structure
Investigate the actual structure of accessibility tree data from Verizon
"""

import os
import json
from her.runner import Runner
from her.config import CanonicalMode

def debug_accessibility_structure():
    """Debug the actual structure of accessibility tree data"""
    
    print("🔍 DEBUGGING ACCESSIBILITY TREE STRUCTURE")
    print("=" * 60)
    
    # Set environment variable for accessibility-only mode
    os.environ['HER_CANONICAL_MODE'] = 'accessibility_only'
    
    print("🔧 Testing accessibility-only mode on Verizon.com")
    
    # Initialize runner
    runner = Runner(headless=True)
    
    # Get snapshot
    snapshot = runner._snapshot('https://www.verizon.com/')
    
    if isinstance(snapshot, dict) and 'ax_nodes' in snapshot:
        ax_nodes = snapshot['ax_nodes']
        print(f"📊 Found {len(ax_nodes)} accessibility nodes")
        
        # Analyze first few nodes
        print(f"\n🔍 ANALYZING FIRST 10 ACCESSIBILITY NODES:")
        print("-" * 60)
        
        for i, ax_node in enumerate(ax_nodes[:10]):
            print(f"\n--- NODE {i+1} ---")
            print(f"Type: {type(ax_node)}")
            print(f"Keys: {list(ax_node.keys()) if isinstance(ax_node, dict) else 'Not a dict'}")
            
            if isinstance(ax_node, dict):
                # Check role specifically
                role = ax_node.get('role')
                print(f"Role: {role}")
                print(f"Role type: {type(role)}")
                
                if isinstance(role, dict):
                    print(f"Role dict keys: {list(role.keys())}")
                    print(f"Role dict values: {role}")
                elif isinstance(role, list):
                    print(f"Role list: {role}")
                
                # Check other important fields
                for key in ['name', 'description', 'value', 'nodeId', 'backendNodeId']:
                    value = ax_node.get(key)
                    if value is not None:
                        print(f"{key}: {value} (type: {type(value)})")
                
                # Show full structure for first node
                if i == 0:
                    print(f"\nFULL STRUCTURE OF FIRST NODE:")
                    print(json.dumps(ax_node, indent=2, default=str))
        
        # Check for common patterns
        print(f"\n🔍 ANALYZING ROLE PATTERNS:")
        print("-" * 60)
        
        role_types = {}
        role_values = set()
        
        for ax_node in ax_nodes:
            if isinstance(ax_node, dict):
                role = ax_node.get('role')
                role_type = type(role).__name__
                role_types[role_type] = role_types.get(role_type, 0) + 1
                
                if isinstance(role, str):
                    role_values.add(role)
                elif isinstance(role, dict) and 'value' in role:
                    role_values.add(role['value'])
        
        print(f"Role types distribution:")
        for role_type, count in role_types.items():
            print(f"  {role_type}: {count}")
        
        print(f"\nUnique role values (first 20):")
        for role in sorted(list(role_values))[:20]:
            print(f"  {role}")
        
        # Check for interactive elements
        print(f"\n🔍 CHECKING FOR INTERACTIVE ELEMENTS:")
        print("-" * 60)
        
        interactive_roles = {'button', 'link', 'textbox', 'checkbox', 'radio', 'combobox', 'menu', 'menuitem'}
        found_interactive = []
        
        for ax_node in ax_nodes:
            if isinstance(ax_node, dict):
                role = ax_node.get('role')
                role_str = ''
                
                if isinstance(role, str):
                    role_str = role
                elif isinstance(role, dict) and 'value' in role:
                    role_str = role['value']
                elif isinstance(role, list) and role:
                    role_str = str(role[0])
                
                if role_str.lower() in interactive_roles:
                    found_interactive.append({
                        'role': role_str,
                        'name': ax_node.get('name', ''),
                        'nodeId': ax_node.get('nodeId', ''),
                        'full_node': ax_node
                    })
        
        print(f"Found {len(found_interactive)} interactive elements:")
        for elem in found_interactive[:10]:
            print(f"  {elem['role']}: {elem['name']} (nodeId: {elem['nodeId']})")
        
        # Save sample data for analysis
        with open('/tmp/accessibility_debug_data.json', 'w') as f:
            json.dump({
                'total_nodes': len(ax_nodes),
                'sample_nodes': ax_nodes[:5],
                'role_types': role_types,
                'role_values': list(role_values),
                'interactive_elements': found_interactive[:10]
            }, f, indent=2, default=str)
        
        print(f"\n💾 Debug data saved to /tmp/accessibility_debug_data.json")
        
    else:
        print("❌ No accessibility nodes found in snapshot")
        print(f"Snapshot keys: {list(snapshot.keys()) if isinstance(snapshot, dict) else 'Not a dict'}")

if __name__ == "__main__":
    debug_accessibility_structure()