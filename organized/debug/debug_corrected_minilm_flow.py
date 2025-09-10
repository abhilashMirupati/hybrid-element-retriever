#!/usr/bin/env python3
"""
Debug Corrected MiniLM Flow Test
Tests that MiniLM gets only target text for semantic matching
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def test_corrected_minilm_flow():
    """Test that MiniLM gets only target text for semantic matching"""
    
    print("🔍 CORRECTED MINILM FLOW TEST")
    print("=" * 60)
    
    # Test script to verify corrected flow
    test_script = """
import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))
os.environ["HER_MODELS_DIR"] = str(Path.cwd() / "src" / "her" / "models")
os.environ["HER_CACHE_DIR"] = str(Path.cwd() / ".her_cache")

from her.runner import Runner

def test_corrected_flow():
    try:
        # Initialize runner
        runner = Runner(headless=True)
        runner._ensure_browser()
        runner._page.goto("https://www.verizon.com/")
        
        # Test case: Enter $test123 in "password" field
        test_step = 'Enter $test123 in "password" field'
        
        print(f"\\n🔍 TESTING CORRECTED FLOW FOR: '{test_step}'")
        print("=" * 60)
        
        # Step 1: Parse with enhanced intent parser
        print("\\n1️⃣ INTENT PARSING:")
        intent = runner.intent.parse(test_step)
        print(f"   intent.action = '{intent.action}'")
        print(f"   intent.target_phrase = '{intent.target_phrase}'")
        print(f"   intent.value = '{getattr(intent, 'value', None)}'")
        
        # Step 2: Get snapshot
        snapshot = runner._snapshot()
        elements = snapshot.get('elements', [])
        print(f"\\n2️⃣ SNAPSHOT: {len(elements)} elements")
        
        # Step 3: Test corrected _resolve_selector
        print("\\n3️⃣ CORRECTED SELECTOR RESOLUTION:")
        
        # Capture the pipeline.query call parameters
        original_query = runner.pipeline.query
        def traced_query(*args, **kwargs):
            print(f"   📤 PIPELINE.QUERY CALLED WITH:")
            print(f"      phrase (MiniLM query): '{args[0]}'")
            print(f"      elements count: {len(args[1])}")
            print(f"      user_intent: '{kwargs.get('user_intent')}'")
            print(f"      target: '{kwargs.get('target')}'")
            
            # Verify MiniLM gets only target text
            miniLM_query = args[0]
            expected_target = intent.target_phrase
            if miniLM_query == expected_target:
                print(f"   ✅ CORRECT: MiniLM gets target only: '{miniLM_query}'")
            else:
                print(f"   ❌ WRONG: MiniLM got '{miniLM_query}', expected '{expected_target}'")
            
            # Call original method
            result = original_query(*args, **kwargs)
            
            print(f"   📥 PIPELINE.QUERY RETURNED:")
            print(f"      Results count: {len(result.get('results', []))}")
            if result.get('results'):
                first_result = result['results'][0]
                print(f"      First result selector: '{first_result.get('selector', '')[:50]}...'")
                print(f"      First result score: {first_result.get('score', 0)}")
            
            return result
        
        # Replace pipeline.query with traced version
        runner.pipeline.query = traced_query
        
        resolved = runner._resolve_selector(test_step, snapshot)
        
        print(f"\\n4️⃣ RESOLUTION RESULT:")
        print(f"   selector: '{resolved.get('selector', '')[:50]}...'")
        print(f"   confidence: {resolved.get('confidence', 0)}")
        
        # Step 4: Verify value flow
        print(f"\\n5️⃣ VALUE FLOW VERIFICATION:")
        value = getattr(intent, 'value', None) or intent.args
        print(f"   value for sendKeys: '{value}'")
        print(f"   action: '{intent.action}'")
        
        if intent.action == "type" and value:
            print(f"   ✅ Would call: element.fill('{value}')")
        else:
            print(f"   ❌ Action '{intent.action}' doesn't use sendKeys")
        
        print("\\n✅ CORRECTED FLOW TEST COMPLETED")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_corrected_flow()
"""
    
    # Run test
    result = subprocess.run(
        [sys.executable, "-c", test_script],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent.parent
    )
    
    print("Raw output:")
    print(result.stdout)
    print("Raw error:")
    print(result.stderr)

if __name__ == "__main__":
    test_corrected_minilm_flow()