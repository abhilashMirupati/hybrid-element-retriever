#!/usr/bin/env python3
"""
Natural Language Test Runner - Command Line Interface
Run tests using plain English descriptions.
"""

import sys
import argparse
from src.her.testing.natural_test_runner import run_natural_test


def main():
    """Main entry point for natural language test runner."""
    parser = argparse.ArgumentParser(description="Run natural language tests")
    parser.add_argument("--test", "-t", help="Test name")
    parser.add_argument("--url", "-u", help="Starting URL")
    parser.add_argument("--steps", "-s", nargs="+", help="Test steps in natural language")
    parser.add_argument("--headless", action="store_true", default=True, help="Run in headless mode")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if not args.test or not args.url or not args.steps:
        print("Usage: python run_natural_test.py --test 'Test Name' --url 'https://example.com' --steps 'step1' 'step2' 'step3'")
        print("\nExample:")
        print("python run_natural_test.py --test 'Verizon Phone Shopping' --url 'https://www.verizon.com/' --steps 'Click on Phones' 'Click on Apple' 'Click on iPhone'")
        sys.exit(1)
    
    print(f"🚀 Running test: {args.test}")
    print(f"📍 Starting URL: {args.url}")
    print(f"📝 Steps: {len(args.steps)}")
    for i, step in enumerate(args.steps, 1):
        print(f"   {i}. {step}")
    print()
    
    # Run the test
    result = run_natural_test(
        test_name=args.test,
        steps=args.steps,
        start_url=args.url,
        headless=args.headless
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