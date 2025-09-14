#!/usr/bin/env python3
"""
Debug Verizon Test - Debug each step with multiple approaches
"""

import json
import os
import sys
import time
import traceback
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from her.core.runner import Runner
from her.core.pipeline import HybridPipeline


def debug_step_detailed(runner, step, step_num):
    """Debug a single step with detailed analysis."""
    print(f"\n{'='*80}")
    print(f"🔍 DEBUGGING STEP {step_num}: {step}")
    print(f"{'='*80}")
    
    # Step 1: Try basic execution
    print(f"\n1️⃣ BASIC EXECUTION ATTEMPT:")
    try:
        result = runner.run_step(step)
        print(f"   Result: {result}")
        if result.get('success', False):
            print(f"   ✅ SUCCESS with basic execution!")
            return result
        else:
            print(f"   ❌ FAILED: {result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"   ❌ EXCEPTION: {str(e)}")
        traceback.print_exc()
    
    # Step 2: Analyze the step components
    print(f"\n2️⃣ STEP ANALYSIS:")
    try:
        parsed = runner.intent.parse(step)
        print(f"   Parsed Action: {parsed.action}")
        print(f"   Parsed Target: {parsed.target}")
        print(f"   Parsed Intent: {parsed}")
    except Exception as e:
        print(f"   ❌ Parsing failed: {str(e)}")
        traceback.print_exc()
    
    # Step 3: Take snapshot and analyze elements
    print(f"\n3️⃣ SNAPSHOT ANALYSIS:")
    try:
        snapshot = runner.snapshot()
        elements = snapshot.get("elements", [])
        print(f"   Total elements found: {len(elements)}")
        
        # Look for elements with target text
        if "click" in step.lower():
            target = step.split("on")[-1].strip().strip('"').strip("'")
            print(f"   Looking for target: '{target}'")
            
            # Find elements containing target text
            matching_elements = []
            for i, elem in enumerate(elements[:100]):  # Check first 100 elements
                text = elem.get('text', '').lower()
                if target.lower() in text or text in target.lower():
                    matching_elements.append({
                        'index': i,
                        'text': elem.get('text', ''),
                        'tag': elem.get('tag', ''),
                        'attributes': elem.get('attributes', {}),
                        'element': elem
                    })
            
            print(f"   Elements matching '{target}': {len(matching_elements)}")
            for match in matching_elements[:5]:  # Show first 5 matches
                print(f"     - [{match['index']}] {match['tag']}: '{match['text']}'")
        
    except Exception as e:
        print(f"   ❌ Snapshot failed: {str(e)}")
        traceback.print_exc()
    
    # Step 4: Try manual selector resolution
    print(f"\n4️⃣ MANUAL SELECTOR RESOLUTION:")
    try:
        if "click" in step.lower():
            target = step.split("on")[-1].strip().strip('"').strip("'")
            print(f"   Attempting to resolve selector for: '{target}'")
            
            resolved = runner.resolve_selector(target, snapshot)
            print(f"   Resolved result: {resolved}")
            
            if resolved.get('selector'):
                print(f"   ✅ Found selector: {resolved['selector']}")
                print(f"   Confidence: {resolved.get('confidence', 0)}")
                print(f"   Strategy: {resolved.get('strategy', 'unknown')}")
                
                # Try to execute with this selector
                print(f"\n5️⃣ EXECUTION WITH RESOLVED SELECTOR:")
                try:
                    parsed = runner.intent.parse(step)
                    runner.do_action(parsed.action, resolved['selector'], promo=resolved.get('promo', {}))
                    print(f"   ✅ SUCCESS with resolved selector!")
                    return {"success": True, "selector": resolved['selector'], "method": "resolved_selector"}
                except Exception as e:
                    print(f"   ❌ Failed with resolved selector: {str(e)}")
                    traceback.print_exc()
            else:
                print(f"   ❌ No selector found")
                
    except Exception as e:
        print(f"   ❌ Manual resolution failed: {str(e)}")
        traceback.print_exc()
    
    # Step 5: Try alternative targets
    print(f"\n6️⃣ ALTERNATIVE TARGETS:")
    if "click" in step.lower():
        target = step.split("on")[-1].strip().strip('"').strip("'")
        alternatives = get_alternative_targets(target)
        
        for alt_target in alternatives:
            print(f"   Trying alternative: '{alt_target}'")
            alt_step = step.replace(target, alt_target)
            
            try:
                alt_result = runner.run_step(alt_step)
                if alt_result.get('success', False):
                    print(f"   ✅ SUCCESS with alternative: '{alt_target}'!")
                    return alt_result
                else:
                    print(f"   ❌ Failed with alternative: {alt_result.get('error', 'Unknown error')}")
            except Exception as e:
                print(f"   ❌ Exception with alternative: {str(e)}")
    
    # Step 6: Try different approaches based on step type
    print(f"\n7️⃣ SPECIALIZED APPROACHES:")
    step_lower = step.lower()
    
    if "navigate" in step_lower or "open" in step_lower:
        print(f"   Trying direct navigation approach...")
        try:
            url = step.split('"')[1] if '"' in step else step.split()[-1]
            snapshot = runner.snapshot(url)
            print(f"   ✅ Navigation successful to: {url}")
            return {"success": True, "url": url, "method": "direct_navigation"}
        except Exception as e:
            print(f"   ❌ Direct navigation failed: {str(e)}")
    
    elif "validate" in step_lower:
        print(f"   Trying validation approach...")
        try:
            is_valid = runner._validate(step)
            print(f"   ✅ Validation result: {is_valid}")
            return {"success": is_valid, "method": "validation"}
        except Exception as e:
            print(f"   ❌ Validation failed: {str(e)}")
    
    return {"success": False, "error": "All approaches failed"}


def get_alternative_targets(target):
    """Get alternative target texts to try."""
    alternatives = []
    
    target_lower = target.lower()
    
    if "phones" in target_lower:
        alternatives = ["Phones", "PHONES", "Smartphones", "SMARTPHONES", "Mobile", "Devices"]
    elif "apple" in target_lower:
        alternatives = ["Apple", "APPLE", "iPhone", "IPHONE", "Apple iPhone"]
    elif "iphone" in target_lower and "17" in target_lower:
        alternatives = ["iPhone 17", "IPHONE 17", "Apple iPhone 17", "iPhone17", "Apple iPhone17"]
    elif "white" in target_lower:
        alternatives = ["White", "WHITE", "white color", "White Color", "White Colour"]
    elif "color" in target_lower:
        alternatives = ["Color", "COLOR", "Colour", "COLOUR", "Colors", "COLORS"]
    
    return alternatives


def run_debug_verizon_test():
    """Run the debug Verizon test."""
    print("🔍 Starting Debug Verizon Test")
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
        start_time = time.time()
        
        # Debug this step
        result = debug_step_detailed(runner, step, i)
        execution_time = time.time() - start_time
        
        # Store result
        results.append({
            "step": i,
            "description": step,
            "success": result.get('success', False),
            "time": execution_time,
            "debug_result": result
        })
        
        # Wait between steps
        time.sleep(3)
    
    # Final summary
    print(f"\n{'='*80}")
    print("📊 FINAL DEBUG RESULTS")
    print(f"{'='*80}")
    
    successful = sum(1 for r in results if r['success'])
    total = len(results)
    
    print(f"Total Steps: {total}")
    print(f"Successful: {successful}")
    print(f"Failed: {total - successful}")
    print(f"Success Rate: {(successful/total)*100:.1f}%")
    
    print(f"\n📋 DETAILED STEP RESULTS:")
    for r in results:
        status = "✅" if r['success'] else "❌"
        print(f"  {status} Step {r['step']}: {r['description']}")
        print(f"     Time: {r['time']:.2f}s")
        print(f"     Result: {r['debug_result']}")
    
    # Save detailed results
    with open("debug_verizon_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📄 Detailed debug results saved to: debug_verizon_results.json")
    
    # Cleanup
    runner._close()
    
    return results


if __name__ == "__main__":
    run_debug_verizon_test()