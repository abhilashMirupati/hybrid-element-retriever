#!/usr/bin/env python3
"""Test without any caching."""

import subprocess
import sys

# Run a fresh Python process
code = """
import sys
sys.path.insert(0, '/workspace/src')

from her.pipeline import HERPipeline

pipeline = HERPipeline()

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

print(f"Laptop score: {laptop_score:.3f}")
print(f"Phone score: {phone_score:.3f}")

# Full pipeline
result = pipeline.process(query, [laptop, phone])
if result:
    selected = result.get('element', {}).get('dataTestId', 'none')
    print(f"Selected: {selected}")
    
    if selected == 'add-cart-phone':
        print("✅ CORRECT - Phone was selected!")
    else:
        print("❌ WRONG - Should have selected phone!")
"""

# Run in subprocess to avoid caching
result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd="/workspace")
print(result.stdout)
if result.stderr:
    print("Errors:", result.stderr)