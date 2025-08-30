#!/usr/bin/env python3
"""Debug the full scoring flow."""
# import sys
import logging
# from pathlib import Path
# Clear cache
for key in list(sys.modules.keys()):
    if 'her' in key:
        del sys.modules[key]
# removed sys.path hack
# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

from her.pipeline import HERPipeline

# Monkey patch to add debug output
original_semantic_match = HERPipeline._semantic_match

def debug_semantic_match(self, query, descriptors, intent):
    print(f"\n=== SEMANTIC MATCH DEBUG ===")
    print(f"Query: '{query}'")
    
    # Call original
    result = original_semantic_match(self, query, descriptors, intent)
    
    print(f"\nFinal candidates:")
    for desc, score in result:
        print(f"  {desc.get('dataTestId', 'unknown')}: {score:.3f}")
    
    return result

HERPipeline._semantic_match = debug_semantic_match

pipeline = HERPipeline()

# Product descriptors
descriptors = [
    {
        "tag": "button",
        "text": "Add to Cart",
        "dataTestId": "add-cart-laptop",
        "attributes": {"data-product": "laptop"}
    },
    {
        "tag": "button",
        "text": "Add to Cart",
        "dataTestId": "add-cart-phone",
        "attributes": {"data-product": "phone"}
    }
]

query = "add phone to cart"

# Process
result = pipeline.process(query, descriptors)

print("\n=== FINAL RESULT ===")
if result:
    print(f"Selected: {result.get('element', {}).get('dataTestId')}")
    print(f"XPath: {result.get('xpath')}")