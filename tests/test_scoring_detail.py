#!/usr/bin/env python3
"""Detailed scoring test."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Product descriptors
desc_laptop = {
    "tag": "button",
    "text": "Add to Cart",
    "dataTestId": "add-cart-laptop",
    "attributes": {"data-product": "laptop"}
}

desc_phone = {
    "tag": "button",
    "text": "Add to Cart",
    "dataTestId": "add-cart-phone",
    "attributes": {"data-product": "phone"}
}

query = "add phone to cart"
query_lower = query.lower()
query_words = query_lower.split()

print(f"Query: '{query}'")
print("=" * 50)

for desc in [desc_laptop, desc_phone]:
    print(f"\nElement: {desc['dataTestId']}")
    print("-" * 30)
    
    score = 0.0
    
    # Extract properties
    text = str(desc.get('text', '')).lower()
    tag = str(desc.get('tag', '')).lower()
    elem_id = str(desc.get('id', '')).lower()
    elem_type = str(desc.get('type', '')).lower()
    data_testid = str(desc.get('dataTestId', '')).lower()
    attrs = desc.get('attributes', {})
    data_product = str(attrs.get('data-product', '')).lower()
    
    print(f"  tag: {tag}")
    print(f"  text: {text}")
    print(f"  data-product: {data_product}")
    
    # Button detection
    if 'add' in query_lower:
        if tag == 'button':
            score += 0.4
            print(f"  +0.4 (button tag)")
            
            if 'add to cart' in query_lower and 'add to cart' in text:
                score += 0.5
                print(f"  +0.5 ('add to cart' match)")
    
    # Product matching
    product_words = ['laptop', 'phone', 'tablet', 'watch', 'camera', 'tv']
    for prod_word in product_words:
        if prod_word in query_lower:
            print(f"  Checking product word: '{prod_word}'")
            if prod_word in data_product:
                score += 0.6
                print(f"    +0.6 (matches data-product)")
            elif prod_word in data_testid:
                score += 0.5
                print(f"    +0.5 (matches dataTestId)")
            else:
                # Check for wrong product
                for other_prod in product_words:
                    if other_prod != prod_word and other_prod in data_product:
                        score -= 0.3
                        print(f"    -0.3 (wrong product: has '{other_prod}' not '{prod_word}')")
                        break
    
    print(f"  TOTAL SCORE: {score:.3f}")
    print(f"  CAPPED SCORE: {min(score, 1.0):.3f}")