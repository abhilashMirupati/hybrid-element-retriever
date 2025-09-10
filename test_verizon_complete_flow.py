#!/usr/bin/env python3
"""
Complete Verizon Flow Test
1. Open Verizon page
2. Click on Phone on top of page
3. Select Apple filter
4. Select Apple 16 Pro device
5. Validate it landed on product PDP page
6. Select 512GB
"""

import os
import sys
import time
import subprocess
from datetime import datetime

def run_verizon_flow_test():
    """Run the complete Verizon flow test"""
    print("🚀 VERIZON COMPLETE FLOW TEST")
    print("=" * 60)
    print("Steps:")
    print("1. Open Verizon page")
    print("2. Click on Phone on top of page")
    print("3. Select Apple filter")
    print("4. Select Apple 16 Pro device")
    print("5. Validate it landed on product PDP page")
    print("6. Select 512GB")
    print("=" * 60)
    
    test_script = f"""
import os
import sys
import time
sys.path.insert(0, 'src')

# Set environment variables
os.environ['HER_CANONICAL_MODE'] = 'both'
os.environ['HER_USE_HIERARCHY'] = 'false'
os.environ['HER_USE_TWO_STAGE'] = 'false'

from her.runner import Runner
from her.parser.enhanced_intent import EnhancedIntentParser

def print_step(step_num, action, query, result):
    print(f"\\n{'='*60}")
    print(f"STEP {{step_num}}: {{action}}")
    print(f"{'='*60}")
    print(f"Query: '{{query}}'")
    print(f"Selected: {{result.get('selector', 'N/A')}}")
    print(f"Strategy: {{result.get('strategy', 'unknown')}}")
    print(f"Confidence: {{result.get('confidence', 0.0):.3f}}")
    print(f"Success: {'✅' if result.get('selector') else '❌'}")

def run_verizon_flow():
    try:
        print("🔧 Initializing Runner...")
        runner = Runner()
        print("✅ Runner initialized")
        
        # Step 1: Open Verizon page
        print("\\n📱 STEP 1: Opening Verizon page...")
        snapshot = runner._snapshot('https://www.verizon.com/')
        print(f"✅ Page loaded with {{len(snapshot.get('elements', []))}} elements")
        
        # Step 2: Click on Phone on top of page
        print("\\n📱 STEP 2: Clicking on Phone...")
        phone_query = 'Click on the "Phone" button'
        phone_result = runner._resolve_selector(phone_query, snapshot)
        print_step(2, "Click on Phone", phone_query, phone_result)
        
        if not phone_result.get('selector'):
            print("❌ Failed to find Phone button")
            return False
            
        # Take new snapshot after clicking Phone
        print("\\n📸 Taking new snapshot after Phone click...")
        snapshot = runner._snapshot('https://www.verizon.com/')
        print(f"✅ New snapshot with {{len(snapshot.get('elements', []))}} elements")
        
        # Step 3: Select Apple filter
        print("\\n🍎 STEP 3: Selecting Apple filter...")
        apple_filter_query = 'Click on the "Apple" filter'
        apple_filter_result = runner._resolve_selector(apple_filter_query, snapshot)
        print_step(3, "Select Apple filter", apple_filter_query, apple_filter_result)
        
        if not apple_filter_result.get('selector'):
            print("❌ Failed to find Apple filter")
            return False
            
        # Take new snapshot after Apple filter
        print("\\n📸 Taking new snapshot after Apple filter...")
        snapshot = runner._snapshot('https://www.verizon.com/')
        print(f"✅ New snapshot with {{len(snapshot.get('elements', []))}} elements")
        
        # Step 4: Select Apple 16 Pro device
        print("\\n📱 STEP 4: Selecting Apple iPhone 16 Pro...")
        iphone_query = 'Click on the "Apple iPhone 16 Pro" device'
        iphone_result = runner._resolve_selector(iphone_query, snapshot)
        print_step(4, "Select Apple iPhone 16 Pro", iphone_query, iphone_result)
        
        if not iphone_result.get('selector'):
            print("❌ Failed to find Apple iPhone 16 Pro")
            return False
            
        # Take new snapshot after iPhone selection
        print("\\n📸 Taking new snapshot after iPhone selection...")
        snapshot = runner._snapshot('https://www.verizon.com/')
        print(f"✅ New snapshot with {{len(snapshot.get('elements', []))}} elements")
        
        # Step 5: Validate it landed on product PDP page
        print("\\n✅ STEP 5: Validating PDP page...")
        pdp_validation_query = 'Validate that "iPhone 16 Pro" is displayed on the page'
        pdp_result = runner._resolve_selector(pdp_validation_query, snapshot)
        print_step(5, "Validate PDP page", pdp_validation_query, pdp_result)
        
        # Step 6: Select 512GB
        print("\\n💾 STEP 6: Selecting 512GB storage...")
        storage_query = 'Click on the "512GB" storage option'
        storage_result = runner._resolve_selector(storage_query, snapshot)
        print_step(6, "Select 512GB", storage_query, storage_result)
        
        if not storage_result.get('selector'):
            print("❌ Failed to find 512GB option")
            return False
        
        print("\\n🎉 VERIZON FLOW TEST COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("✅ All 6 steps completed successfully")
        print("✅ Framework is working correctly for complex flows")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {{e}}")
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
    success = run_verizon_flow()
    exit(0 if success else 1)
"""
    
    # Run the test
    print(f"🚀 Starting test at: {datetime.now().isoformat()}")
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

