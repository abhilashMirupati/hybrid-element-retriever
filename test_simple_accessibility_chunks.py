#!/usr/bin/env python3
"""
Simple test that uses existing runner to get accessibility tree and pass to MarkupLM in 512-token chunks.
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

def create_html_chunks_from_elements(elements, max_tokens=512):
    """
    Convert elements to HTML structure and split into 512-token chunks.
    """
    def element_to_html(element):
        """Convert a single element to HTML."""
        tag = element.get('tag', 'div').lower()
        text = element.get('text', '')
        attrs = element.get('attributes', {})
        
        # Build attribute string
        attr_str = ""
        for key, value in attrs.items():
            attr_str += f' {key}="{value}"'
        
        # Create HTML structure
        if tag in ['a', 'button', 'input', 'select', 'option']:
            if tag == 'a':
                return f'<a{attr_str}>{text}</a>'
            elif tag == 'button':
                return f'<button{attr_str}>{text}</button>'
            elif tag == 'input':
                return f'<input{attr_str} value="{text}">'
            else:
                return f'<{tag}{attr_str}>{text}</{tag}>'
        else:
            return f'<{tag}{attr_str}>{text}</{tag}>'
    
    # Convert all elements to HTML
    html_parts = []
    for element in elements:
        html_parts.append(element_to_html(element))
    
    full_html = '\n'.join(html_parts)
    
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

def test_simple_accessibility_chunks():
    """Test using existing runner to get elements and pass to MarkupLM in chunks."""
    print("🌳 Simple Accessibility Tree Test with MarkupLM Chunks")
    print("=" * 70)
    
    config = get_config()
    print(f"Config: {config}")
    print(f"Heuristics Disabled: {config.should_disable_heuristics()}")
    
    runner = Runner()
    
    try:
        # Test query
        query = "Click on the Phones button"
        print(f"\n🎯 Test Query: '{query}'")
        
        # Get page snapshot using existing runner
        print(f"\n📸 Taking page snapshot...")
        snapshot = runner._snapshot("https://www.verizon.com/")
        elements = snapshot.get("elements", [])
        print(f"✅ Captured {len(elements)} elements")
        
        # Filter for phone-related elements
        phone_elements = []
        for elem in elements:
            text = elem.get('text', '').lower()
            if 'phone' in text:
                phone_elements.append(elem)
        
        print(f"🔍 Found {len(phone_elements)} phone-related elements")
        
        # Convert to HTML chunks
        print(f"\n🔧 Converting elements to HTML chunks (512 tokens each)...")
        html_chunks = create_html_chunks_from_elements(phone_elements, max_tokens=512)
        print(f"✅ Created {len(html_chunks)} HTML chunks")
        
        for i, chunk in enumerate(html_chunks):
            print(f"   Chunk {i+1}: {len(chunk)} characters")
            print(f"   Preview: {chunk[:100]}...")
        
        # Test each chunk with MarkupLM
        print(f"\n🧪 Testing each chunk with MarkupLM...")
        
        pipeline = HybridPipeline()
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
        
        # Test with full runner query for comparison
        print(f"\n🔄 Testing with full runner query for comparison:")
        result = runner._resolve_selector(query, snapshot)
        print(f"   Runner Result XPath: {result.get('xpath', 'N/A')[:60]}...")
        print(f"   Runner Result Text: {result.get('text', 'N/A')}")
        print(f"   Runner Result Score: {result.get('score', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        Runner.cleanup_models()

if __name__ == "__main__":
    test_simple_accessibility_chunks()