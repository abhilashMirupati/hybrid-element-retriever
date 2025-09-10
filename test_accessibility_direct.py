#!/usr/bin/env python3
"""
Test accessing accessibility tree directly and passing to MarkupLM in chunks.
"""

import os
import sys
import time
import json
sys.path.insert(0, 'src')

# Disable heuristics to see pure MarkupLM scoring
os.environ["HER_DISABLE_HEURISTICS"] = "true"

from her.runner import Runner
from her.pipeline import HybridPipeline
from her.config import get_config
from her.bridge.cdp_bridge import get_full_ax_tree

def create_html_from_accessibility_tree(ax_nodes, max_tokens=512):
    """
    Convert accessibility tree nodes to HTML structure, splitting into chunks if needed.
    """
    def build_html_from_node(node, depth=0):
        """Build HTML from a single accessibility node."""
        if not node:
            return ""
        
        # Get node properties
        role = node.get('role', {}).get('value', '') if isinstance(node.get('role'), dict) else str(node.get('role', ''))
        name = node.get('name', {}).get('value', '') if isinstance(node.get('name'), dict) else str(node.get('name', ''))
        value = node.get('value', {}).get('value', '') if isinstance(node.get('value'), dict) else str(node.get('value', ''))
        description = node.get('description', {}).get('value', '') if isinstance(node.get('description'), dict) else str(node.get('description', ''))
        
        # Map accessibility roles to HTML tags
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
        
        # Get HTML tag
        tag = role_to_tag.get(role.lower(), 'div')
        
        # Build attributes
        attrs = []
        if name:
            attrs.append(f'aria-label="{name}"')
        if role and role != tag:
            attrs.append(f'role="{role}"')
        if value:
            attrs.append(f'value="{value}"')
        if description:
            attrs.append(f'aria-describedby="{description}"')
        
        attr_str = ' ' + ' '.join(attrs) if attrs else ''
        
        # Get children
        children = node.get('children', [])
        
        # Build content
        content = name or value or ''
        
        # Build HTML
        if children:
            children_html = ''.join([build_html_from_node(child, depth + 1) for child in children])
            if tag in ['input', 'img', 'hr', 'br']:
                # Self-closing tags
                html = f'<{tag}{attr_str} />'
            else:
                html = f'<{tag}{attr_str}>{content}{children_html}</{tag}>'
        else:
            if tag in ['input', 'img', 'hr', 'br']:
                # Self-closing tags
                html = f'<{tag}{attr_str} />'
            else:
                html = f'<{tag}{attr_str}>{content}</{tag}>'
        
        return html
    
    # Build full HTML from all nodes
    full_html = ""
    for node in ax_nodes:
        full_html += build_html_from_node(node)
    
    # Split into chunks if too long
    chunks = []
    if len(full_html) <= max_tokens * 4:  # Rough estimate: 4 chars per token
        chunks.append(full_html)
    else:
        # Simple chunking by splitting at tag boundaries
        current_chunk = ""
        current_tokens = 0
        
        # Split by tags
        parts = full_html.split('>')
        for i, part in enumerate(parts):
            if i < len(parts) - 1:
                part += '>'
            
            part_tokens = len(part.split())  # Rough token count
            if current_tokens + part_tokens > max_tokens and current_chunk:
                chunks.append(current_chunk)
                current_chunk = part
                current_tokens = part_tokens
            else:
                current_chunk += part
                current_tokens += part_tokens
        
        if current_chunk:
            chunks.append(current_chunk)
    
    return chunks

