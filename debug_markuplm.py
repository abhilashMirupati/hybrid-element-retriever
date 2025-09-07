#!/usr/bin/env python3

import os
import sys
sys.path.insert(0, 'src')

# Set up environment
os.environ['HER_MODELS_DIR'] = '/workspace/src/her/models'
os.environ['HER_CACHE_DIR'] = '/workspace/.her_cache'
os.environ['HER_E2E'] = '1'

def debug_markuplm():
    """Debug MarkupLM loading"""
    try:
        print("Testing MarkupLM import...")
        from her.embeddings.markuplm_embedder import MarkupLMEmbedder
        print("✅ MarkupLM import successful")
        
        print("Testing MarkupLM loading...")
        model_dir = "/workspace/src/her/models/markuplm-base"
        embedder = MarkupLMEmbedder(model_dir=model_dir)
        print("✅ MarkupLM loaded successfully")
        
        # Test encoding a sample element
        sample_element = {
            "tag": "a",
            "text": "iPhone 16 Pro",
            "attributes": {
                "href": "/smartphones/apple-iphone-16-pro/",
                "class": "product-link"
            }
        }
        
        print("Testing element encoding...")
        embedding = embedder.encode(sample_element)
        print(f"✅ Element encoded successfully, shape: {embedding.shape}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_markuplm()