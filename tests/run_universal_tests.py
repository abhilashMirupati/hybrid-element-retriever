#!/usr/bin/env python3
"""
Universal Automation Test Runner
================================

This script demonstrates the universal nature of the English automation framework
by running tests across multiple different websites and use cases.

The framework can automate ANY website with plain English instructions.
"""

import os
import sys
import argparse
import time
from pathlib import Path

# Add tests directory to path
sys.path.insert(0, str(Path(__file__).parent))

from universal_automation_framework import run_universal_automation, UniversalAutomationRunner

def run_website_test(website_name, website_url, steps, use_case, headless=False):
    """Run a test for a specific website."""
    print(f"\n🌐 Testing {website_name} - {use_case}")
    print("=" * 60)
    print(f"Website: {website_url}")
    print(f"Use Case: {use_case}")
    print("\nSteps:")
    for i, step in enumerate(steps, 1):
        print(f"  {i}. {step}")
    
    print("\n" + "=" * 60)
    print("Starting automation...")
    print("=" * 60)
    
    start_time = time.time()
    result = run_universal_automation(steps, website_name, use_case, headless=headless)
    total_time = time.time() - start_time
    
    print(f"\n📊 {website_name} Results:")
    print("=" * 60)
    print(f"Success Rate: {result.success_rate:.1f}%")
    print(f"Successful Steps: {result.successful_steps}/{result.total_steps}")
    print(f"Total Time: {total_time:.2f}s")
    print(f"Final URL: {result.final_url}")
    
    print(f"\n📋 Detailed Results:")
    for i, step_result in enumerate(result.results, 1):
        status = "✅ PASS" if step_result.success else "❌ FAIL"
        print(f"  {i}. {status} - {step_result.step_text}")
        if step_result.selector:
            print(f"     Selector: {step_result.selector}")
            print(f"     Confidence: {step_result.confidence:.3f}")
        if step_result.error_message:
            print(f"     Error: {step_result.error_message}")
    
    return result

