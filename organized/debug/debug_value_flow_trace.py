#!/usr/bin/env python3
"""
Debug Value Flow Trace
Traces exactly how the 4 values flow through the system
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def test_value_flow_trace():
    """Trace the exact flow of 4 values through the system"""
    
    print("🔍 VALUE FLOW TRACE TEST")
    print("=" * 60)
    
    # Test script to trace value flow
    test_script = """
import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))
os.environ["HER_MODELS_DIR"] = str(Path.cwd() / "src" / "her" / "models")
os.environ["HER_CACHE_DIR"] = str(Path.cwd() / ".her_cache")

from her.runner import Runner

def trace_value_flow():
    try:
        # Initialize runner
        runner = Runner(headless=True)
        runner._ensure_browser()
        runner._page.goto("https://www.verizon.com/")
        
        # Test case: Enter $test123 in "password" field
        test_step = 'Enter $test123 in "password" field'
        
        print(f"\\n🔍 TRACING VALUE FLOW FOR: '{test_step}'")
        print("=" * 60)
        
        # Step 1: Parse with enhanced intent parser
        print("\\n1️⃣ INTENT PARSING:")
        intent = runner.intent.parse(test_step)
        print(f"   intent.action = '{intent.action}'")
        print(f"   intent.target_phrase = '{intent.target_phrase}'")
        print(f"   intent.args = '{intent.args}'")
        print(f"   intent.value = '{getattr(intent, 'value', None)}'")
        print(f"   intent.confidence = {intent.confidence}")
        
        # Step 2: Get snapshot and elements
        print("\\n2️⃣ SNAPSHOT CREATION:")
        snapshot = runner._snapshot()
        elements = snapshot.get('elements', [])
        print(f"   Elements count: {len(elements)}")
        print(f"   First element: {elements[0] if elements else 'None'}")
        
        # Step 3: Resolve selector (this calls pipeline.query)
        print("\\n3️⃣ SELECTOR RESOLUTION:")
        print("   Calling _resolve_selector()...")
        
        # Capture the pipeline.query call parameters
        original_query = runner.pipeline.query
        def traced_query(*args, **kwargs):
            print(f"   📤 PIPELINE.QUERY CALLED WITH:")
            print(f"      phrase (query): '{args[0]}'")
            print(f"      elements count: {len(args[1])}")
            print(f"      user_intent: '{kwargs.get('user_intent')}'")
            print(f"      target: '{kwargs.get('target')}'")
            print(f"      top_k: {kwargs.get('top_k')}")
            print(f"      page_sig: '{kwargs.get('page_sig')}'")
            print(f"      frame_hash: '{kwargs.get('frame_hash')}'")
            print(f"      label_key: '{kwargs.get('label_key')}'")
            
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
        
        print(f"   📥 _resolve_selector RETURNED:")
        print(f"      selector: '{resolved.get('selector', '')[:50]}...'")
        print(f"      confidence: {resolved.get('confidence', 0)}")
        print(f"      candidates count: {len(resolved.get('candidates', []))}")
        
        # Step 4: Action execution preparation
        print("\\n4️⃣ ACTION EXECUTION PREPARATION:")
        selector = resolved.get("selector", "")
        value = getattr(intent, 'value', None) or intent.args
        print(f"   selector: '{selector[:50]}...'")
        print(f"   value for sendKeys: '{value}'")
        print(f"   action: '{intent.action}'")
        
        # Step 5: What would happen in _do_action
        print("\\n5️⃣ WHAT WOULD HAPPEN IN _do_action:")
        if intent.action == "type" and value:
            print(f"   ✅ Would call: element.fill('{value}')")
            print(f"   ✅ This is equivalent to sendKeys('{value}')")
        else:
            print(f"   ❌ Action '{intent.action}' doesn't use sendKeys")
        
        # Step 6: Summary of 4 values
        print("\\n6️⃣ SUMMARY OF 4 VALUES:")
        print("   📤 TO MINILM (for element matching):")
        print(f"      query: '{test_step}' (full user step)")
        print(f"      user_intent: '{intent.action}' (action only)")
        print(f"      target: '{intent.target_phrase}' (target only)")
        print("   📤 TO SENDKEYS (for input):")
        print(f"      value: '{value}' (extracted value)")
        
        print("\\n✅ VALUE FLOW TRACE COMPLETED")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    trace_value_flow()
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
    test_value_flow_trace()