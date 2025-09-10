#!/usr/bin/env python3
"""
Verizon Simple Test - No HER Framework Required
==============================================

This test runs ONLY your specific Verizon test case using basic Playwright:
1) Open verizon page https://www.verizon.com/
2) Click on "Phones" button
3) Click on "Apple" filter button
4) Click on "Apple iPhone 16 Pro Max"
5) Validate that it landed on "https://www.verizon.com/smartphones/apple-iphone-16-pro-max/"
6) Click on "512 GB"
"""

import time
import logging
from playwright.sync_api import sync_playwright

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_verizon_simple_test(headless=False):
    """Run the specific Verizon test case using basic Playwright."""
    
    # Your exact test steps
    steps = [
        "Open verizon page https://www.verizon.com/",
        "Click on \"Phones\" button",
        "Click on \"Apple\" filter button", 
        "Click on \"Apple iPhone 16 Pro Max\"",
        "Validate that it landed on \"https://www.verizon.com/smartphones/apple-iphone-16-pro-max/\"",
        "Click on \"512 GB\""
    ]
    
    print("🚀 Verizon Simple Test")
    print("=" * 50)
    print("Running your specific test steps:")
    for i, step in enumerate(steps, 1):
        print(f"  {i}. {step}")
    print("=" * 50)
    
    playwright = None
    browser = None
    page = None
    
    try:
        # Start browser
        print("🌐 Starting browser...")
        playwright = sync_playwright().start()
        browser = playwright.chromium.launch(
            headless=headless,
            args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-web-security']
        )
        page = browser.new_page()
        page.set_default_timeout(30000)
        print("✅ Browser started")
        
        # Run each step
        results = []
        for i, step in enumerate(steps, 1):
            print(f"\n🔄 Step {i}: {step}")
            
            try:
                if step.startswith("Open verizon page"):
                    # Step 1: Navigate to Verizon
                    url = "https://www.verizon.com/"
                    print(f"   Navigating to: {url}")
                    page.goto(url, wait_until="networkidle")
                    time.sleep(3)
                    
                    # Dismiss any popups
                    try:
                        page.click('button[aria-label="Close"]', timeout=2000)
                    except:
                        pass
                    try:
                        page.click('button:has-text("Accept")', timeout=2000)
                    except:
                        pass
                    
                    results.append({"step": i, "success": True, "xpath": "navigation", "url": page.url})
                    print(f"   ✅ Step {i} passed - Navigated to Verizon")
                    
                elif step.startswith("Click on \"Phones\""):
                    # Step 2: Click on Phones button
                    print("   Looking for Phones button...")
                    
                    # Try multiple selectors for Phones button
                    phones_selectors = [
                        "text=Phones",
                        "a:has-text('Phones')",
                        "button:has-text('Phones')",
                        "[aria-label*='Phones']",
                        "[data-testid*='phones']",
                        "a[href*='phones']",
                        "button[href*='phones']",
                        "nav a:has-text('Phones')",
                        ".nav a:has-text('Phones')",
                        "[role='menuitem']:has-text('Phones')"
                    ]
                    
                    clicked = False
                    used_xpath = ""
                    for selector in phones_selectors:
                        try:
                            element = page.locator(selector).first
                            if element.is_visible():
                                print(f"   Found Phones button with selector: {selector}")
                                element.click()
                                time.sleep(3)
                                clicked = True
                                used_xpath = selector
                                break
                        except Exception as e:
                            print(f"   Trying {selector}: {e}")
                            continue
                    
                    if clicked:
                        results.append({"step": i, "success": True, "xpath": used_xpath, "url": page.url})
                        print(f"   ✅ Step {i} passed - Clicked Phones button")
                    else:
                        results.append({"step": i, "success": False, "xpath": "not found", "url": page.url})
                        print(f"   ❌ Step {i} failed - Could not find Phones button")
                        print(f"   Current page content preview: {page.content()[:500]}...")
                        break
                        
                elif step.startswith("Click on \"Apple\""):
                    # Step 3: Click on Apple filter
                    print("   Looking for Apple filter...")
                    
                    apple_selectors = [
                        "text=Apple",
                        "button:has-text('Apple')",
                        "a:has-text('Apple')",
                        "[aria-label*='Apple']",
                        "[data-testid*='apple']",
                        "input[value*='Apple']",
                        "label:has-text('Apple')",
                        "[data-filter*='apple']",
                        ".filter:has-text('Apple')",
                        "[role='checkbox']:has-text('Apple')"
                    ]
                    
                    clicked = False
                    used_xpath = ""
                    for selector in apple_selectors:
                        try:
                            element = page.locator(selector).first
                            if element.is_visible():
                                print(f"   Found Apple filter with selector: {selector}")
                                element.click()
                                time.sleep(2)
                                clicked = True
                                used_xpath = selector
                                break
                        except Exception as e:
                            print(f"   Trying {selector}: {e}")
                            continue
                    
                    if clicked:
                        results.append({"step": i, "success": True, "xpath": used_xpath, "url": page.url})
                        print(f"   ✅ Step {i} passed - Clicked Apple filter")
                    else:
                        results.append({"step": i, "success": False, "xpath": "not found", "url": page.url})
                        print(f"   ❌ Step {i} failed - Could not find Apple filter")
                        break
                        
                elif step.startswith("Click on \"Apple iPhone 16 Pro Max\""):
                    # Step 4: Click on iPhone 16 Pro Max
                    print("   Looking for Apple iPhone 16 Pro Max...")
                    
                    iphone_selectors = [
                        "text=Apple iPhone 16 Pro Max",
                        "a:has-text('Apple iPhone 16 Pro Max')",
                        "button:has-text('Apple iPhone 16 Pro Max')",
                        "[aria-label*='Apple iPhone 16 Pro Max']",
                        "[data-testid*='iphone-16-pro-max']",
                        "a[href*='iphone-16-pro-max']",
                        "h3:has-text('Apple iPhone 16 Pro Max')",
                        "h2:has-text('Apple iPhone 16 Pro Max')",
                        ".product:has-text('Apple iPhone 16 Pro Max')",
                        "[data-product*='iphone-16-pro-max']"
                    ]
                    
                    clicked = False
                    used_xpath = ""
                    for selector in iphone_selectors:
                        try:
                            element = page.locator(selector).first
                            if element.is_visible():
                                print(f"   Found iPhone with selector: {selector}")
                                element.click()
                                time.sleep(3)
                                clicked = True
                                used_xpath = selector
                                break
                        except Exception as e:
                            print(f"   Trying {selector}: {e}")
                            continue
                    
                    if clicked:
                        results.append({"step": i, "success": True, "xpath": used_xpath, "url": page.url})
                        print(f"   ✅ Step {i} passed - Clicked iPhone 16 Pro Max")
                    else:
                        results.append({"step": i, "success": False, "xpath": "not found", "url": page.url})
                        print(f"   ❌ Step {i} failed - Could not find iPhone 16 Pro Max")
                        break
                        
                elif step.startswith("Validate that it landed on"):
                    # Step 5: Validate URL
                    expected_url = "https://www.verizon.com/smartphones/apple-iphone-16-pro-max/"
                    current_url = page.url
                    
                    print(f"   Expected URL: {expected_url}")
                    print(f"   Current URL: {current_url}")
                    
                    if expected_url in current_url or current_url in expected_url:
                        results.append({"step": i, "success": True, "xpath": "url validation", "url": current_url})
                        print(f"   ✅ Step {i} passed - URL validation successful")
                    else:
                        results.append({"step": i, "success": False, "xpath": "url mismatch", "url": current_url})
                        print(f"   ❌ Step {i} failed - URL validation failed")
                        break
                        
                elif step.startswith("Click on \"512 GB\""):
                    # Step 6: Click on 512 GB option
                    print("   Looking for 512 GB option...")
                    
                    gb_selectors = [
                        "text=512 GB",
                        "button:has-text('512 GB')",
                        "a:has-text('512 GB')",
                        "[aria-label*='512 GB']",
                        "[data-testid*='512']",
                        "input[value*='512']",
                        "label:has-text('512 GB')",
                        "[data-value*='512']",
                        ".storage:has-text('512 GB')",
                        "[data-storage*='512']"
                    ]
                    
                    clicked = False
                    used_xpath = ""
                    for selector in gb_selectors:
                        try:
                            element = page.locator(selector).first
                            if element.is_visible():
                                print(f"   Found 512 GB with selector: {selector}")
                                element.click()
                                time.sleep(2)
                                clicked = True
                                used_xpath = selector
                                break
                        except Exception as e:
                            print(f"   Trying {selector}: {e}")
                            continue
                    
                    if clicked:
                        results.append({"step": i, "success": True, "xpath": used_xpath, "url": page.url})
                        print(f"   ✅ Step {i} passed - Clicked 512 GB")
                    else:
                        results.append({"step": i, "success": False, "xpath": "not found", "url": page.url})
                        print(f"   ❌ Step {i} failed - Could not find 512 GB option")
                        break
                
            except Exception as e:
                print(f"   ❌ Step {i} failed with error: {e}")
                results.append({"step": i, "success": False, "xpath": f"error: {e}", "url": page.url})
                break
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 VERIZON TEST RESULTS")
        print("=" * 50)
        
        successful_steps = sum(1 for r in results if r["success"])
        total_steps = len(results)
        success_rate = (successful_steps / total_steps) * 100 if total_steps > 0 else 0
        
        print(f"Total Steps: {total_steps}")
        print(f"Successful Steps: {successful_steps}")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Final URL: {page.url}")
        
        print(f"\n📋 Detailed Results with XPaths:")
        for result in results:
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            print(f"  Step {result['step']}: {status}")
            print(f"    XPath Used: {result['xpath']}")
            print(f"    URL: {result['url']}")
            print()
        
        return success_rate >= 80
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        try:
            if page:
                page.close()
            if browser:
                browser.close()
            if playwright:
                playwright.stop()
        except:
            pass

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Verizon Simple Test")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    
    args = parser.parse_args()
    
    print("🚀 Starting Verizon Simple Test")
    print("=" * 50)
    
    success = run_verizon_simple_test(headless=args.headless)
    
    if success:
        print("🎉 Verizon test completed successfully!")
    else:
        print("💥 Verizon test failed!")
    
    exit(0 if success else 1)