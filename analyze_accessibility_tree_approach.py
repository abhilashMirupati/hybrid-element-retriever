#!/usr/bin/env python3
"""
Analyze the difference between passing entire accessibility tree vs current approach to MarkupLM.
"""

import os
import sys
import time
import json
sys.path.insert(0, 'src')

from her.runner import Runner
from her.pipeline import HybridPipeline
from her.config import get_config
from her.bridge.cdp_bridge import get_full_ax_tree

def analyze_accessibility_tree_approach():
    """Compare current approach vs entire accessibility tree approach."""
    print("🔍 Analyzing Accessibility Tree vs Current Approach for MarkupLM")
    print("=" * 80)
    
    runner = Runner()
    
    try:
        # Get page
        print(f"\n📸 Loading page...")
        page = runner._ensure_browser()
        page.goto("https://www.verizon.com/")
        time.sleep(2)
        
        # Get both approaches
        print(f"\n🌳 Getting accessibility tree...")
        ax_nodes = get_full_ax_tree(page, include_frames=True)
        print(f"✅ Captured {len(ax_nodes)} accessibility nodes")
        
        print(f"\n📄 Getting current snapshot...")
        snapshot = runner._snapshot("https://www.verizon.com/")
        elements = snapshot.get("elements", [])
        print(f"✅ Captured {len(elements)} merged elements")
        
        # Test query
        query = "Click on the Phones button"
        print(f"\n🎯 Test Query: '{query}'")
        
        # Create pipeline
        pipeline = HybridPipeline()
        
        # Approach 1: Current approach (merged elements)
        print(f"\n🔧 APPROACH 1: Current Merged Elements")
        print(f"   Elements: {len(elements)}")
        
        # Find phone-related elements in current approach
        phone_elements_current = []
        for elem in elements:
            text = elem.get('text', '').lower()
            if 'phone' in text:
                phone_elements_current.append(elem)
        
        print(f"   Phone elements found: {len(phone_elements_current)}")
        for i, elem in enumerate(phone_elements_current[:3]):
            print(f"     {i+1}. Text: '{elem.get('text', '')[:50]}...'")
            print(f"        Tag: {elem.get('tag', '')}")
            print(f"        XPath: {elem.get('xpath', '')[:60]}...")
        
        # Approach 2: Entire accessibility tree
        print(f"\n🌳 APPROACH 2: Entire Accessibility Tree")
        print(f"   Nodes: {len(ax_nodes)}")
        
        # Find phone-related nodes in accessibility tree
        phone_nodes_ax = []
        def find_phone_nodes(nodes, depth=0):
            for node in nodes:
                name = node.get('name', {}).get('value', '') if isinstance(node.get('name'), dict) else str(node.get('name', ''))
                if 'phone' in name.lower():
                    phone_nodes_ax.append((node, depth))
                children = node.get('children', [])
                if children:
                    find_phone_nodes(children, depth + 1)
        
        find_phone_nodes(ax_nodes)
        print(f"   Phone nodes found: {len(phone_nodes_ax)}")
        for i, (node, depth) in enumerate(phone_nodes_ax[:3]):
            name = node.get('name', {}).get('value', '') if isinstance(node.get('name'), dict) else str(node.get('name', ''))
            role = node.get('role', {}).get('value', '') if isinstance(node.get('role'), dict) else str(node.get('role', ''))
            print(f"     {i+1}. Name: '{name[:50]}...'")
            print(f"        Role: {role}")
            print(f"        Depth: {depth}")
        
        # Compare information richness
        print(f"\n📊 INFORMATION RICHNESS COMPARISON")
        print(f"   Current approach elements: {len(elements)}")
        print(f"   Accessibility tree nodes: {len(ax_nodes)}")
        print(f"   Ratio: {len(ax_nodes) / len(elements):.2f}x more nodes in accessibility tree")
        
        # Analyze structure differences
        print(f"\n🏗️ STRUCTURAL DIFFERENCES")
        
        # Current approach structure
        current_tags = {}
        for elem in elements:
            tag = elem.get('tag', '')
            current_tags[tag] = current_tags.get(tag, 0) + 1
        
        print(f"   Current approach tag distribution:")
        for tag, count in sorted(current_tags.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"     {tag}: {count}")
        
        # Accessibility tree structure
        ax_roles = {}
        def count_roles(nodes):
            for node in nodes:
                role = node.get('role', {}).get('value', '') if isinstance(node.get('role'), dict) else str(node.get('role', ''))
                if role:
                    ax_roles[role] = ax_roles.get(role, 0) + 1
                children = node.get('children', [])
                if children:
                    count_roles(children)
        
        count_roles(ax_nodes)
        print(f"   Accessibility tree role distribution:")
        for role, count in sorted(ax_roles.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"     {role}: {count}")
        
        # Test MarkupLM with both approaches
        print(f"\n🧪 MARKUPLM TESTING")
        
        # Test current approach
        print(f"\n   Testing Current Approach:")
        if phone_elements_current:
            # Convert to HTML for MarkupLM
            current_html = ""
            for elem in phone_elements_current[:5]:  # Test first 5
                tag = elem.get('tag', 'div').lower()
                text = elem.get('text', '')
                attrs = elem.get('attributes', {})
                attr_str = ' '.join([f'{k}="{v}"' for k, v in attrs.items()])
                current_html += f'<{tag} {attr_str}>{text}</{tag}>\n'
            
            current_element = {"text": current_html, "tag": "html", "attributes": {}}
            current_embedding = pipeline.element_embedder.encode(current_element)
            print(f"     HTML length: {len(current_html)} chars")
            print(f"     Embedding shape: {current_embedding.shape}")
        
        # Test accessibility tree approach
        print(f"\n   Testing Accessibility Tree Approach:")
        if phone_nodes_ax:
            # Convert to HTML for MarkupLM
            ax_html = ""
            for node, depth in phone_nodes_ax[:5]:  # Test first 5
                name = node.get('name', {}).get('value', '') if isinstance(node.get('name'), dict) else str(node.get('name', ''))
                role = node.get('role', {}).get('value', '') if isinstance(node.get('role'), dict) else str(node.get('role', ''))
                value = node.get('value', {}).get('value', '') if isinstance(node.get('value'), dict) else str(node.get('value', ''))
                
                # Map role to HTML tag
                role_to_tag = {
                    'button': 'button',
                    'link': 'a',
                    'text': 'span',
                    'heading': 'h1',
                    'list': 'ul',
                    'listitem': 'li',
                    'navigation': 'nav',
                    'main': 'main',
                    'banner': 'header',
                    'contentinfo': 'footer',
                    'complementary': 'aside',
                    'region': 'section',
                    'article': 'article',
                    'form': 'form',
                    'textbox': 'input',
                    'combobox': 'select',
                    'checkbox': 'input',
                    'radio': 'input',
                    'menu': 'menu',
                    'menuitem': 'li',
                    'menubar': 'nav',
                    'tab': 'button',
                    'tablist': 'div',
                    'tabpanel': 'div',
                    'dialog': 'dialog',
                    'alert': 'div',
                    'status': 'div',
                    'progressbar': 'progress',
                    'slider': 'input',
                    'separator': 'hr',
                    'img': 'img',
                    'graphic': 'img',
                    'table': 'table',
                    'row': 'tr',
                    'cell': 'td',
                    'columnheader': 'th',
                    'rowheader': 'th',
                    'grid': 'div',
                    'tree': 'div',
                    'treeitem': 'div',
                    'group': 'div',
                    'toolbar': 'div',
                    'tooltip': 'div',
                    'spinbutton': 'input',
                    'scrollbar': 'div',
                    'marquee': 'div',
                    'log': 'div',
                    'timer': 'div',
                    'application': 'div',
                    'document': 'div',
                    'presentation': 'div',
                    'none': 'div'
                }
                
                tag = role_to_tag.get(role.lower(), 'div')
                content = name or value or ''
                ax_html += f'<{tag} role="{role}">{content}</{tag}>\n'
            
            ax_element = {"text": ax_html, "tag": "html", "attributes": {}}
            ax_embedding = pipeline.element_embedder.encode(ax_element)
            print(f"     HTML length: {len(ax_html)} chars")
            print(f"     Embedding shape: {ax_embedding.shape}")
        
        # Calculate similarity with query
        print(f"\n🎯 SIMILARITY ANALYSIS")
        query_embedding = pipeline._embed_query_markup(query)
        
        if phone_elements_current and phone_nodes_ax:
            import numpy as np
            
            # Current approach similarity
            if 'current_embedding' in locals():
                current_sim = np.dot(query_embedding, current_embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(current_embedding)
                )
                print(f"   Current approach similarity: {current_sim:.4f}")
            
            # Accessibility tree similarity
            if 'ax_embedding' in locals():
                ax_sim = np.dot(query_embedding, ax_embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(ax_embedding)
                )
                print(f"   Accessibility tree similarity: {ax_sim:.4f}")
        
        # Analyze pros and cons
        print(f"\n⚖️ PROS AND CONS ANALYSIS")
        print(f"\n   CURRENT APPROACH (Merged Elements):")
        print(f"     ✅ Pros:")
        print(f"       - Already filtered and processed")
        print(f"       - Contains both DOM and accessibility info")
        print(f"       - Smaller dataset (faster processing)")
        print(f"       - XPath already generated")
        print(f"       - Interactive elements prioritized")
        print(f"     ❌ Cons:")
        print(f"       - May lose some accessibility context")
        print(f"       - Merging might lose hierarchical relationships")
        print(f"       - Limited to what was captured in snapshot")
        
        print(f"\n   ACCESSIBILITY TREE APPROACH:")
        print(f"     ✅ Pros:")
        print(f"       - Complete accessibility information")
        print(f"       - Preserves hierarchical relationships")
        print(f"       - More semantic role information")
        print(f"       - Better for complex UI understanding")
        print(f"       - Native accessibility tree structure")
        print(f"     ❌ Cons:")
        print(f"       - Much larger dataset (slower processing)")
        print(f"       - May include irrelevant nodes")
        print(f"       - No direct XPath mapping")
        print(f"       - Requires additional processing")
        print(f"       - May overwhelm MarkupLM with noise")
        
        # Recommendation
        print(f"\n💡 RECOMMENDATION")
        print(f"   For most use cases, the CURRENT APPROACH is better because:")
        print(f"   1. It's already optimized and filtered")
        print(f"   2. It provides the right balance of information")
        print(f"   3. It's faster and more efficient")
        print(f"   4. It maintains the necessary context without noise")
        print(f"   ")
        print(f"   Consider ACCESSIBILITY TREE APPROACH only if:")
        print(f"   1. You need maximum semantic understanding")
        print(f"   2. You're dealing with very complex UIs")
        print(f"   3. You have performance headroom")
        print(f"   4. You need to understand deep hierarchical relationships")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        Runner.cleanup_models()

if __name__ == "__main__":
    analyze_accessibility_tree_approach()