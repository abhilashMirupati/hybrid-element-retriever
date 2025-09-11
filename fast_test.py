#!/usr/bin/env python3
"""
Fast Natural Language Test Runner
- Minimal logging
- Direct element targeting
- Quick execution
"""

import time
from src.her.core.runner import Runner

def fast_google_test():
    print("🚀 Fast Google Test - Starting...")
    start_time = time.time()
    
    # Initialize runner
    runner = Runner(headless=True)
    
    try:
        # Step 1: Go to Google
        print("📍 Step 1: Navigating to Google...")
        runner.snapshot("https://www.google.com/")
        runner.wait_for_timeout(2000)
        
        # Step 2: Click search box (direct targeting)
        print("🔍 Step 2: Clicking search box...")
        runner.do_action("click", "//textarea[@name='q']", None)
        runner.wait_for_timeout(1000)
        
        # Step 3: Type search term
        print("⌨️ Step 3: Typing search term...")
        runner.do_action("type", "//textarea[@name='q']", "Python programming")
        runner.wait_for_timeout(1000)
        
        # Step 4: Press Enter
        print("⏎ Step 4: Pressing Enter...")
        runner.do_action("press", "//textarea[@name='q']", "Enter")
        runner.wait_for_timeout(3000)
        
        # Check results
        current_url = runner.get_current_url()
        print(f"🌐 Final URL: {current_url}")
        
        if "search" in current_url and "Python" in current_url:
            print("✅ SUCCESS: Search completed!")
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
    success = fast_google_test()
    exit(0 if success else 1)