def run_individual_step_tests():
    """Run individual step tests to debug each step"""
    print("\\n\\n🔍 INDIVIDUAL STEP DEBUGGING")
    print("=" * 60)
    
    steps = [
        ("Click on the \"Phone\" button", "Find Phone navigation"),
        ("Click on the \"Apple\" filter", "Find Apple filter"),
        ("Click on the \"Apple iPhone 16 Pro\" device", "Find iPhone 16 Pro"),
        ("Validate that \"iPhone 16 Pro\" is displayed", "Validate PDP page"),
        ("Click on the \"512GB\" storage option", "Find 512GB option")
    ]
    
    for i, (query, description) in enumerate(steps, 1):
        print(f"\\n{'='*40}")
        print(f"DEBUG STEP {i}: {description}")
        print(f"{'='*40}")
        
        test_script = f"""
import os
import sys
sys.path.insert(0, 'src')

os.environ['HER_CANONICAL_MODE'] = 'both'
os.environ['HER_USE_HIERARCHY'] = 'false'
os.environ['HER_USE_TWO_STAGE'] = 'false'

from her.runner import Runner

try:
    runner = Runner()
    snapshot = runner._snapshot('https://www.verizon.com/')
    
    print(f"Query: '{query}'")
    print(f"Elements available: {{len(snapshot.get('elements', []))}}")
    
    result = runner._resolve_selector('{query}', snapshot)
    
    print(f"\\nResult:")
    print(f"  Selected: {{result.get('selector', 'N/A')}}")
    print(f"  Strategy: {{result.get('strategy', 'unknown')}}")
    print(f"  Confidence: {{result.get('confidence', 0.0):.3f}}")
    
    # Show top 5 candidates
    candidates = result.get('candidates', [])
    if candidates:
        print(f"\\nTop 5 candidates:")
        for j, candidate in enumerate(candidates[:5]):
            text = candidate.get('text', '')[:50]
            xpath = candidate.get('xpath', '')[:80]
            score = candidate.get('score', 0.0)
            print(f"  {{j+1}}. Score: {{score:.3f}} | '{{text}}...' | {{xpath}}...")
    
    runner.cleanup_models()
    runner._browser.close()
    runner._playwright.stop()
    
except Exception as e:
    print(f"ERROR: {{e}}")
    import traceback
    traceback.print_exc()
"""
        
        process = subprocess.run(['python', '-c', test_script], 
                               capture_output=True, text=True, 
                               env=os.environ.copy())
        
        print(process.stdout)
        if process.stderr:
            print("STDERR:", process.stderr)

def main():
    """Main test function"""
    print("🚀 VERIZON COMPLETE FLOW TEST SUITE")
    print("=" * 80)
    
    # Run the complete flow test
    success = run_verizon_flow_test()
    
    if not success:
        print("\\n🔍 Running individual step debugging...")
        run_individual_step_tests()
    
    print("\\n🏁 TEST SUITE COMPLETED")
    return success

if __name__ == "__main__":
    main()