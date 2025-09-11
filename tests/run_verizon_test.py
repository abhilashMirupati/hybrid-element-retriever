#!/usr/bin/env python3
"""
Verizon Real-World Test Runner
==============================

This script runs the English automation framework against the real Verizon website
and provides detailed XPath validation and debugging information.

Usage:
    python run_verizon_test.py [--headless] [--debug]
"""

import os
import sys
import argparse
import time
import json
from pathlib import Path

# Add tests directory to path
sys.path.insert(0, str(Path(__file__).parent))

from english_automation_framework import run_english_automation, EnglishAutomationRunner

def run_verizon_test(headless=False, debug=False):
    """Run the Verizon test with detailed validation."""
    
    print("🚀 Verizon English Automation Test")
    print("=" * 60)
    print(f"Headless mode: {headless}")
    print(f"Debug mode: {debug}")
    print("=" * 60)
    
    # Define test steps
    steps = [
        "Open https://www.verizon.com/",
        "Click on 'Phones' button",
        "Click on 'Apple' filter button", 
        "Click on 'Apple iPhone 16 Pro Max'",
        "Validate that it landed on https://www.verizon.com/smartphones/apple-iphone-16-pro-max/",
        "Click on '512 GB'"
    ]
    
    print("\n📋 Test Steps:")
    for i, step in enumerate(steps, 1):
        print(f"  {i}. {step}")
    
    print("\n" + "=" * 60)
    print("Starting automation...")
    print("=" * 60)
    
    # Run the automation
    start_time = time.time()
    result = run_english_automation(steps, headless=headless)
    total_time = time.time() - start_time
    
    # Print results
    print("\n📊 AUTOMATION RESULTS")
    print("=" * 60)
    print(f"Total Steps: {result.total_steps}")
    print(f"Successful: {result.successful_steps}")
    print(f"Failed: {result.failed_steps}")
    print(f"Success Rate: {result.success_rate:.1f}%")
    print(f"Total Time: {total_time:.2f}s")
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
    
    # Debug mode - run additional validation
    if debug:
        print("\n🔍 DEBUG MODE - Additional Validation")
        print("=" * 60)
        
        runner = EnglishAutomationRunner(headless=headless)
        
        try:
            runner.start_browser()
            
            # Navigate to Verizon
            print("🌐 Navigating to Verizon...")
            runner.page.goto("https://www.verizon.com/", wait_until="networkidle")
            time.sleep(3)
            
            # Test each step individually
            for i, step in enumerate(steps, 1):
                print(f"\n🔍 DEBUG STEP {i}: {step}")
                print("-" * 40)
                
                result = runner.execute_step(i, step)
                
                if result.selector:
                    # Validate XPath
                    is_valid, match_count, error_msg = runner.validator.validate_xpath(result.selector)
                    print(f"XPath Validation: {'✅ Valid' if is_valid else '❌ Invalid'}")
                    print(f"Match Count: {match_count}")
                    if error_msg:
                        print(f"Error: {error_msg}")
                    
                    # Get element details
                    if is_valid and match_count > 0:
                        element_info = runner.validator.get_element_info(result.selector)
                        print(f"Element Details:")
                        for j, element in enumerate(element_info.get('elements', [])[:3]):
                            print(f"  Element {j+1}:")
                            print(f"    Text: {element.get('text', '')[:100]}...")
                            print(f"    Tag: {element.get('tag', '')}")
                            print(f"    Visible: {element.get('visible', False)}")
                            print(f"    Enabled: {element.get('enabled', False)}")
                
                if not result.success:
                    print(f"❌ Step failed: {result.error_message}")
                else:
                    print(f"✅ Step passed")
                
                # Wait between steps
                time.sleep(2)
            
        finally:
            runner.stop_browser()
    
    # Final assessment
    print("\n🎯 FINAL ASSESSMENT")
    print("=" * 60)
    
    success_rate = result.success_rate if hasattr(result, 'success_rate') else 0.0
    
    if success_rate >= 80:
        print("✅ EXCELLENT: Framework performed very well")
    elif success_rate >= 60:
        print("✅ GOOD: Framework performed well with minor issues")
    elif success_rate >= 40:
        print("⚠️  FAIR: Framework had some issues but made progress")
    else:
        print("❌ POOR: Framework had significant issues")
    
    print(f"Success Rate: {success_rate:.1f}%")
    print(f"Total Time: {total_time:.2f}s")
    
    # Return success status
    return success_rate >= 60

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run Verizon English Automation Test")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode with additional validation")
    
    args = parser.parse_args()
    
    try:
        success = run_verizon_test(headless=args.headless, debug=args.debug)
        
        if success:
            print("\n🎉 Test completed successfully!")
            sys.exit(0)
        else:
            print("\n💥 Test failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()