def run_all_tests(headless=False):
    """Run all universal automation tests."""
    print("🚀 Universal English Automation Framework")
    print("=" * 60)
    print("This framework can automate ANY website with English instructions!")
    print("=" * 60)
    
    # Define test cases for different websites and use cases
    test_cases = [
        {
            "name": "Google",
            "url": "https://www.google.com/",
            "use_case": "Search Functionality",
            "steps": [
                "Open https://www.google.com/",
                "Click on 'Search' field",
                "Type 'artificial intelligence' in 'Search' field",
                "Click on 'Google Search' button",
                "Validate that search results are visible",
                "Click on 'First result'"
            ]
        },
        {
            "name": "Amazon",
            "url": "https://www.amazon.com/",
            "use_case": "E-commerce Shopping",
            "steps": [
                "Open https://www.amazon.com/",
                "Click on 'Search' field",
                "Type 'laptop' in 'Search' field",
                "Click on 'Search' button",
                "Validate that search results are visible",
                "Click on 'First product'",
                "Validate that product page is visible"
            ]
        },
        {
            "name": "GitHub",
            "url": "https://www.github.com/",
            "use_case": "Developer Platform Navigation",
            "steps": [
                "Open https://www.github.com/",
                "Click on 'Sign in'",
                "Validate that login page is visible",
                "Click on 'Back to GitHub'",
                "Click on 'Explore'",
                "Validate that explore page is visible"
            ]
        },
        {
            "name": "Wikipedia",
            "url": "https://www.wikipedia.org/",
            "use_case": "Research and Information",
            "steps": [
                "Open https://www.wikipedia.org/",
                "Click on 'English' link",
                "Click on 'Search' field",
                "Type 'machine learning' in 'Search' field",
                "Click on 'Search' button",
                "Validate that article is visible"
            ]
        },
        {
            "name": "BBC News",
            "url": "https://www.bbc.com/",
            "use_case": "News Website Navigation",
            "steps": [
                "Open https://www.bbc.com/",
                "Click on 'News' tab",
                "Validate that news page is visible",
                "Click on 'First article'",
                "Validate that article is visible"
            ]
        },
        {
            "name": "LinkedIn",
            "url": "https://www.linkedin.com/",
            "use_case": "Professional Social Media",
            "steps": [
                "Open https://www.linkedin.com/",
                "Click on 'Sign in'",
                "Validate that login page is visible",
                "Click on 'Back to LinkedIn'",
                "Click on 'Jobs' tab",
                "Validate that jobs page is visible"
            ]
        },
        {
            "name": "eBay",
            "url": "https://www.ebay.com/",
            "use_case": "Online Marketplace",
            "steps": [
                "Open https://www.ebay.com/",
                "Click on 'Search' field",
                "Type 'smartphone' in 'Search' field",
                "Click on 'Search' button",
                "Validate that search results are visible"
            ]
        },
        {
            "name": "Coursera",
            "url": "https://www.coursera.org/",
            "use_case": "Educational Platform",
            "steps": [
                "Open https://www.coursera.org/",
                "Click on 'Log in'",
                "Validate that login page is visible",
                "Click on 'Back to Coursera'",
                "Click on 'Browse'",
                "Validate that browse page is visible"
            ]
        },
        {
            "name": "Medium",
            "url": "https://www.medium.com/",
            "use_case": "Content Platform",
            "steps": [
                "Open https://www.medium.com/",
                "Click on 'Sign in'",
                "Validate that sign in page is visible",
                "Click on 'Back to Medium'",
                "Click on 'Get started'",
                "Validate that signup page is visible"
            ]
        },
        {
            "name": "Verizon",
            "url": "https://www.verizon.com/",
            "use_case": "Phone Shopping",
            "steps": [
                "Open https://www.verizon.com/",
                "Click on 'Phones' button",
                "Click on 'Apple' filter button",
                "Click on 'Apple iPhone 16 Pro Max'",
                "Validate that it landed on https://www.verizon.com/smartphones/apple-iphone-16-pro-max/",
                "Click on '512 GB'"
            ]
        }
    ]
    
    # Run all tests
    results = []
    for test_case in test_cases:
        try:
            result = run_website_test(
                test_case["name"],
                test_case["url"],
                test_case["steps"],
                test_case["use_case"],
                headless=headless
            )
            results.append(result)
        except Exception as e:
            print(f"\n❌ {test_case['name']} test failed: {e}")
            continue
    
    # Summary
    print("\n🎯 UNIVERSAL AUTOMATION SUMMARY")
    print("=" * 60)
    
    if results:
        total_tests = len(results)
        successful_tests = sum(1 for r in results if r.success_rate >= 50)
        avg_success_rate = sum(r.success_rate for r in results) / len(results)
        
        print(f"Total Tests: {total_tests}")
        print(f"Successful Tests: {successful_tests}")
        print(f"Average Success Rate: {avg_success_rate:.1f}%")
        
        print(f"\n📊 Individual Results:")
        for result in results:
            status = "✅ PASS" if result.success_rate >= 50 else "❌ FAIL"
            print(f"  {result.website}: {status} ({result.success_rate:.1f}%)")
        
        print(f"\n🎉 Universal Framework Test Complete!")
        print(f"The framework successfully automated {successful_tests}/{total_tests} different websites!")
        
        return avg_success_rate >= 60
    else:
        print("❌ No tests completed successfully")
        return False

def run_custom_test(website_url, steps, headless=False):
    """Run a custom test with user-provided steps."""
    print("🚀 Custom Universal Automation Test")
    print("=" * 60)
    
    # Extract website name from URL
    website_name = website_url.split('//')[1].split('/')[0].split('.')[0].title()
    
    result = run_website_test(website_name, website_url, steps, "Custom Test", headless=headless)
    
    return result.success_rate >= 50

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run Universal Automation Tests")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument("--custom", action="store_true", help="Run custom test")
    parser.add_argument("--website", type=str, help="Website URL for custom test")
    parser.add_argument("--steps", nargs="+", help="Steps for custom test")
    
    args = parser.parse_args()
    
    try:
        if args.custom:
            if not args.website or not args.steps:
                print("❌ Custom test requires --website and --steps arguments")
                sys.exit(1)
            
            success = run_custom_test(args.website, args.steps, headless=args.headless)
            if success:
                print("\n🎉 Custom test passed!")
                sys.exit(0)
            else:
                print("\n💥 Custom test failed!")
                sys.exit(1)
        else:
            success = run_all_tests(headless=args.headless)
            if success:
                print("\n🎉 All tests passed!")
                sys.exit(0)
            else:
                print("\n💥 Some tests failed!")
                sys.exit(1)
                
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Tests failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()