#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, 'src')

os.environ["HER_MODELS_DIR"] = os.path.abspath("src/her/models")
os.environ["HER_CACHE_DIR"] = os.path.abspath(".her_cache")
os.environ["HER_DEBUG_CANDIDATES"] = "1"

from her.runner import Runner

runner = Runner(headless=False)  # Run with GUI to see what's happening

steps = [
    "Open https://www.verizon.com/",
    "Click on Phones btn in top",
    "Select Apple filter",
    "Select Apple iPhone 16 Pro",  # Changed to a real product
    "Validate it landed on https://www.verizon.com/smartphones/apple-iphone-16-pro/",
]

print("Running test with visible browser...")
results = runner.run(steps)

for i, r in enumerate(results, 1):
    print(f"\nStep {i}: {r.step}")
    print(f"  Success: {r.ok}")
    if not r.ok and 'error' in r.info:
        print(f"  Error: {r.info['error']}")
    
# Check final URL
if runner._page:
    try:
        final_url = runner._page.url
        print(f"\nFinal URL: {final_url}")
        print(f"Contains 'iphone': {'iphone' in final_url.lower()}")
    except:
        pass

runner._close()