#!/usr/bin/env python3
"""
Simple Verizon Test - Only the 7 steps you mentioned
"""

import json
import os
import sys
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from her.core.runner import Runner


def run_simple_verizon_test():
    """Run the simple Verizon test with your 7 steps."""
    print("🚀 Starting Simple Verizon Test - Your 7 Steps Only")
    print("=" * 80)
    
    # Set environment
    os.environ["HER_USE_SEMANTIC_SEARCH"] = "true"
    os.environ["HER_CACHE_DIR"] = str(Path(".her_cache").resolve())
    
    # Initialize runner
    runner = Runner(headless=False)
    
    # Your exact 7 steps
    steps = [
        'Navigate to Verizon page "https://www.verizon.com/"',
        'Click on "Phones" button',
        'Click on "Apple" filter',
        'Click on "Apple IPhone 17" device',
        'Validate it landed on "https://www.verizon.com/smartphones/apple-iphone-17/"',
        'Validate "Apple iPhone 17" text on pdp page',
        'Click on "White" color'
    ]
    
    results = []
    
    for i, step in enumerate(steps, 1):
        print(f"\n{'='*60}")
        print(f"STEP {i}: {step}")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        try:
            # Execute step
            result = runner.run_step(step)
            execution_time = time.time() - start_time
            
            print(f"✅ Success: {result.get('success', False)}")
            print(f"⏱️  Time: {execution_time:.2f}s")
            
            if result.get('success', False):
                print(f"🎯 Canonical Description: Successfully executed step {i}")
                if 'selector' in result:
                    print(f"📍 Selector: {result['selector']}")
                if 'confidence' in result:
                    print(f"🎯 Confidence: {result['confidence']}")
            else:
                print(f"❌ Error: {result.get('error', 'Unknown error')}")
                print(f"🎯 Canonical Description: Failed to execute step {i}")
            
            results.append({
                "step": i,
                "description": step,
                "success": result.get('success', False),
                "time": execution_time,
                "result": result
            })
            
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            results.append({
                "step": i,
                "description": step,
                "success": False,
                "time": time.time() - start_time,
                "error": str(e)
            })
        
        # Wait between steps
        time.sleep(2)
    
    # Final summary
    print(f"\n{'='*80}")
    print("📊 FINAL RESULTS")
    print(f"{'='*80}")
    
    successful = sum(1 for r in results if r['success'])
    total = len(results)
    
    print(f"Total Steps: {total}")
    print(f"Successful: {successful}")
    print(f"Failed: {total - successful}")
    print(f"Success Rate: {(successful/total)*100:.1f}%")
    
    print(f"\n📋 STEP RESULTS:")
    for r in results:
        status = "✅" if r['success'] else "❌"
        print(f"  {status} Step {r['step']}: {r['description'][:50]}...")
    
    # Save results
    with open("simple_verizon_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📄 Results saved to: simple_verizon_results.json")
    
    # Cleanup
    runner._close()
    
    return results


if __name__ == "__main__":
    run_simple_verizon_test()