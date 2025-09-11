#!/usr/bin/env python3
"""
Ultra-Fast Test Runner
- No AI processing
- Direct Playwright calls
- Minimal overhead
"""

import time
from playwright.sync_api import sync_playwright

def ultra_fast_google_test():
    print("⚡ Ultra-Fast Google Test - Starting...")
    start_time = time.time()
    
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # Step 1: Go to Google
            print("📍 Step 1: Navigating to Google...")
            page.goto("https://www.google.com/")
            page.wait_for_timeout(1000)
            
            # Step 2: Click search box
            print("🔍 Step 2: Clicking search box...")
            page.locator("textarea[name='q']").click()
            page.wait_for_timeout(500)
            
            # Step 3: Type search term
            print("⌨️ Step 3: Typing search term...")
            page.locator("textarea[name='q']").fill("Python programming")
            page.wait_for_timeout(500)
            
            # Step 4: Press Enter
            print("⏎ Step 4: Pressing Enter...")
            page.locator("textarea[name='q']").press("Enter")
            page.wait_for_timeout(2000)
            
            # Check results
            current_url = page.url
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
            browser.close()
            elapsed = time.time() - start_time
            print(f"⏱️ Total time: {elapsed:.2f} seconds")

if __name__ == "__main__":
    success = ultra_fast_google_test()
    exit(0 if success else 1)