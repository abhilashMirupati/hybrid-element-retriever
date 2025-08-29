#!/usr/bin/env python3
"""Debug scoring in detail."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Test the scoring logic directly
query = "add phone to cart"
query_lower = query.lower()
query_words = query_lower.split()

# Laptop descriptor
desc1 = {
    "tag": "button",
    "text": "Add to Cart",
    "dataTestId": "add-cart-laptop",
    "attributes": {"data-product": "laptop"}
}

# Phone descriptor
desc2 = {
    "tag": "button",
    "text": "Add to Cart",
    "dataTestId": "add-cart-phone",
    "attributes": {"data-product": "phone"}
}

def debug_score(desc, label):
    print(f"\n{label}:")
    score = 0.0
    
    attrs = desc.get('attributes', {})
    data_product = str(attrs.get('data-product', '')).lower()
    data_testid = str(desc.get('dataTestId', '')).lower()
    
    print(f"  data-product: {data_product}")
    print(f"  dataTestId: {data_testid}")
    
    # Check for product words
    product_words = ['laptop', 'phone', 'tablet', 'watch', 'camera', 'tv']
    for prod_word in product_words:
        if prod_word in query_lower:
            print(f"  Found '{prod_word}' in query")
            if prod_word in data_product:
                print(f"    ✓ Matches data-product: +0.6")
                score += 0.6
            elif prod_word in data_testid:
                print(f"    ✓ Matches dataTestId: +0.5")
                score += 0.5
            else:
                # Check for wrong product
                for other_prod in product_words:
                    if other_prod != prod_word and other_prod in data_product:
                        print(f"    ✗ Wrong product ({other_prod} != {prod_word}): -0.3")
                        score -= 0.3
                        break
    
    # Check button/add matching
    if 'add' in query_lower:
        if desc.get('tag') == 'button':
            print(f"  Button tag + 'add' in query: +0.4")
            score += 0.4
            if 'add to cart' in desc.get('text', '').lower():
                print(f"  'Add to Cart' text match: +0.5")
                score += 0.5
    
    print(f"  Final score: {score:.3f}")
    return score

score1 = debug_score(desc1, "LAPTOP Button")
score2 = debug_score(desc2, "PHONE Button")

print("\n" + "=" * 40)
print(f"Laptop score: {score1:.3f}")
print(f"Phone score: {score2:.3f}")
print(f"Winner: {'PHONE' if score2 > score1 else 'LAPTOP' if score1 > score2 else 'TIE'}")