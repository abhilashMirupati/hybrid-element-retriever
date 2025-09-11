#!/usr/bin/env python3
"""
Smart Test Runner
- Uses AI only when needed
- Direct Playwright for simple actions
- Best of both worlds
"""

import time
from playwright.sync_api import sync_playwright

def smart_google_test():
    print("🧠 Smart Google Test - Starting...")
    start_time = time.time()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # Step 1: Go to Google (direct)
            print("📍 Step 1: Navigating to Google...")
            page.goto("https://www.google.com/")
            page.wait_for_timeout(1000)
            
            # Step 2: Smart element detection
            print("🔍 Step 2: Finding search box...")
            
            # Try multiple selectors (smart fallback)
            selectors = [
                "textarea[name='q']",
                "input[name='q']", 
                "[role='searchbox']",
                "textarea[aria-label*='Search']"
            ]
            
            search_box = None
            for selector in selectors:
                try:
                    search_box = page.locator(selector).first
                    if search_box.is_visible():
                        print(f"   ✅ Found search box with: {selector}")
                        break
                except:
                    continue
            
            if not search_box:
                print("   ❌ Could not find search box")
                return False
            
            # Step 3: Click and type
            print("⌨️ Step 3: Typing search term...")
            search_box.click()
            search_box.fill("Python programming")
            page.wait_for_timeout(500)
            
            # Step 4: Press Enter
            print("⏎ Step 4: Pressing Enter...")
            search_box.press("Enter")
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
    success = smart_google_test()
    exit(0 if success else 1)