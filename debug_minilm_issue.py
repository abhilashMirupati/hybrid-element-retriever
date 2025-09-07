#!/usr/bin/env python3
"""
Debug script to investigate MiniLM similarity calculation issues
"""
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set environment variables
os.environ["HER_E2E"] = "1"

def debug_minilm_similarity():
    """Debug MiniLM similarity calculation"""
    from her.runner import Runner
    from her.embeddings.text_embedder import TextEmbedder
    import numpy as np
    
    print("🔍 Debugging MiniLM similarity calculation...")
    
    # Create runner and get page snapshot
    runner = Runner(headless=True)
    
    try:
        # Navigate to Verizon homepage
        print("📱 Navigating to Verizon homepage...")
        snapshot = runner._snapshot("https://www.verizon.com/")
        
        # Get text embedder
        text_embedder = TextEmbedder()
        
        # Test query
        query = "Phones btn"
        print(f"\n🎯 Testing query: '{query}'")
        
        # Get query embedding
        query_embedding = text_embedder.encode_one(query)
        print(f"Query embedding shape: {query_embedding.shape}")
        print(f"Query embedding (first 10 dims): {query_embedding[:10]}")
        
        # Get all elements and their texts
        print(f"\n📄 Analyzing page elements...")
        elements = snapshot.get('elements', [])
        print(f"Total elements found: {len(elements)}")
        
        # Extract texts and compute similarities
        similarities = []
        for i, element in enumerate(elements[:100]):  # Check first 100 elements
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
                        'text': text[:100],  # Truncate for display
                        'similarity': similarity,
                        'tag': element.get('tag', ''),
                        'xpath': element.get('xpath', '')[:100]
                    })
                except Exception as e:
                    print(f"Error processing element {i}: {e}")
                    continue
        
        # Sort by similarity
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        
        print(f"\n🔍 Top 20 most similar elements:")
        for i, item in enumerate(similarities[:20]):
            print(f"{i+1:2d}. Similarity: {item['similarity']:.4f} | Tag: {item['tag']:8s} | Text: '{item['text']}'")
            if i < 5:  # Show XPath for top 5
                print(f"    XPath: {item['xpath']}")
        
        # Look for specific terms
        print(f"\n🔍 Looking for specific terms:")
        phone_terms = ['phone', 'phones', 'smartphone', 'mobile', 'device']
        for term in phone_terms:
            matches = [item for item in similarities if term.lower() in item['text'].lower()]
            if matches:
                print(f"'{term}': {len(matches)} matches")
                for match in matches[:3]:
                    print(f"  - {match['similarity']:.4f}: '{match['text']}'")
            else:
                print(f"'{term}': No matches found")
        
        # Check what "My offers" actually contains
        print(f"\n🔍 Analyzing 'My offers' elements:")
        offers_matches = [item for item in similarities if 'offers' in item['text'].lower()]
        for match in offers_matches[:5]:
            print(f"  - {match['similarity']:.4f}: '{match['text']}' | Tag: {match['tag']}")
            print(f"    XPath: {match['xpath']}")
        
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

def debug_text_extraction():
    """Debug text extraction from elements"""
    from her.runner import Runner
    
    print("\n🔍 Debugging text extraction...")
    
    runner = Runner(headless=True)
    
    try:
        # Navigate to Verizon homepage
        snapshot = runner._snapshot("https://www.verizon.com/")
        
        # Get all elements
        elements = snapshot.get('elements', [])
        print(f"Total elements: {len(elements)}")
        
        # Look for navigation elements
        nav_elements = []
        for i, element in enumerate(elements):
            text = element.get('text', '').strip()
            tag = element.get('tag', '')
            xpath = element.get('xpath', '')
            
            # Look for navigation-related elements
            if any(keyword in text.lower() for keyword in ['phone', 'smartphone', 'mobile', 'device', 'offers', 'deals']):
                nav_elements.append({
                    'index': i,
                    'text': text,
                    'tag': tag,
                    'xpath': xpath,
                    'attributes': element.get('attributes', {})
                })
        
        print(f"\n📱 Navigation elements found: {len(nav_elements)}")
        for i, elem in enumerate(nav_elements[:20]):
            print(f"{i+1:2d}. Tag: {elem['tag']:8s} | Text: '{elem['text']}'")
            print(f"    XPath: {elem['xpath'][:100]}")
            if elem['attributes']:
                print(f"    Attributes: {elem['attributes']}")
            print()
        
        return nav_elements
        
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
    print("🚀 Starting MiniLM debugging...")
    
    # Debug similarity calculation
    similarities = debug_minilm_similarity()
    
    # Debug text extraction
    nav_elements = debug_text_extraction()
    
    print("\n🎯 Debugging complete!")