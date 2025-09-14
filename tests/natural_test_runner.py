#!/usr/bin/env python3
"""
Natural Language Test Runner - Command Line Interface
Run tests using plain English descriptions.
"""

import sys
import os
import argparse

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.her.testing.natural_test_runner import run_natural_test

# Try to load environment variables from .env file (optional)
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("📁 Loaded configuration from .env file")
except ImportError:
    print("⚠️  python-dotenv not installed, using default environment variables")
    print("   Install with: pip install python-dotenv")
except Exception as e:
    print(f"⚠️  Could not load .env file: {e}")

# Set environment variables from .env file
os.environ.setdefault('HER_MODELS_DIR', os.getenv('HER_MODELS_DIR', './src/her/models'))
os.environ.setdefault('HER_CACHE_DIR', os.getenv('HER_CACHE_DIR', './.her_cache'))

# =============================================================================
# INLINE TEST CONFIGURATION
# =============================================================================
# You can define test steps directly here instead of using command line arguments
# Just uncomment and modify the test configuration below:

# Example test configuration - uncomment to use:
TEST_CONFIG = {
    "test_name": "Google Search Test",
    "start_url": "https://www.google.com/",
    "steps": [
        "Navigate to \"https://www.google.com/\"",
        "Click on \"search\""
    ],
    "headless": True
}

# Another example:
# TEST_CONFIG = {
#     "test_name": "Verizon Phone Shopping",
#     "start_url": "https://www.verizon.com/",
#     "steps": [
#         "Click on Phones",
#         "Click on Apple",
#         "Click on iPhone"
#     ],
#     "headless": True
# }

# =============================================================================

def main():
    """Main entry point for natural language test runner."""
    parser = argparse.ArgumentParser(description="Run natural language tests")
    parser.add_argument("--test", "-t", help="Test name")
    parser.add_argument("--url", "-u", help="Starting URL")
    parser.add_argument("--steps", "-s", nargs="+", help="Test steps in natural language")
    parser.add_argument("--headless", action="store_true", default=True, help="Run in headless mode")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--use-inline", action="store_true", help="Use inline test configuration from file")
    
    args = parser.parse_args()
    
    # Check if user wants to use inline configuration
    if args.use_inline:
        # Check if TEST_CONFIG is defined
        if 'TEST_CONFIG' not in globals():
            print("❌ No inline test configuration found!")
            print("Please uncomment and configure TEST_CONFIG in the file.")
            sys.exit(1)
        
        # Use inline configuration
        test_name = TEST_CONFIG["test_name"]
        start_url = TEST_CONFIG["start_url"]
        steps = TEST_CONFIG["steps"]
        headless = TEST_CONFIG["headless"]
        
        print("📝 Using inline test configuration from file")
    else:
        # Use command line arguments
        if not args.test or not args.url or not args.steps:
            print("Usage: python run_natural_test.py --test 'Test Name' --url 'https://example.com' --steps 'step1' 'step2' 'step3'")
            print("\nOr use inline configuration:")
            print("python run_natural_test.py --use-inline")
            print("\nExample:")
            print("python run_natural_test.py --test 'Verizon Phone Shopping' --url 'https://www.verizon.com/' --steps 'Click on Phones' 'Click on Apple' 'Click on iPhone'")
            sys.exit(1)
        
        test_name = args.test
        start_url = args.url
        steps = args.steps
        headless = args.headless
    
    print(f"🚀 Running test: {test_name}")
    print(f"📍 Starting URL: {start_url}")
    print(f"📝 Steps: {len(steps)}")
    for i, step in enumerate(steps, 1):
        print(f"   {i}. {step}")
    print()
    
    # Run the test
    result = run_natural_test(
        test_name=test_name,
        steps=steps,
        start_url=start_url,
        headless=headless
    )
    
    # Print results
    print("\n" + "="*60)
    print(f"📊 TEST RESULTS: {result['test_name']}")
    print("="*60)
    print(f"✅ Success: {result['success']}")
    print(f"📝 Message: {result['message']}")
    print(f"📈 Steps: {result['successful_steps']}/{result['total_steps']} successful")
    print(f"🌐 Final URL: {result['final_url']}")
    
    if result['step_results']:
        print(f"\n📋 Step Details:")
        for step_result in result['step_results']:
            status = "✅" if step_result['success'] else "❌"
            print(f"   {status} Step {step_result['step_number']}: {step_result.get('action', 'unknown')} -> {step_result.get('target', 'unknown')}")
            if not step_result['success']:
                print(f"      Error: {step_result['error']}")
    
    print("\n" + "="*60)
    
    # Exit with appropriate code
    sys.exit(0 if result['success'] else 1)


if __name__ == "__main__":
    main()