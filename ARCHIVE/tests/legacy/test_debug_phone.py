#!/usr/bin/env python3
"""Debug why phone selection isn't working."""
# import sys
# from pathlib import Path
# removed sys.path hack
from her.pipeline import HERPipeline

pipeline = HERPipeline()

# Product descriptors
product_descriptors = [
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

# Test query
query = "add phone to cart"

# Process with detailed scoring
print(f"Query: '{query}'")
print("-" * 40)

# Manually test scoring
for i, desc in enumerate(product_descriptors):
    print(f"\nDescriptor {i+1}:")
    print(f"  dataTestId: {desc['dataTestId']}")
    print(f"  data-product: {desc['attributes'].get('data-product')}")
    
    # Calculate score manually
    score = pipeline._calculate_match_score(
        query.lower(),
        query.lower().split(),
        desc,
        {"action": "add"}
    )
    print(f"  Score: {score:.3f}")

# Now run full pipeline
print("\n" + "=" * 40)
print("Full pipeline result:")
result = pipeline.process(query, product_descriptors)

if result and "xpath" in result:
    print(f"  XPath: {result['xpath']}")
    print(f"  Element: {result.get('element', {}).get('dataTestId')}")
    print(f"  Confidence: {result.get('confidence', 0):.3f}")