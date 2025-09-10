#!/usr/bin/env python3
"""
Verizon English Automation Test
===============================

Real-world test of the English automation framework against Verizon's website.
This test validates that the framework can actually find and interact with
real elements using XPath validation.

Test Steps:
1. Open verizon page https://www.verizon.com/
2. Click on "Phones" button
3. Click on "Apple" filter button
4. Click on "Apple iPhone 16 Pro Max"
5. Validate that it landed on "https://www.verizon.com/smartphones/apple-iphone-16-pro-max/"
6. Click on "512 GB"
"""

import os
import sys
import pytest
import time
from pathlib import Path

# Add tests directory to path
sys.path.insert(0, str(Path(__file__).parent))

from english_automation_framework import run_english_automation, EnglishAutomationRunner

# Check if we can run e2e tests
PLAYWRIGHT_AVAILABLE = True
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

HER_AVAILABLE = True
try:
    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
    from her.core.runner import Runner
except ImportError:
    HER_AVAILABLE = False

@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not available")
@pytest.mark.skipif(not HER_AVAILABLE, reason="HER framework not available")
@pytest.mark.skipif(os.getenv("HER_E2E") != "1", reason="Set HER_E2E=1 to run live e2e test")
@pytest.mark.timeout(300)
class TestVerizonEnglishAutomation:
    """Test English automation framework with real Verizon website."""
    
    def test_verizon_phone_navigation_flow(self):
        """Test complete Verizon phone navigation flow using English steps."""
        
        # Define the test steps in plain English
        steps = [
            "Open https://www.verizon.com/",
            "Click on 'Phones' button",
            "Click on 'Apple' filter button", 
            "Click on 'Apple iPhone 16 Pro Max'",
            "Validate that it landed on https://www.verizon.com/smartphones/apple-iphone-16-pro-max/",
            "Click on '512 GB'"
        ]
        
        print("\n🚀 Starting Verizon English Automation Test")
        print("=" * 60)
        print("Test Steps:")
        for i, step in enumerate(steps, 1):
            print(f"  {i}. {step}")
        print("=" * 60)
        
        # Run the automation
        result = run_english_automation(steps, headless=False)
        
        # Print detailed results
        print("\n📊 AUTOMATION RESULTS")
        print("=" * 60)
        print(f"Total Steps: {result.total_steps}")
        print(f"Successful: {result.successful_steps}")
        print(f"Failed: {result.failed_steps}")
        print(f"Success Rate: {result.success_rate:.1f}%")
        print(f"Total Time: {result.total_time:.2f}s")
        print(f"Final URL: {result.final_url}")
        
        print("\n📋 DETAILED STEP RESULTS")
        print("=" * 60)
        for i, step_result in enumerate(result.results, 1):
            status = "✅ PASS" if step_result.success else "❌ FAIL"
            print(f"\n{i}. {status} - {step_result.step_text}")
            print(f"   Execution Time: {step_result.execution_time:.2f}s")
            
            if step_result.selector:
                print(f"   XPath Selector: {step_result.selector}")
                print(f"   Confidence: {step_result.confidence:.3f}")
                print(f"   XPath Matches: {step_result.xpath_matches}")
                print(f"   Validation Passed: {step_result.validation_passed}")
            
            if step_result.error_message:
                print(f"   Error: {step_result.error_message}")
        
        # Assertions
        assert result.total_steps == 6, f"Expected 6 steps, got {result.total_steps}"
        assert result.successful_steps >= 4, f"Expected at least 4 successful steps, got {result.successful_steps}"
        assert result.success_rate >= 66.7, f"Expected at least 66.7% success rate, got {result.success_rate:.1f}%"
        
        # Check specific step results
        assert result.results[0].success, f"Step 1 (Navigate) failed: {result.results[0].error_message}"
        assert result.results[1].success, f"Step 2 (Click Phones) failed: {result.results[1].error_message}"
        
        print(f"\n✅ Test completed successfully with {result.success_rate:.1f}% success rate")
    
    def test_verizon_step_by_step_validation(self):
        """Test each step individually with detailed XPath validation."""
        
        runner = EnglishAutomationRunner(headless=False)
        
        try:
            # Start browser
            runner.start_browser()
            
            # Step 1: Navigate to Verizon
            print("\n🔍 STEP 1: Navigate to Verizon")
            result1 = runner.execute_step(1, "Open https://www.verizon.com/")
            assert result1.success, f"Navigation failed: {result1.error_message}"
            print(f"✅ Navigation successful: {runner.page.url}")
            
            # Step 2: Find and click Phones button
            print("\n🔍 STEP 2: Find Phones button")
            result2 = runner.execute_step(2, "Click on 'Phones' button")
            
            if result2.success:
                print(f"✅ Phones button clicked successfully")
                print(f"   XPath: {result2.selector}")
                print(f"   Confidence: {result2.confidence:.3f}")
                print(f"   XPath Matches: {result2.xpath_matches}")
            else:
                print(f"❌ Phones button click failed: {result2.error_message}")
                
                # Try to find Phones button manually for debugging
                print("\n🔍 DEBUG: Searching for Phones button...")
                try:
                    # Try different selectors
                    selectors = [
                        "text=Phones",
                        "[aria-label*='Phones']",
                        "button:has-text('Phones')",
                        "a:has-text('Phones')",
                        "[data-testid*='phones']",
                    ]
                    
                    for selector in selectors:
                        try:
                            element = runner.page.locator(selector).first
                            if element.is_visible():
                                print(f"   Found element with selector: {selector}")
                                print(f"   Text: {element.text_content()}")
                                print(f"   Tag: {element.evaluate('el => el.tagName')}")
                                print(f"   Visible: {element.is_visible()}")
                                break
                        except Exception as e:
                            continue
                    else:
                        print("   No Phones button found with any selector")
                        
                except Exception as e:
                    print(f"   Debug search failed: {e}")
            
            # Step 3: Find and click Apple filter
            print("\n🔍 STEP 3: Find Apple filter")
            result3 = runner.execute_step(3, "Click on 'Apple' filter button")
            
            if result3.success:
                print(f"✅ Apple filter clicked successfully")
                print(f"   XPath: {result3.selector}")
                print(f"   Confidence: {result3.confidence:.3f}")
                print(f"   XPath Matches: {result3.xpath_matches}")
            else:
                print(f"❌ Apple filter click failed: {result3.error_message}")
                
                # Debug Apple filter
                print("\n🔍 DEBUG: Searching for Apple filter...")
                try:
                    selectors = [
                        "text=Apple",
                        "[aria-label*='Apple']",
                        "button:has-text('Apple')",
                        "input[value*='Apple']",
                        "[data-testid*='apple']",
                        "[id*='Apple']",
                    ]
                    
                    for selector in selectors:
                        try:
                            elements = runner.page.locator(selector)
                            count = elements.count()
                            if count > 0:
                                print(f"   Found {count} elements with selector: {selector}")
                                for i in range(min(count, 3)):
                                    element = elements.nth(i)
                                    if element.is_visible():
                                        print(f"     Element {i+1}: {element.text_content()[:50]}...")
                                        print(f"     Tag: {element.evaluate('el => el.tagName')}")
                                        print(f"     Visible: {element.is_visible()}")
                            break
                        except Exception as e:
                            continue
                    else:
                        print("   No Apple filter found with any selector")
                        
                except Exception as e:
                    print(f"   Debug search failed: {e}")
            
            # Step 4: Find iPhone product
            print("\n🔍 STEP 4: Find iPhone 16 Pro Max")
            result4 = runner.execute_step(4, "Click on 'Apple iPhone 16 Pro Max'")
            
            if result4.success:
                print(f"✅ iPhone product clicked successfully")
                print(f"   XPath: {result4.selector}")
                print(f"   Confidence: {result4.confidence:.3f}")
                print(f"   XPath Matches: {result4.xpath_matches}")
            else:
                print(f"❌ iPhone product click failed: {result4.error_message}")
            
            # Step 5: Validate URL
            print("\n🔍 STEP 5: Validate URL")
            result5 = runner.execute_step(5, "Validate that it landed on https://www.verizon.com/smartphones/apple-iphone-16-pro-max/")
            
            if result5.success:
                print(f"✅ URL validation passed")
                print(f"   Current URL: {runner.page.url}")
            else:
                print(f"❌ URL validation failed: {result5.error_message}")
                print(f"   Current URL: {runner.page.url}")
            
            # Step 6: Find storage option
            print("\n🔍 STEP 6: Find 512 GB option")
            result6 = runner.execute_step(6, "Click on '512 GB'")
            
            if result6.success:
                print(f"✅ Storage option clicked successfully")
                print(f"   XPath: {result6.selector}")
                print(f"   Confidence: {result6.confidence:.3f}")
                print(f"   XPath Matches: {result6.xpath_matches}")
            else:
                print(f"❌ Storage option click failed: {result6.error_message}")
                
                # Debug storage options
                print("\n🔍 DEBUG: Searching for storage options...")
                try:
                    selectors = [
                        "text=512",
                        "text=512 GB",
                        "[aria-label*='512']",
                        "button:has-text('512')",
                        "input[value*='512']",
                        "[data-testid*='512']",
                    ]
                    
                    for selector in selectors:
                        try:
                            elements = runner.page.locator(selector)
                            count = elements.count()
                            if count > 0:
                                print(f"   Found {count} elements with selector: {selector}")
                                for i in range(min(count, 3)):
                                    element = elements.nth(i)
                                    if element.is_visible():
                                        print(f"     Element {i+1}: {element.text_content()[:50]}...")
                                        print(f"     Tag: {element.evaluate('el => el.tagName')}")
                                        print(f"     Visible: {element.is_visible()}")
                            break
                        except Exception as e:
                            continue
                    else:
                        print("   No storage options found with any selector")
                        
                except Exception as e:
                    print(f"   Debug search failed: {e}")
            
            # Summary
            results = [result1, result2, result3, result4, result5, result6]
            successful = sum(1 for r in results if r.success)
            print(f"\n📊 SUMMARY: {successful}/6 steps successful ({successful/6*100:.1f}%)")
            
        finally:
            runner.stop_browser()
    
    def test_verizon_xpath_validation_only(self):
        """Test XPath validation on Verizon page without full automation."""
        
        runner = EnglishAutomationRunner(headless=False)
        
        try:
            runner.start_browser()
            
            # Navigate to Verizon
            print("🌐 Navigating to Verizon...")
            runner.page.goto("https://www.verizon.com/", wait_until="networkidle")
            time.sleep(3)
            
            # Test finding Phones button
            print("\n🔍 Testing Phones button detection...")
            if runner.her_runner:
                snapshot = runner.her_runner._snapshot()
                result = runner.her_runner._resolve_selector("Phones", snapshot)
                
                print(f"HER Result: {result}")
                
                if result.get('selector'):
                    xpath = result['selector']
                    is_valid, match_count, error_msg = runner.validator.validate_xpath(xpath)
                    
                    print(f"XPath: {xpath}")
                    print(f"Valid: {is_valid}")
                    print(f"Matches: {match_count}")
                    print(f"Error: {error_msg}")
                    
                    if is_valid and match_count > 0:
                        # Get element details
                        element_info = runner.validator.get_element_info(xpath)
                        print(f"Element Info: {json.dumps(element_info, indent=2)}")
            
            # Test finding Apple filter
            print("\n🔍 Testing Apple filter detection...")
            if runner.her_runner:
                snapshot = runner.her_runner._snapshot()
                result = runner.her_runner._resolve_selector("Apple", snapshot)
                
                print(f"HER Result: {result}")
                
                if result.get('selector'):
                    xpath = result['selector']
                    is_valid, match_count, error_msg = runner.validator.validate_xpath(xpath)
                    
                    print(f"XPath: {xpath}")
                    print(f"Valid: {is_valid}")
                    print(f"Matches: {match_count}")
                    print(f"Error: {error_msg}")
                    
                    if is_valid and match_count > 0:
                        # Get element details
                        element_info = runner.validator.get_element_info(xpath)
                        print(f"Element Info: {json.dumps(element_info, indent=2)}")
            
        finally:
            runner.stop_browser()

if __name__ == "__main__":
    # Run the test directly
    test = TestVerizonEnglishAutomation()
    
    print("🚀 Running Verizon English Automation Test")
    print("=" * 60)
    
    try:
        test.test_verizon_phone_navigation_flow()
        print("\n✅ All tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()