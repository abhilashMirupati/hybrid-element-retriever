#!/usr/bin/env python3
import os
import sys
import time
sys.path.insert(0, 'src')

os.environ["HER_MODELS_DIR"] = os.path.abspath("src/her/models")
os.environ["HER_CACHE_DIR"] = os.path.abspath(".her_cache")

from her.runner import Runner

runner = Runner(headless=True)

steps = [
    "Open https://www.verizon.com/",
    "Click on Phones btn in top",
    "Select Apple filter",
    "Select Apple iPhone 16 Pro",
]

print("Running steps...")
results = runner.run(steps)

for i, r in enumerate(results, 1):
    print(f"Step {i}: {'✓' if r.ok else '✗'} {r.step}")

# Check what URL we're actually on
if runner._page:
    try:
        time.sleep(3)  # Wait for any redirects
        final_url = runner._page.url
        print(f"\nActual URL we landed on: {final_url}")
        
        # Try different validation patterns
        print("\nURL checks:")
        print(f"  Contains 'iphone': {'iphone' in final_url.lower()}")
        print(f"  Contains '16': {'16' in final_url}")
        print(f"  Contains 'pro': {'pro' in final_url.lower()}")
        print(f"  Contains 'apple': {'apple' in final_url.lower()}")
        
        # Check normalized
        norm = runner._normalize_url(final_url)
        print(f"\nNormalized URL: {norm}")
        
        # What we expected
        expected = "https://www.verizon.com/smartphones/apple-iphone-16-pro/"
        exp_norm = runner._normalize_url(expected)
        print(f"Expected (normalized): {exp_norm}")
        print(f"Match: {norm == exp_norm}")
        
    except Exception as e:
        print(f"Error: {e}")

runner._close()