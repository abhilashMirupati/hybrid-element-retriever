#!/usr/bin/env python3
"""Trace phone scoring."""

phone = {
    "tag": "button",
    "text": "Add to Cart",
    "dataTestId": "add-cart-phone",
    "attributes": {"data-product": "phone"}
}

query = "add phone to cart"
query_lower = query.lower()
data_testid = phone['dataTestId'].lower()
data_product = phone['attributes']['data-product'].lower()

print(f"Query: '{query}'")
print(f"Element: {phone['dataTestId']}")
print(f"data-product: {data_product}")
print(f"dataTestId (lower): {data_testid}")

score = 0.0

# Check button
if 'add' in query_lower:
    if phone['tag'] == 'button':
        score += 0.4
        print(f"  +0.4 (button)")
        if 'add to cart' in phone['text'].lower():
            score += 0.5
            print(f"  +0.5 (add to cart text)")

# Product matching
product_words = ['laptop', 'phone', 'tablet', 'watch', 'camera', 'tv']
for prod_word in product_words:
    if prod_word in query_lower:
        print(f"\nFound '{prod_word}' in query")
        
        # Check if RIGHT product
        if prod_word in data_product:
            score += 0.6
            print(f"  +0.6 (matches data-product)")
        elif prod_word in data_testid:
            score += 0.5
            print(f"  +0.5 (matches dataTestId)")
        
        # Check for WRONG product
        for other_prod in product_words:
            if other_prod != prod_word:
                if other_prod in data_product:
                    print(f"  Found wrong product '{other_prod}' in data-product")
                    score -= 0.5
                    print(f"  -0.5 (penalty)")
                if other_prod in data_testid:
                    print(f"  Found wrong product '{other_prod}' in dataTestId")
                    score -= 0.5
                    print(f"  -0.5 (penalty)")

print(f"\nFinal score: {score:.3f}")
print(f"Clamped score: {max(0.0, min(score, 1.0)):.3f}")