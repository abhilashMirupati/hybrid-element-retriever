#!/usr/bin/env python3
"""
Verizon Flow Test with Clean MiniLM and MarkupLM Scores
Shows only the essential scoring information for each step
"""

import os
import sys
import time
import subprocess
from datetime import datetime

def run_verizon_clean_scores():
    """Run Verizon flow test with clean scoring display"""
    print("🚀 VERIZON FLOW TEST - CLEAN SCORING ANALYSIS")
    print("=" * 80)
    
    test_script = """
import os
import sys
import time
sys.path.insert(0, 'src')

# Set environment variables
os.environ['HER_CANONICAL_MODE'] = 'both'
os.environ['HER_USE_HIERARCHY'] = 'false'
os.environ['HER_USE_TWO_STAGE'] = 'false'

from her.runner import Runner

def print_clean_scores(step_name, query, result):
    print("\\n" + "="*60)
    print(f"📊 {step_name}")
    print("="*60)
    print(f"Query: '{query}'")
    print(f"Selected: {result.get('selector', 'N/A')}")
    print(f"Confidence: {result.get('confidence', 0.0):.3f}")
    print(f"Strategy: {result.get('strategy', 'unknown')}")
    
    # Show top candidates with clean format
    candidates = result.get('candidates', [])
    if candidates:
        print(f"\\n🏆 TOP CANDIDATES:")
        print("-" * 60)
        for i, candidate in enumerate(candidates[:5]):  # Show top 5
            text = candidate.get('text', '')[:40]
            xpath = candidate.get('xpath', '')[:50]
            score = candidate.get('score', 0.0)
            tag = candidate.get('tag', '')
            interactive = candidate.get('interactive', False)
            
            print(f"{i+1:2d}. {score:6.3f} | {tag:8s} | {'✓' if interactive else '✗'} | '{text}...'")
            print(f"     {xpath}...")
    else:
        print("\\n❌ No candidates found")

def run_clean_verizon_flow():
    try:
        print("🔧 Initializing Runner...")
        runner = Runner()
        print("✅ Runner initialized")
        
        # Step 1: Open Verizon page
        print("\\n📱 STEP 1: Opening Verizon page...")
        snapshot = runner._snapshot('https://www.verizon.com/')
        print(f"✅ Page loaded with {len(snapshot.get('elements', []))} elements")
        
        # Step 2: Click on Phones
        print("\\n📱 STEP 2: Clicking on Phones...")
        phones_query = 'Click on the "Phones" button'
        phones_result = runner._resolve_selector(phones_query, snapshot)
        print_clean_scores("STEP 2: Phones Navigation", phones_query, phones_result)
        
        if not phones_result.get('selector'):
            print("❌ Failed to find Phones button")
            return False
            
        # Take new snapshot after clicking Phones
        print("\\n📸 Taking new snapshot after Phones click...")
        snapshot = runner._snapshot('https://www.verizon.com/')
        print(f"✅ New snapshot with {len(snapshot.get('elements', []))} elements")
        
        # Step 3: Select Apple filter
        print("\\n🍎 STEP 3: Selecting Apple filter...")
        apple_filter_query = 'Click on the "Apple" filter'
        apple_filter_result = runner._resolve_selector(apple_filter_query, snapshot)
        print_clean_scores("STEP 3: Apple Filter", apple_filter_query, apple_filter_result)
        
        if not apple_filter_result.get('selector'):
            print("❌ Failed to find Apple filter")
            return False
            
        # Take new snapshot after Apple filter
        print("\\n📸 Taking new snapshot after Apple filter...")
        snapshot = runner._snapshot('https://www.verizon.com/')
        print(f"✅ New snapshot with {len(snapshot.get('elements', []))} elements")
        
        # Step 4: Select Apple iPhone 16 Pro device
        print("\\n📱 STEP 4: Selecting Apple iPhone 16 Pro...")
        iphone_query = 'Click on the "Apple iPhone 16 Pro" device'
        iphone_result = runner._resolve_selector(iphone_query, snapshot)
        print_clean_scores("STEP 4: iPhone 16 Pro Selection", iphone_query, iphone_result)
        
        if not iphone_result.get('selector'):
            print("❌ Failed to find Apple iPhone 16 Pro")
            return False
            
        # Take new snapshot after iPhone selection
        print("\\n📸 Taking new snapshot after iPhone selection...")
        snapshot = runner._snapshot('https://www.verizon.com/')
        print(f"✅ New snapshot with {len(snapshot.get('elements', []))} elements")
        
        # Step 5: Validate it landed on product PDP page
        print("\\n✅ STEP 5: Validating PDP page...")
        pdp_validation_query = 'Validate that "iPhone 16 Pro" is displayed on the page'
        pdp_result = runner._resolve_selector(pdp_validation_query, snapshot)
        print_clean_scores("STEP 5: PDP Validation", pdp_validation_query, pdp_result)
        
        # Step 6: Select 512GB
        print("\\n💾 STEP 6: Selecting 512GB storage...")
        storage_query = 'Click on the "512GB" storage option'
        storage_result = runner._resolve_selector(storage_query, snapshot)
        print_clean_scores("STEP 6: 512GB Storage", storage_query, storage_result)
        
        print("\\n🎉 CLEAN SCORING ANALYSIS COMPLETED!")
        print("=" * 80)
        print("✅ All 6 steps analyzed with clean scoring display")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        try:
            runner.cleanup_models()
            runner._browser.close()
            runner._playwright.stop()
            print("\\n🧹 Cleanup completed")
        except:
            pass

if __name__ == "__main__":
    success = run_clean_verizon_flow()
    exit(0 if success else 1)
"""
    
    # Run the test
    print(f"🚀 Starting clean scoring test at: {datetime.now().isoformat()}")
    process = subprocess.run(['python', '-c', test_script], 
                           capture_output=True, text=True, 
                           env=os.environ.copy())
    
    print("STDOUT:")
    print(process.stdout)
    
    if process.stderr:
        print("STDERR:")
        print(process.stderr)
    
    print(f"\\n🏁 Test completed at: {datetime.now().isoformat()}")
    print(f"Exit code: {process.returncode}")
    
    return process.returncode == 0

def main():
    """Main test function"""
    print("🚀 VERIZON CLEAN SCORING TEST")
    print("=" * 80)
    
    success = run_verizon_clean_scores()
    
    print("\\n🏁 CLEAN SCORING TEST COMPLETED")
    return success

if __name__ == "__main__":
    main()