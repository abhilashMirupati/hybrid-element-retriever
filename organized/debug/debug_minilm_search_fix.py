#!/usr/bin/env python3
"""
Fix MiniLM search to properly find navigation elements
"""
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set environment variables
os.environ["HER_E2E"] = "1"

def test_fixed_minilm_search():
    """Test the fixed MiniLM search"""
    from her.runner import Runner
    from her.embeddings.text_embedder import TextEmbedder
    import numpy as np
    
    print("🔍 Testing fixed MiniLM search...")
    
    runner = Runner(headless=True)
    
    try:
        # Navigate to Verizon homepage
        snapshot = runner._snapshot("https://www.verizon.com/")
        
        # Get text embedder
        text_embedder = TextEmbedder()
        
        # Test query
        query = "Phones btn"
        print(f"\n🎯 Testing query: '{query}'")
        
        # Get query embedding
        query_embedding = text_embedder.encode_one(query)
        
        # Get ALL elements (not just first 100)
        elements = snapshot.get('elements', [])
        print(f"Total elements: {len(elements)}")
        
        # Extract texts and compute similarities for ALL elements
        similarities = []
        for i, element in enumerate(elements):
            text = element.get('text', '').strip()
            if text and len(text) > 0:
                try:
                    # Get element embedding
                    element_embedding = text_embedder.encode_one(text)
                    
                    # Compute cosine similarity
                    similarity = np.dot(query_embedding, element_embedding) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(element_embedding)
                    )
                    
                    similarities.append({
                        'index': i,
                        'text': text[:100],
                        'similarity': similarity,
                        'tag': element.get('tag', ''),
                        'xpath': element.get('xpath', '')[:100]
                    })
                except Exception as e:
                    continue
        
        # Sort by similarity
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        
        print(f"\n🔍 Top 20 most similar elements (ALL elements searched):")
        for i, item in enumerate(similarities[:20]):
            print(f"{i+1:2d}. Similarity: {item['similarity']:.4f} | Tag: {item['tag']:8s} | Text: '{item['text']}'")
            if i < 10:  # Show XPath for top 10
                print(f"    XPath: {item['xpath']}")
        
        # Look for navigation-specific terms
        print(f"\n🔍 Navigation elements found:")
        nav_terms = ['smartphone', 'phone', 'device', 'shop', 'mobile']
        for term in nav_terms:
            matches = [item for item in similarities if term.lower() in item['text'].lower()]
            if matches:
                print(f"\n'{term}' matches:")
                for match in matches[:5]:
                    print(f"  - {match['similarity']:.4f}: '{match['text']}' | Tag: {match['tag']}")
                    print(f"    XPath: {match['xpath']}")
        
        # Test the actual pipeline
        print(f"\n🔍 Testing actual pipeline...")
        result = runner._resolve_selector("Phones btn", snapshot)
        if result.get("selector"):
            print(f"✅ Pipeline found: {result['selector']}")
            print(f"   Confidence: {result.get('confidence', 'N/A')}")
        else:
            print("❌ Pipeline failed to find element")
        
        return similarities
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        try:
            runner._page.close()
        except:
            pass

if __name__ == "__main__":
    print("🚀 Testing fixed MiniLM search...")
    similarities = test_fixed_minilm_search()
    print(f"\n🎯 Analysis complete!")