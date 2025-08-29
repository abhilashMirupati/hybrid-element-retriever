#!/usr/bin/env python3
"""Test pipeline semantic matching directly."""

import sys
from pathlib import Path

# Clear cache
for key in list(sys.modules.keys()):
    if 'her' in key:
        del sys.modules[key]

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from her.pipeline import HERPipeline

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
intent = {"action": "add"}

# Call semantic_match directly
candidates = pipeline._semantic_match(query, descriptors, intent)

print(f"Query: '{query}'")
print("=" * 40)
print("\nSemantic match results:")
for desc, score in candidates:
    print(f"  {desc['dataTestId']}: {score:.3f}")

# Now test full pipeline
print("\nFull pipeline result:")
result = pipeline.process(query, descriptors)
if result:
    print(f"  Selected: {result.get('element', {}).get('dataTestId')}")
    print(f"  XPath: {result.get('xpath')}")
    print(f"  Confidence: {result.get('confidence', 0):.3f}")