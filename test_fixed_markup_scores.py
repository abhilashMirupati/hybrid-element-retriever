#!/usr/bin/env python3
"""
Test fixed MarkupLM with proper HTML structure - show scores without heuristics.
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

def test_fixed_markup_scores():
    """Test fixed MarkupLM with proper HTML structure."""
    print("🔧 Testing Fixed MarkupLM with Proper HTML Structure")
    print("=" * 70)
    
    config = get_config()
    print(f"Config: {config}")
    print(f"Heuristics Disabled: {config.should_disable_heuristics()}")
    
    runner = Runner()
    
    try:
        # Test query
        query = "Click on the Phones button"
        print(f"\n🎯 Test Query: '{query}'")
        
        # Get page snapshot
        print(f"\n📸 Taking page snapshot...")
        snapshot = runner._snapshot("https://www.verizon.com/")
        elements = snapshot.get("elements", [])
        print(f"✅ Captured {len(elements)} elements")
        
        # Find phones-related elements
        phones_elements = []
        for elem in elements:
            text = elem.get('text', '').lower()
            if 'phone' in text and elem.get('tag') in ['A', 'BUTTON']:
                phones_elements.append(elem)
        
        print(f"\n🔍 Found {len(phones_elements)} phone-related elements:")
        for i, elem in enumerate(phones_elements[:5]):
            print(f"  {i+1}. Text: '{elem.get('text', '')}'")
            print(f"     Tag: {elem.get('tag', '')}")
            print(f"     XPath: {elem.get('xpath', '')[:60]}...")
        
        if not phones_elements:
            print("❌ No phone-related elements found")
            return
        
        # Test with pipeline
        print(f"\n🧪 Testing with Fixed MarkupLM Pipeline...")
        result = runner._resolve_selector(query, snapshot)
        
        print(f"\n📊 Results:")
        print(f"   Strategy: {result.get('strategy', 'unknown')}")
        print(f"   XPath: {result.get('xpath', 'N/A')}")
        print(f"   Text: {result.get('text', 'N/A')}")
        print(f"   Tag: {result.get('tag', 'N/A')}")
        print(f"   Score: {result.get('score', 'N/A')}")
        print(f"   Confidence: {result.get('confidence', 'N/A')}")
        
        # Test individual element scoring with fixed MarkupLM
        print(f"\n🔍 Individual Element Scoring (Fixed MarkupLM):")
        
        pipeline = HybridPipeline()
        
        # Test each phone element
        for i, elem in enumerate(phones_elements[:5]):
            print(f"\n  Element {i+1}: '{elem.get('text', '')}'")
            
            # Create proper HTML structure for element
            tag = elem.get('tag', '').lower()
            text = elem.get('text', '')
            attrs = elem.get('attributes', {})
            
            # Build attribute string
            attr_str = ""
            for key, value in attrs.items():
                attr_str += f' {key}="{value}"'
            
            # Create HTML structure
            if tag == 'a':
                html_text = f'<a{attr_str}>{text}</a>'
            elif tag == 'button':
                html_text = f'<button{attr_str}>{text}</button>'
            else:
                html_text = f'<{tag}{attr_str}>{text}</{tag}>'
            
            # Create element for MarkupLM
            html_element = {
                "text": html_text,
                "tag": "html",
                "attributes": {}
            }
            
            # Get embeddings
            query_embedding = pipeline._embed_query_markup(query)
            element_embedding = pipeline.element_embedder.encode(html_element)
            
            # Calculate similarity
            import numpy as np
            similarity = np.dot(query_embedding, element_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(element_embedding)
            )
            
            print(f"     HTML: '{html_text}'")
            print(f"     MarkupLM Score: {similarity:.4f}")
            print(f"     XPath: {elem.get('xpath', '')[:60]}...")
        
        # Test with different query types
        print(f"\n🧪 Testing Different Query Types with Fixed MarkupLM:")
        
        query_types = [
            "Click on the Phones button",
            "Click Phones",
            "Select Phones",
            "Press Phones button",
            "Tap on Phones"
        ]
        
        for query_test in query_types:
            print(f"\n  Query: '{query_test}'")
            result = runner._resolve_selector(query_test, snapshot)
            print(f"    XPath: {result.get('xpath', 'N/A')[:60]}...")
            print(f"    Text: {result.get('text', 'N/A')}")
            print(f"    Score: {result.get('score', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        Runner.cleanup_models()

if __name__ == "__main__":
    test_fixed_markup_scores()