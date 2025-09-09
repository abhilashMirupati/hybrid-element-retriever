#!/usr/bin/env python3

import os
import sys
sys.path.insert(0, 'src')

# Set up environment
os.environ['HER_MODELS_DIR'] = '/workspace/src/her/models'
os.environ['HER_CACHE_DIR'] = '/workspace/.her_cache'
os.environ['HER_E2E'] = '1'

def test_minimal():
    """Minimal test to check if the framework works"""
    try:
        from playwright.sync_api import sync_playwright
        
        print("Testing with Playwright directly...")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("https://www.verizon.com/")
            
            # Wait for page to load
            page.wait_for_timeout(3000)
            
            # Look for Phones link
            phones_link = page.locator('a:has-text("Phones")').first
            if phones_link.is_visible():
                print("✅ Found Phones link")
                phones_link.click()
                page.wait_for_timeout(2000)
                current_url = page.url
                print(f"Current URL after click: {current_url}")
                
                if "/smartphones/" in current_url:
                    print("✅ Successfully navigated to smartphones page")
                else:
                    print(f"❌ Unexpected URL: {current_url}")
            else:
                print("❌ Phones link not found or not visible")
                
            browser.close()
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_minimal()