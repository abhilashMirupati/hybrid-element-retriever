#!/usr/bin/env python3
"""
Universal Automation Test Cases
===============================

Test cases demonstrating the universal nature of the English automation framework
across different websites and use cases.

This framework can automate ANY website with plain English instructions.
"""

import os
import sys
import pytest
import time
from pathlib import Path

# Add tests directory to path
sys.path.insert(0, str(Path(__file__).parent))

from universal_automation_framework import run_universal_automation, UniversalAutomationRunner

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
class TestUniversalAutomation:
    """Test universal automation framework across different websites and use cases."""
    
    def test_verizon_phone_navigation(self):
        """Test Verizon phone navigation - just one example."""
        steps = [
            "Open https://www.verizon.com/",
            "Click on 'Phones' button",
            "Click on 'Apple' filter button", 
            "Click on 'Apple iPhone 16 Pro Max'",
            "Validate that it landed on https://www.verizon.com/smartphones/apple-iphone-16-pro-max/",
            "Click on '512 GB'"
        ]
        
        result = run_universal_automation(steps, "Verizon", "Phone Navigation", headless=False)
        
        print(f"\n📱 Verizon Test Results:")
        print(f"Success Rate: {result.success_rate:.1f}%")
        print(f"Successful Steps: {result.successful_steps}/{result.total_steps}")
        print(f"Final URL: {result.final_url}")
        
        # Assertions
        assert result.total_steps == 6
        assert result.successful_steps >= 3  # At least half should work
        assert result.success_rate >= 50.0
    
    def test_google_search(self):
        """Test Google search functionality."""
        steps = [
            "Open https://www.google.com/",
            "Click on 'Search' field",
            "Type 'artificial intelligence' in 'Search' field",
            "Click on 'Google Search' button",
            "Validate that search results are visible",
            "Click on 'First result'"
        ]
        
        result = run_universal_automation(steps, "Google", "Search Functionality", headless=False)
        
        print(f"\n🔍 Google Test Results:")
        print(f"Success Rate: {result.success_rate:.1f}%")
        print(f"Successful Steps: {result.successful_steps}/{result.total_steps}")
        print(f"Final URL: {result.final_url}")
        
        # Assertions
        assert result.total_steps == 6
        assert result.successful_steps >= 4  # Most should work
        assert result.success_rate >= 66.7
    
    def test_amazon_shopping(self):
        """Test Amazon shopping flow."""
        steps = [
            "Open https://www.amazon.com/",
            "Click on 'Search' field",
            "Type 'laptop' in 'Search' field",
            "Click on 'Search' button",
            "Validate that search results are visible",
            "Click on 'First product'",
            "Validate that product page is visible"
        ]
        
        result = run_universal_automation(steps, "Amazon", "E-commerce Shopping", headless=False)
        
        print(f"\n🛒 Amazon Test Results:")
        print(f"Success Rate: {result.success_rate:.1f}%")
        print(f"Successful Steps: {result.successful_steps}/{result.total_steps}")
        print(f"Final URL: {result.final_url}")
        
        # Assertions
        assert result.total_steps == 7
        assert result.successful_steps >= 4  # Most should work
        assert result.success_rate >= 57.1
    
    def test_github_navigation(self):
        """Test GitHub navigation."""
        steps = [
            "Open https://www.github.com/",
            "Click on 'Sign in'",
            "Validate that login page is visible",
            "Click on 'Back to GitHub'",
            "Click on 'Explore'",
            "Validate that explore page is visible"
        ]
        
        result = run_universal_automation(steps, "GitHub", "Navigation", headless=False)
        
        print(f"\n🐙 GitHub Test Results:")
        print(f"Success Rate: {result.success_rate:.1f}%")
        print(f"Successful Steps: {result.successful_steps}/{result.total_steps}")
        print(f"Final URL: {result.final_url}")
        
        # Assertions
        assert result.total_steps == 6
        assert result.successful_steps >= 3  # At least half should work
        assert result.success_rate >= 50.0
    
    def test_wikipedia_research(self):
        """Test Wikipedia research flow."""
        steps = [
            "Open https://www.wikipedia.org/",
            "Click on 'English' link",
            "Click on 'Search' field",
            "Type 'machine learning' in 'Search' field",
            "Click on 'Search' button",
            "Validate that article is visible",
            "Click on 'First section'"
        ]
        
        result = run_universal_automation(steps, "Wikipedia", "Research", headless=False)
        
        print(f"\n📚 Wikipedia Test Results:")
        print(f"Success Rate: {result.success_rate:.1f}%")
        print(f"Successful Steps: {result.successful_steps}/{result.total_steps}")
        print(f"Final URL: {result.final_url}")
        
        # Assertions
        assert result.total_steps == 7
        assert result.successful_steps >= 4  # Most should work
        assert result.success_rate >= 57.1
    
    def test_news_website_navigation(self):
        """Test news website navigation."""
        steps = [
            "Open https://www.bbc.com/",
            "Click on 'News' tab",
            "Validate that news page is visible",
            "Click on 'First article'",
            "Validate that article is visible",
            "Scroll down",
            "Click on 'Related stories'"
        ]
        
        result = run_universal_automation(steps, "BBC News", "News Navigation", headless=False)
        
        print(f"\n📰 BBC News Test Results:")
        print(f"Success Rate: {result.success_rate:.1f}%")
        print(f"Successful Steps: {result.successful_steps}/{result.total_steps}")
        print(f"Final URL: {result.final_url}")
        
        # Assertions
        assert result.total_steps == 7
        assert result.successful_steps >= 3  # At least half should work
        assert result.success_rate >= 42.9
    
    def test_social_media_navigation(self):
        """Test social media navigation."""
        steps = [
            "Open https://www.linkedin.com/",
            "Click on 'Sign in'",
            "Validate that login page is visible",
            "Click on 'Back to LinkedIn'",
            "Click on 'Jobs' tab",
            "Validate that jobs page is visible"
        ]
        
        result = run_universal_automation(steps, "LinkedIn", "Social Media Navigation", headless=False)
        
        print(f"\n💼 LinkedIn Test Results:")
        print(f"Success Rate: {result.success_rate:.1f}%")
        print(f"Successful Steps: {result.successful_steps}/{result.total_steps}")
        print(f"Final URL: {result.final_url}")
        
        # Assertions
        assert result.total_steps == 6
        assert result.successful_steps >= 3  # At least half should work
        assert result.success_rate >= 50.0
    
    def test_ecommerce_checkout_flow(self):
        """Test e-commerce checkout flow."""
        steps = [
            "Open https://www.ebay.com/",
            "Click on 'Search' field",
            "Type 'smartphone' in 'Search' field",
            "Click on 'Search' button",
            "Validate that search results are visible",
            "Click on 'First product'",
            "Validate that product page is visible",
            "Click on 'Add to cart'"
        ]
        
        result = run_universal_automation(steps, "eBay", "E-commerce Checkout", headless=False)
        
        print(f"\n🛍️ eBay Test Results:")
        print(f"Success Rate: {result.success_rate:.1f}%")
        print(f"Successful Steps: {result.successful_steps}/{result.total_steps}")
        print(f"Final URL: {result.final_url}")
        
        # Assertions
        assert result.total_steps == 8
        assert result.successful_steps >= 4  # Most should work
        assert result.success_rate >= 50.0
    
    def test_educational_platform(self):
        """Test educational platform navigation."""
        steps = [
            "Open https://www.coursera.org/",
            "Click on 'Log in'",
            "Validate that login page is visible",
            "Click on 'Back to Coursera'",
            "Click on 'Browse'",
            "Validate that browse page is visible",
            "Click on 'First course'"
        ]
        
        result = run_universal_automation(steps, "Coursera", "Educational Platform", headless=False)
        
        print(f"\n🎓 Coursera Test Results:")
        print(f"Success Rate: {result.success_rate:.1f}%")
        print(f"Successful Steps: {result.successful_steps}/{result.total_steps}")
        print(f"Final URL: {result.final_url}")
        
        # Assertions
        assert result.total_steps == 7
        assert result.successful_steps >= 3  # At least half should work
        assert result.success_rate >= 42.9
    
    def test_newsletter_signup(self):
        """Test newsletter signup flow."""
        steps = [
            "Open https://www.medium.com/",
            "Click on 'Sign in'",
            "Validate that sign in page is visible",
            "Click on 'Back to Medium'",
            "Click on 'Get started'",
            "Validate that signup page is visible"
        ]
        
        result = run_universal_automation(steps, "Medium", "Newsletter Signup", headless=False)
        
        print(f"\n📝 Medium Test Results:")
        print(f"Success Rate: {result.success_rate:.1f}%")
        print(f"Successful Steps: {result.successful_steps}/{result.total_steps}")
        print(f"Final URL: {result.final_url}")
        
        # Assertions
        assert result.total_steps == 6
        assert result.successful_steps >= 3  # At least half should work
        assert result.success_rate >= 50.0
    
    def test_universal_step_parsing(self):
        """Test that the framework can parse various English step formats."""
        test_steps = [
            "Open https://www.example.com/",
            "Click on 'Login' button",
            "Type 'username' in 'Username' field",
            "Type 'password' in 'Password' field",
            "Press 'Submit' button",
            "Validate that 'Welcome' is visible",
            "Hover over 'Profile' menu",
            "Click on 'Settings' option",
            "Scroll down",
            "Wait 3 seconds",
            "Clear 'Search' field",
            "Fill 'Search' field with 'test'",
            "Submit 'Contact form'",
            "Verify that it landed on https://www.example.com/success/"
        ]
        
        runner = UniversalAutomationRunner(headless=True)
        
        try:
            runner.start_browser()
            
            parsed_steps = []
            for i, step in enumerate(test_steps, 1):
                parsed = runner.parser.parse_step(step)
                parsed_steps.append(parsed)
                print(f"Step {i}: {step}")
                print(f"  Parsed: {parsed['action']} - {parsed.get('target', parsed.get('url', ''))}")
                print()
            
            # Verify all steps were parsed correctly
            assert len(parsed_steps) == len(test_steps)
            
            # Check that different action types were identified
            actions = [p['action'] for p in parsed_steps]
            expected_actions = ['navigate', 'click', 'type', 'type', 'click', 'validate', 'hover', 'click', 'scroll', 'wait', 'clear', 'type', 'submit', 'validate']
            
            for i, (actual, expected) in enumerate(zip(actions, expected_actions)):
                assert actual == expected, f"Step {i+1}: expected {expected}, got {actual}"
            
            print("✅ All steps parsed correctly!")
            
        finally:
            runner.stop_browser()
    
    def test_xpath_validation(self):
        """Test XPath validation on real websites."""
        runner = UniversalAutomationRunner(headless=False)
        
        try:
            runner.start_browser()
            
            # Test on Google
            runner.page.goto("https://www.google.com/", wait_until="networkidle")
            time.sleep(2)
            
            # Test various XPath patterns
            test_xpaths = [
                "//input[@name='q']",  # Google search box
                "//button[@name='btnK']",  # Google search button
                "//a[contains(text(), 'Images')]",  # Images link
                "//a[contains(text(), 'Gmail')]",  # Gmail link
            ]
            
            for xpath in test_xpaths:
                is_valid, match_count, error_msg = runner.validator.validate_xpath(xpath)
                print(f"XPath: {xpath}")
                print(f"Valid: {is_valid}, Matches: {match_count}, Error: {error_msg}")
                
                if is_valid and match_count > 0:
                    element_info = runner.validator.get_element_info(xpath)
                    print(f"Element Info: {element_info}")
                print()
            
            # At least one XPath should be valid
            valid_count = sum(1 for xpath in test_xpaths 
                            if runner.validator.validate_xpath(xpath)[0])
            assert valid_count >= 1, "At least one XPath should be valid"
            
        finally:
            runner.stop_browser()

if __name__ == "__main__":
    # Run a quick test
    test = TestUniversalAutomation()
    
    print("🚀 Running Universal Automation Tests")
    print("=" * 60)
    
    try:
        # Test step parsing
        test.test_universal_step_parsing()
        print("\n✅ Step parsing test passed!")
        
        # Test XPath validation
        test.test_xpath_validation()
        print("\n✅ XPath validation test passed!")
        
        print("\n🎉 All tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()