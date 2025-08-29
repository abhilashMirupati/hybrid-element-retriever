#!/usr/bin/env python3
"""Test scoring directly without pipeline."""

# Simulate the exact scoring logic
def calculate_score(query_lower, query_words, desc, intent):
    score = 0.0
    
    # Extract element properties
    text = str(desc.get('text', '')).lower()
    tag = str(desc.get('tag', '')).lower()
    attrs = desc.get('attributes', {})
    data_product = str(attrs.get('data-product', '')).lower()
    data_testid = str(desc.get('dataTestId', '')).lower()
    
    # Button detection
    if 'add' in query_lower:
        if tag == 'button':
            score += 0.4
            button_text_lower = text.lower()
            if 'add to cart' in query_lower and 'add to cart' in button_text_lower:
                score += 0.5
    
    # Product matching
    product_words = ['laptop', 'phone', 'tablet', 'watch', 'camera', 'tv']
    for prod_word in product_words:
        if prod_word in query_lower:
            if prod_word in data_product:
                score += 0.6  # Strong boost for exact product match
            elif prod_word in data_testid:
                score += 0.5
            else:
                # Penalty for wrong product
                for other_prod in product_words:
                    if other_prod != prod_word and other_prod in data_product:
                        score -= 0.3  # Penalty for wrong product
                        break
    
    return min(score, 1.0)

# Test data
laptop_desc = {
    "tag": "button",
    "text": "Add to Cart",
    "dataTestId": "add-cart-laptop",
    "attributes": {"data-product": "laptop"}
}

phone_desc = {
    "tag": "button",
    "text": "Add to Cart",
    "dataTestId": "add-cart-phone",
    "attributes": {"data-product": "phone"}
}

query = "add phone to cart"
query_lower = query.lower()
query_words = query_lower.split()
intent = {"action": "add"}

laptop_score = calculate_score(query_lower, query_words, laptop_desc, intent)
phone_score = calculate_score(query_lower, query_words, phone_desc, intent)

print(f"Query: '{query}'")
print(f"Laptop score: {laptop_score:.3f}")
print(f"Phone score: {phone_score:.3f}")
print(f"Winner: {'PHONE' if phone_score > laptop_score else 'LAPTOP'}")