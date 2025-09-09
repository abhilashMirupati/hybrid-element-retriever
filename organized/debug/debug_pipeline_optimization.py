#!/usr/bin/env python3
"""
Optimize the pipeline for better performance
"""
import os
import sys
from pathlib import Path
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set environment variables
os.environ["HER_E2E"] = "1"

def test_optimized_pipeline():
    """Test optimized pipeline performance"""
    from her.runner import Runner
    
    print("🚀 Testing optimized pipeline...")
    
    runner = Runner(headless=True)
    
    try:
        # Navigate to Verizon homepage
        print("📱 Navigating to Verizon homepage...")
        start_time = time.time()
        snapshot = runner._snapshot("https://www.verizon.com/")
        nav_time = time.time() - start_time
        print(f"⏱️  Navigation time: {nav_time:.2f}s")
        
        # Test Step 2: Click on Phones btn
        print("\n🔍 Testing Step 2: Click on Phones btn")
        start_time = time.time()
        result = runner._resolve_selector("Phones btn", snapshot)
        resolve_time = time.time() - start_time
        print(f"⏱️  Resolve time: {resolve_time:.2f}s")
        
        if result.get("selector"):
            print(f"✅ Found: {result['selector']}")
            print(f"   Confidence: {result.get('confidence', 'N/A')}")
        else:
            print("❌ Not found")
        
        # Test the full flow with timing
        print("\n🔍 Testing full flow with timing...")
        steps = [
            "Open https://www.verizon.com/",
            "Click on Phones btn in top",
            "Select Apple filter", 
            "Select Apple iPhone 16 Pro",
            "Validate it landed on https://www.verizon.com/smartphones/apple-iphone-16-pro/",
            "Select Desert Titanium",
            "Select 512 GB",
            "Click Add to Cart",
            "Validate 'Added to your cart'",
        ]
        
        start_time = time.time()
        results = runner.run(steps)
        total_time = time.time() - start_time
        
        print(f"\n⏱️  Total execution time: {total_time:.2f}s")
        print(f"⏱️  Average per step: {total_time/len(steps):.2f}s")
        
        # Show results
        for i, result in enumerate(results):
            status = "✅" if result.ok else "❌"
            print(f"{i+1:2d}. {status} {result.step}")
            if not result.ok:
                print(f"    Error: {result.info}")
        
        return results
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        try:
            runner._page.close()
        except:
            pass

if __name__ == "__main__":
    print("🚀 Starting optimized pipeline test...")
    results = test_optimized_pipeline()
    print(f"\n🎯 Test complete!")