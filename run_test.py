#!/usr/bin/env python3
"""
HER Framework Test Runner
Simple launcher for natural language tests.
"""

import sys
import os
import subprocess

def main():
    """Launch the natural language test runner."""
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    test_runner_path = os.path.join(script_dir, 'tests', 'natural_test_runner.py')
    
    # Check if the test runner exists
    if not os.path.exists(test_runner_path):
        print(f"❌ Test runner not found at: {test_runner_path}")
        sys.exit(1)
    
    # Pass all arguments to the test runner
    cmd = [sys.executable, test_runner_path] + sys.argv[1:]
    
    try:
        # Run the test runner
        result = subprocess.run(cmd, cwd=script_dir)
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error running test: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()