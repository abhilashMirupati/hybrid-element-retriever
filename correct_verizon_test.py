#!/usr/bin/env python3
"""
Corrected Verizon Test - Using actual elements available on the page
"""

import os
import sys
import time
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, '/workspace/src')

# Set environment variables
os.environ["HER_USE_SEMANTIC_SEARCH"] = "false"  # Test no-semantic mode first
os.environ["HER_CACHE_DIR"] = str(Path(".her_cache").resolve())

from her.core.runner import Runner

def run_corrected_verizon_test():
    """Run the corrected Verizon test with actual available elements."""
    print("🔍 Starting Corrected Verizon Test")
    print("=" * 80)
    
    # Initialize runner
    runner = Runner(headless=False)
    
    # Corrected steps based on actual page elements
    steps = [
        'Navigate to Verizon page "https://www.verizon.com/"',
        'Click on "Shop" button',  # Changed from "Phones" to "Shop"
        'Click on "Devices"',      # Changed from "Apple" filter to "Devices"
        'Click on "Smartphones"',  # Navigate to smartphones section
        'Click on "Apple iPhone 17"',  # Select the iPhone
        'Validate it landed on "https://www.verizon.com/smartphones/apple-iphone-17/"',
        'Validate "Apple iPhone 17" text on pdp page',
        'Click on "White" color'
    ]
    
    results = []
    
    for i, step in enumerate(steps, 1):
        start_time = time.time()
        
        print(f"\n{'='*60}")
        print(f"🔍 STEP {i}: {step}")
        print(f"{'='*60}")
        
        try:
            # Use the correct Runner API
            result = runner.run([step])
            execution_time = time.time() - start_time
            
            # Store result
            results.append({
                "step": i,
                "description": step,
                "success": result[0].get('success', False) if result else False,
                "time": execution_time,
                "result": result[0] if result else {}
            })
            
            print(f"✅ Step {i} completed in {execution_time:.2f}s")
            if result and result[0].get('success'):
                print(f"   Result: {result[0]}")
            else:
                print(f"   ❌ Failed: {result[0] if result else 'No result'}")
                
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"❌ Step {i} failed with exception: {str(e)}")
            results.append({
                "step": i,
                "description": step,
                "success": False,
                "time": execution_time,
                "error": str(e)
            })
        
        # Wait between steps
        time.sleep(3)
    
    # Final summary
    print(f"\n{'='*80}")
    print("📊 FINAL RESULTS")
    print(f"{'='*80}")
    
    successful = sum(1 for r in results if r['success'])
    total = len(results)
    success_rate = (successful / total) * 100 if total > 0 else 0
    
    print(f"Total Steps: {total}")
    print(f"Successful: {successful}")
    print(f"Failed: {total - successful}")
    print(f"Success Rate: {success_rate:.1f}%")
    
    print(f"\n📋 DETAILED STEP RESULTS:")
    for result in results:
        status = "✅" if result['success'] else "❌"
        print(f"  {status} Step {result['step']}: {result['description']}")
        print(f"     Time: {result['time']:.2f}s")
        if not result['success'] and 'error' in result:
            print(f"     Error: {result['error']}")
    
    # Save results
    with open('corrected_verizon_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: corrected_verizon_results.json")
    
    return results

if __name__ == "__main__":
    run_corrected_verizon_test()