def test_accessibility_direct():
    """Test accessing accessibility tree directly and passing to MarkupLM."""
    print("🌳 Testing Direct Accessibility Tree Access with MarkupLM")
    print("=" * 70)
    
    config = get_config()
    print(f"Config: {config}")
    print(f"Heuristics Disabled: {config.should_disable_heuristics()}")
    
    runner = Runner()
    
    try:
        # Get page
        print(f"\n📸 Loading page...")
        page = runner._get_page()
        page.goto("https://www.verizon.com/")
        time.sleep(2)  # Wait for page to load
        
        # Get accessibility tree directly
        print(f"\n🌳 Getting accessibility tree directly...")
        ax_nodes = get_full_ax_tree(page, include_frames=True)
        print(f"✅ Captured {len(ax_nodes)} accessibility nodes")
        
        if not ax_nodes:
            print("❌ No accessibility nodes found")
            return
        
        # Show sample nodes
        print(f"\n📋 Sample accessibility nodes:")
        for i, node in enumerate(ax_nodes[:5]):
            role = node.get('role', {}).get('value', '') if isinstance(node.get('role'), dict) else str(node.get('role', ''))
            name = node.get('name', {}).get('value', '') if isinstance(node.get('name'), dict) else str(node.get('name', ''))
            print(f"   {i+1}. Role: {role}, Name: {name[:50]}...")
        
        # Convert to HTML chunks
        print(f"\n🔧 Converting accessibility tree to HTML chunks...")
        html_chunks = create_html_from_accessibility_tree(ax_nodes, max_tokens=512)
        print(f"✅ Created {len(html_chunks)} HTML chunks")
        
        for i, chunk in enumerate(html_chunks):
            print(f"   Chunk {i+1}: {len(chunk)} characters")
            print(f"   Preview: {chunk[:100]}...")
        
        # Test query
        query = "Click on the Phones button"
        print(f"\n🎯 Test Query: '{query}'")
        
        # Create pipeline
        pipeline = HybridPipeline()
        
        # Test each chunk with MarkupLM
        print(f"\n🧪 Testing each chunk with MarkupLM...")
        
        best_matches = []
        
        for i, chunk in enumerate(html_chunks):
            print(f"\n  Testing Chunk {i+1}:")
            print(f"    Length: {len(chunk)} characters")
            
            # Create element for MarkupLM
            chunk_element = {
                "text": chunk,
                "tag": "html",
                "attributes": {}
            }
            
            # Get embeddings
            query_embedding = pipeline._embed_query_markup(query)
            chunk_embedding = pipeline.element_embedder.encode(chunk_element)
            
            # Calculate similarity
            import numpy as np
            similarity = np.dot(query_embedding, chunk_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(chunk_embedding)
            )
            
            print(f"    MarkupLM Score: {similarity:.4f}")
            
            # Look for "phones" in this chunk
            phones_found = []
            if 'phone' in chunk.lower():
                # Find phone-related elements in this chunk
                lines = chunk.split('\n')
                for line in lines:
                    if 'phone' in line.lower():
                        phones_found.append(line.strip()[:100])
            
            if phones_found:
                print(f"    Phone elements found: {len(phones_found)}")
                for phone in phones_found[:3]:  # Show first 3
                    print(f"      - {phone}...")
            else:
                print(f"    No phone elements found in this chunk")
            
            best_matches.append((similarity, i, chunk, phones_found))
        
        # Sort by similarity
        best_matches.sort(key=lambda x: x[0], reverse=True)
        
        print(f"\n📊 Results Summary:")
        print(f"   Best chunk: {best_matches[0][1] + 1} (score: {best_matches[0][0]:.4f})")
        print(f"   Phone elements found in {sum(1 for _, _, _, phones in best_matches if phones)} chunks")
        
        # Show best matches
        print(f"\n🏆 Top 3 Chunks by MarkupLM Score:")
        for i, (score, chunk_idx, chunk, phones) in enumerate(best_matches[:3]):
            print(f"   {i+1}. Chunk {chunk_idx + 1}: Score {score:.4f}")
            print(f"      Phone elements: {len(phones)}")
            if phones:
                print(f"      Examples: {phones[0][:80]}...")
            print(f"      Preview: {chunk[:150]}...")
        
        # Test with individual phone elements from best chunk
        if best_matches[0][3]:  # If best chunk has phone elements
            print(f"\n🔍 Testing individual phone elements from best chunk:")
            best_chunk_idx = best_matches[0][1]
            best_chunk = best_matches[0][2]
            
            # Extract individual elements (simplified)
            import re
            phone_elements = re.findall(r'<[^>]*phone[^>]*>.*?</[^>]*>', best_chunk, re.IGNORECASE)
            
            print(f"   Found {len(phone_elements)} phone elements in best chunk")
            
            for i, element in enumerate(phone_elements[:5]):  # Test first 5
                element_obj = {
                    "text": element,
                    "tag": "html",
                    "attributes": {}
                }
                
                element_embedding = pipeline.element_embedder.encode(element_obj)
                similarity = np.dot(query_embedding, element_embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(element_embedding)
                )
                
                print(f"     Element {i+1}: Score {similarity:.4f}")
                print(f"       HTML: {element[:100]}...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        Runner.cleanup_models()

if __name__ == "__main__":
    test_accessibility_direct()