#!/usr/bin/env python3
"""
Run the exact 7 Verizon steps provided by the user
"""

import os
import sys
import time
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, '/workspace/src')

from her.core.runner import Runner

def run_exact_verizon_steps(semantic_mode, mode_name):
    """Run the exact 7 steps with specified semantic mode."""
    print(f"\n{'='*80}")
    print(f"🔍 RUNNING EXACT 7 STEPS - {mode_name}")
    print(f"{'='*80}")
    
    # Set environment variables
    os.environ["HER_USE_SEMANTIC_SEARCH"] = "true" if semantic_mode else "false"
    os.environ["HER_CACHE_DIR"] = str(Path(".her_cache").resolve())
    
    # Initialize runner
    runner = Runner(headless=False)
    
    # Your exact 7 steps (fixing navigation step format)
    steps = [
        'Open https://www.verizon.com/',  # Fixed: Use "Open" format as expected by Runner
        'Click on "Phones" button',
        'Click on "Apple" filter',
        'Click on "Apple IPhone 17" device',
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
            
            success = result[0].ok if result else False
            
            results.append({
                "step": i,
                "description": step,
                "success": success,
                "time": execution_time,
                "result": result[0] if result else None
            })
            
            if success:
                print(f"✅ SUCCESS ({execution_time:.2f}s)")
                if result and result[0].selector:
                    print(f"   Selector: {result[0].selector}")
                    print(f"   Confidence: {result[0].confidence}")
            else:
                print(f"❌ FAILED ({execution_time:.2f}s)")
                if result:
                    print(f"   Info: {result[0].info}")
                
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
        time.sleep(3)
    
    # Summary for this mode
    successful = sum(1 for r in results if r['success'])
    total = len(results)
    success_rate = (successful / total) * 100 if total > 0 else 0
    
    print(f"\n📊 {mode_name} SUMMARY:")
    print(f"   Success Rate: {success_rate:.1f}% ({successful}/{total})")
    
    return results

def main():
    """Run the exact steps with both modes."""
    print("🚀 VERIZON TEST - EXACT 7 STEPS")
    print("=" * 80)
    
    # Test with semantic mode OFF (no-semantic)
    no_semantic_results = run_exact_verizon_steps(False, "SEMANTIC MODE OFF")
    
    print(f"\n{'='*80}")
    print("⏸️  WAITING 15 SECONDS BEFORE NEXT TEST")
    print(f"{'='*80}")
    time.sleep(15)
    
    # Test with semantic mode ON (semantic)
    semantic_results = run_exact_verizon_steps(True, "SEMANTIC MODE ON")
    
    # Final comparison
    print(f"\n{'='*80}")
    print("📊 FINAL COMPARISON")
    print(f"{'='*80}")
    
    no_semantic_success = sum(1 for r in no_semantic_results if r['success'])
    semantic_success = sum(1 for r in semantic_results if r['success'])
    
    print(f"No-Semantic Mode: {no_semantic_success}/{len(no_semantic_results)} ({(no_semantic_success/len(no_semantic_results)*100):.1f}%)")
    print(f"Semantic Mode:    {semantic_success}/{len(semantic_results)} ({(semantic_success/len(semantic_results)*100):.1f}%)")
    
    # Detailed step-by-step comparison
    print(f"\n📋 STEP-BY-STEP COMPARISON:")
    for i in range(len(no_semantic_results)):
        no_sem = no_semantic_results[i]
        sem = semantic_results[i]
        no_sem_status = "✅" if no_sem['success'] else "❌"
        sem_status = "✅" if sem['success'] else "❌"
        print(f"  Step {i+1}: No-Semantic: {no_sem_status} | Semantic: {sem_status}")
        if not no_sem['success'] and no_sem.get('error'):
            print(f"    No-Semantic Error: {no_sem['error']}")
        if not sem['success'] and sem.get('error'):
            print(f"    Semantic Error: {sem['error']}")
    
    # Save results
    comparison_results = {
        "no_semantic": no_semantic_results,
        "semantic": semantic_results,
        "summary": {
            "no_semantic_success_rate": (no_semantic_success/len(no_semantic_results)*100),
            "semantic_success_rate": (semantic_success/len(semantic_results)*100),
            "total_steps": len(no_semantic_results)
        }
    }
    
    with open('exact_verizon_steps_results.json', 'w') as f:
        json.dump(comparison_results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: exact_verizon_steps_results.json")
    
    return comparison_results

if __name__ == "__main__":
    main()