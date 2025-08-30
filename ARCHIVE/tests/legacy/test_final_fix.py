#!/usr/bin/env python3
"""Test with direct calculation to verify logic."""
# import sys
# from pathlib import Path
# Clear all her modules
for key in list(sys.modules.keys()):
    if 'her' in key:
        del sys.modules[key]
# removed sys.path hack
from her.pipeline import HERPipeline

# Create pipeline
pipeline = HERPipeline()

# Descriptors
laptop = {
    "tag": "button",
    "text": "Add to Cart",
    "dataTestId": "add-cart-laptop",
    "attributes": {"data-product": "laptop"}
}

phone = {
    "tag": "button",
    "text": "Add to Cart",
    "dataTestId": "add-cart-phone",
    "attributes": {"data-product": "phone"}
}

query = "add phone to cart"

# Calculate scores directly
print("DIRECT CALCULATION:")
laptop_score = pipeline._calculate_match_score(
    query.lower(),
    query.lower().split(),
    laptop,
    {"action": "add"}
)
phone_score = pipeline._calculate_match_score(
    query.lower(),
    query.lower().split(),
    phone,
    {"action": "add"}
)

print(f"  Laptop: {laptop_score:.3f}")
print(f"  Phone: {phone_score:.3f}")

# Now test through semantic_match
print("\nSEMANTIC MATCH:")
candidates = pipeline._semantic_match(
    query,
    [laptop, phone],
    {"action": "add"}
)

for desc, score in candidates:
    print(f"  {desc['dataTestId']}: {score:.3f}")

# Full pipeline
print("\nFULL PIPELINE:")
result = pipeline.process(query, [laptop, phone])
if result:
    selected = result.get('element', {}).get('dataTestId', 'none')
    print(f"  Selected: {selected}")
    
    # Verify correct selection
    if selected == 'add-cart-phone':
        print("  ✅ CORRECT - Phone was selected!")
    else:
        print("  ❌ WRONG - Should have selected phone!")