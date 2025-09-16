#!/usr/bin/env python3
"""
Test Verizon with both Semantic Mode ON and OFF
"""

import os
import sys
import time
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, '/workspace/src')

from her.core.runner import Runner

def test_with_mode(semantic_mode, mode_name):
    """Test with a specific semantic mode setting."""
    print(f"\n{'='*80}")
    print(f"🔍 TESTING WITH {mode_name}")
    print(f"{'='*80}")
    
    # Set environment variables
    os.environ["HER_USE_SEMANTIC_SEARCH"] = "true" if semantic_mode else "false"
    os.environ["HER_CACHE_DIR"] = str(Path(".her_cache").resolve())
    
    # Initialize runner
    runner = Runner(headless=False)
    
    # Corrected steps based on actual page elements
    steps = [
        'Navigate to Verizon page "https://www.verizon.com/"',
        'Click on "Shop" button',
        'Click on "Devices"',
        'Click on "Smartphones"',
        'Click on "Apple iPhone 17"',
        'Validate it landed on "https://www.verizon.com/smartphones/apple-iphone-17/"',
        'Validate "Apple iPhone 17" text on pdp page',
        'Click on "White" color'
    ]
    
    results = []
    
    for i, step in enumerate(steps, 1):
        start_time = time.time()
        
        print(f"\n--- STEP {i}: {step} ---")
        
        try:
            result = runner.run([step])
            execution_time = time.time() - start_time
            
            success = result[0].get('success', False) if result else False
            
            results.append({
                "step": i,
                "description": step,
                "success": success,
                "time": execution_time,
                "result": result[0] if result else {}
            })
            
            if success:
                print(f"✅ SUCCESS ({execution_time:.2f}s)")
            else:
                print(f"❌ FAILED ({execution_time:.2f}s)")
                if result:
                    print(f"   Error: {result[0].get('error', 'Unknown error')}")
                
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"❌ EXCEPTION ({execution_time:.2f}s): {str(e)}")
            results.append({
                "step": i,
                "description": step,
                "success": False,
                "time": execution_time,
                "error": str(e)
            })
        
        # Wait between steps
        time.sleep(2)
    
    # Summary for this mode
    successful = sum(1 for r in results if r['success'])
    total = len(results)
    success_rate = (successful / total) * 100 if total > 0 else 0
    
    print(f"\n📊 {mode_name} SUMMARY:")
    print(f"   Success Rate: {success_rate:.1f}% ({successful}/{total})")
    
    return results

def main():
    """Run tests with both modes."""
    print("🚀 VERIZON TEST - BOTH MODES COMPARISON")
    print("=" * 80)
    
    # Test with semantic mode OFF (no-semantic)
    no_semantic_results = test_with_mode(False, "SEMANTIC MODE OFF (No-Semantic)")
    
    print(f"\n{'='*80}")
    print("⏸️  WAITING 10 SECONDS BEFORE NEXT TEST")
    print(f"{'='*80}")
    time.sleep(10)
    
    # Test with semantic mode ON (semantic)
    semantic_results = test_with_mode(True, "SEMANTIC MODE ON (Semantic)")
    
    # Final comparison
    print(f"\n{'='*80}")
    print("📊 FINAL COMPARISON")
    print(f"{'='*80}")
    
    no_semantic_success = sum(1 for r in no_semantic_results if r['success'])
    semantic_success = sum(1 for r in semantic_results if r['success'])
    
    print(f"No-Semantic Mode: {no_semantic_success}/{len(no_semantic_results)} ({(no_semantic_success/len(no_semantic_results)*100):.1f}%)")
    print(f"Semantic Mode:    {semantic_success}/{len(semantic_results)} ({(semantic_success/len(semantic_results)*100):.1f}%)")
    
    # Save results
    comparison_results = {
        "no_semantic": no_semantic_results,
        "semantic": semantic_results,
        "summary": {
            "no_semantic_success_rate": (no_semantic_success/len(no_semantic_results)*100),
            "semantic_success_rate": (semantic_success/len(semantic_results)*100)
        }
    }
    
    with open('verizon_both_modes_results.json', 'w') as f:
        json.dump(comparison_results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: verizon_both_modes_results.json")

if __name__ == "__main__":
    main()