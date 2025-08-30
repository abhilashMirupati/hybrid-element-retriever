#!/usr/bin/env python3
"""Test phone selection with fresh import."""
# import sys
# from pathlib import Path
# Clear any cached modules
if 'her' in sys.modules:
    del sys.modules['her']
if 'her.pipeline' in sys.modules:
    del sys.modules['her.pipeline']
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

# Test queries
test_cases = [
    ("add laptop to cart", "add-cart-laptop"),
    ("add phone to cart", "add-cart-phone"),
]

print("PRODUCT-SPECIFIC SELECTION TEST")
print("=" * 40)

for query, expected_id in test_cases:
    result = pipeline.process(query, product_descriptors)
    
    if result and "xpath" in result:
        xpath = result['xpath']
        element = result.get('element', {})
        actual_id = element.get('dataTestId', '')
        correct = expected_id in xpath or expected_id == actual_id
        
        print(f"\nQuery: '{query}'")
        print(f"  Expected: {expected_id}")
        print(f"  Got: {actual_id}")
        print(f"  XPath: {xpath}")
        print(f"  Result: {'✓ CORRECT' if correct else '✗ WRONG'}")
        
        # Debug scores
        print(f"  Debug scores:")
        for desc in product_descriptors:
            score = pipeline._calculate_match_score(
                query.lower(),
                query.lower().split(),
                desc,
                {"action": "add"}
            )
            print(f"    {desc['dataTestId']}: {score:.3f}")
    else:
        print(f"\nQuery: '{query}'")
        print(f"  ✗ Failed to generate XPath")