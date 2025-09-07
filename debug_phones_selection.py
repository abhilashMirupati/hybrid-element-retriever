#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from her.runner import Runner
from her.pipeline import HybridPipeline

def debug_phones_selection():
    runner = Runner()
    
    # Navigate to Verizon homepage
    print("🌐 Navigating to Verizon homepage...")
    snapshot = runner._snapshot("https://www.verizon.com/")
    
    # Get the pipeline
    pipeline = runner.pipeline
    
    # Test the query
    query = "Click on Phones btn in top"
    elements = snapshot.get("elements", [])
    
    print(f"\n🔍 Testing query: '{query}'")
    print(f"📊 Total elements: {len(elements)}")
    
    # Find the Phones link
    phones_links = [elem for elem in elements if elem.get('tag', '').lower() == 'a' and 'phones' in elem.get('text', '').lower()]
    print(f"🔍 Found {len(phones_links)} Phones links:")
    for i, elem in enumerate(phones_links):
        print(f"  {i+1}. Text: '{elem.get('text', '')}' | Href: {elem.get('attrs', {}).get('href', 'N/A')}")
    
    # Test the pipeline query
    print(f"\n🎯 Testing pipeline query...")
    result = pipeline.query(
        query,
        elements,
        top_k=10,
        page_sig="verizon_home",
        frame_hash="test",
        label_key="phones"
    )
    
    print(f"\n📋 Pipeline results:")
    for i, item in enumerate(result.get("results", [])[:5]):
        print(f"  {i+1}. Score: {item.get('score', 0):.3f} | Tag: {item.get('meta', {}).get('tag', '')} | Text: '{item.get('meta', {}).get('text', '')[:50]}...'")
        print(f"      XPath: {item.get('selector', '')}")
    
    runner._close()

if __name__ == "__main__":
    debug_phones_selection()