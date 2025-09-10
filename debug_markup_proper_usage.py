#!/usr/bin/env python3
"""
Debug proper MarkupLM usage - test with actual HTML structure vs plain text.
"""

import os
import sys
import time
sys.path.insert(0, 'src')

# Disable heuristics to see pure MarkupLM scoring
os.environ["HER_DISABLE_HEURISTICS"] = "true"

from her.runner import Runner
from her.pipeline import HybridPipeline
from her.config import get_config

def debug_markup_proper_usage():
    """Debug MarkupLM with proper HTML structure vs plain text."""
    print("🔍 Debugging MarkupLM Proper Usage")
    print("=" * 60)
    
    config = get_config()
    print(f"Config: {config}")
    
    runner = Runner()
    
    try:
        snapshot = runner._snapshot("https://www.verizon.com/")
        elements = snapshot.get("elements", [])
        
        # Find the "Phones" button element
        phones_elements = []
        for elem in elements:
            text = elem.get('text', '').lower()
            if 'phones' in text and elem.get('tag') in ['A', 'BUTTON']:
                phones_elements.append(elem)
        
        print(f"Found {len(phones_elements)} 'phones' button elements:")
        for i, elem in enumerate(phones_elements[:3]):  # Show first 3
            print(f"  {i+1}. Text: '{elem.get('text', '')}'")
            print(f"     Tag: {elem.get('tag', '')}")
            print(f"     XPath: {elem.get('xpath', '')[:80]}...")
            print(f"     Attributes: {elem.get('attributes', {})}")
        
        if not phones_elements:
            print("❌ No 'phones' button elements found")
            return
        
        # Test with proper HTML structure
        test_element = phones_elements[0]
        print(f"\n🧪 Testing MarkupLM with Element: '{test_element.get('text', '')}'")
        
        # Create pipeline instance
        pipeline = HybridPipeline()
        
        # Test 1: Current approach (plain text)
        print(f"\n1️⃣ Current Approach (Plain Text):")
        current_text = test_element.get('text', '')
        print(f"   Text: '{current_text}'")
        
        # Create dummy element for current approach
        dummy_element_current = {
            "text": current_text, 
            "tag": "query", 
            "attributes": {}
        }
        
        # Test 2: Proper HTML structure approach
        print(f"\n2️⃣ Proper HTML Structure Approach:")
        print(f"   Tag: {test_element.get('tag', '')}")
        print(f"   Attributes: {test_element.get('attributes', {})}")
        print(f"   Text: '{test_element.get('text', '')}'")
        
        # Test both approaches
        query = "Click on the Phones button"
        
        print(f"\n🔍 Testing with Query: '{query}'")
        
        # Current approach
        dummy_element_current = {"text": query, "tag": "query", "attributes": {}}
        current_query_embedding = pipeline.element_embedder.encode(dummy_element_current)
        
        # Proper approach - create HTML-like structure
        proper_element = {
            "text": test_element.get('text', ''),
            "tag": test_element.get('tag', ''),
            "attributes": test_element.get('attributes', {}),
            "role": test_element.get('role', ''),
            "xpath": test_element.get('xpath', '')
        }
        
        proper_query_element = {
            "text": query,
            "tag": "button",  # User wants to click a button
            "attributes": {"type": "button"},
            "role": "button"
        }
        
        proper_element_embedding = pipeline.element_embedder.encode(proper_element)
        proper_query_embedding = pipeline.element_embedder.encode(proper_query_element)
        
        # Calculate similarities
        import numpy as np
        
        # Current approach similarity
        current_sim = np.dot(current_query_embedding, proper_element_embedding) / (
            np.linalg.norm(current_query_embedding) * np.linalg.norm(proper_element_embedding)
        )
        
        # Proper approach similarity  
        proper_sim = np.dot(proper_query_embedding, proper_element_embedding) / (
            np.linalg.norm(proper_query_embedding) * np.linalg.norm(proper_element_embedding)
        )
        
        print(f"\n📊 Results:")
        print(f"   Current Approach Similarity: {current_sim:.4f}")
        print(f"   Proper HTML Structure Similarity: {proper_sim:.4f}")
        print(f"   Improvement: {((proper_sim - current_sim) / current_sim * 100):+.1f}%")
        
        # Test with multiple elements
        print(f"\n🧪 Testing Multiple Elements with Proper Structure:")
        
        test_elements = phones_elements[:5]
        proper_query_embedding = pipeline.element_embedder.encode(proper_query_element)
        
        similarities = []
        for elem in test_elements:
            proper_elem = {
                "text": elem.get('text', ''),
                "tag": elem.get('tag', ''),
                "attributes": elem.get('attributes', {}),
                "role": elem.get('role', ''),
                "xpath": elem.get('xpath', '')
            }
            
            elem_embedding = pipeline.element_embedder.encode(proper_elem)
            sim = np.dot(proper_query_embedding, elem_embedding) / (
                np.linalg.norm(proper_query_embedding) * np.linalg.norm(elem_embedding)
            )
            similarities.append((sim, elem))
        
        similarities.sort(key=lambda x: x[0], reverse=True)
        
        print(f"   Proper HTML Structure Similarities (sorted):")
        for i, (score, elem) in enumerate(similarities):
            print(f"     {i+1}. Score: {score:.4f} | Text: '{elem.get('text', '')[:30]}...'")
            print(f"        Tag: {elem.get('tag', '')} | XPath: {elem.get('xpath', '')[:60]}...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        Runner.cleanup_models()

if __name__ == "__main__":
    debug_markup_proper_usage()