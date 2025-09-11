#!/usr/bin/env python3
"""
Fast AI-Powered Test Runner
- Uses HER framework with semantic understanding
- Optimized for speed
- Minimal logging
"""

import time
import logging
from src.her.core.runner import Runner

# Disable verbose logging for speed
logging.getLogger("her").setLevel(logging.WARNING)
logging.getLogger("transformers").setLevel(logging.WARNING)

def fast_ai_google_test():
    print("🧠 Fast AI-Powered Google Test - Starting...")
    start_time = time.time()
    
    # Initialize runner with minimal logging
    runner = Runner(headless=True)
    
    try:
        # Step 1: Go to Google
        print("📍 Step 1: Navigating to Google...")
        runner.snapshot("https://www.google.com/")
        runner.wait_for_timeout(1000)
        
        # Step 2: Use AI to find search box semantically
        print("🔍 Step 2: AI finding search box...")
        snapshot = runner.snapshot()
        result = runner.resolve_selector("search box", snapshot)
        
        if result['confidence'] < 0.5:
            print(f"   ❌ Low confidence: {result['confidence']:.3f}")
            return False
        
        print(f"   ✅ Found with confidence: {result['confidence']:.3f}")
        
        # Step 3: Click search box
        print("🖱️ Step 3: Clicking search box...")
        runner.do_action("click", result['selector'], None)
        runner.wait_for_timeout(500)
        
        # Step 4: Type search term
        print("⌨️ Step 4: Typing search term...")
        runner.do_action("type", result['selector'], "Python programming")
        runner.wait_for_timeout(500)
        
        # Step 5: Press Enter
        print("⏎ Step 5: Pressing Enter...")
        runner.do_action("press", result['selector'], "Enter")
        runner.wait_for_timeout(2000)
        
        # Check results
        current_url = runner.get_current_url()
        print(f"🌐 Final URL: {current_url}")
        
        if "search" in current_url and "Python" in current_url:
            print("✅ SUCCESS: AI-powered search completed!")
            return True
        else:
            print("❌ FAILED: Search didn't work properly")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False
    finally:
        if hasattr(runner, '_browser') and runner._browser:
            runner._browser.close()
        elapsed = time.time() - start_time
        print(f"⏱️ Total time: {elapsed:.2f} seconds")

if __name__ == "__main__":
    success = fast_ai_google_test()
    exit(0 if success else 1)