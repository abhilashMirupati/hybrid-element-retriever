#!/usr/bin/env python3
"""
Dependency checker for HER framework.

This script checks if all required dependencies are installed and provides
helpful error messages if they're missing.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def check_dependency(module_name: str, package_name: str = None, install_command: str = None) -> bool:
    """Check if a dependency is available."""
    try:
        __import__(module_name)
        print(f"✅ {module_name} is available")
        return True
    except ImportError:
        package = package_name or module_name
        cmd = install_command or f"pip install {package}"
        print(f"❌ {module_name} is missing. Install with: {cmd}")
        return False

def check_optional_dependency(module_name: str, package_name: str = None) -> bool:
    """Check if an optional dependency is available."""
    try:
        __import__(module_name)
        print(f"✅ {module_name} is available (optional)")
        return True
    except ImportError:
        package = package_name or module_name
        print(f"⚠️  {module_name} is missing (optional). Install with: pip install {package}")
        return False

def main():
    """Check all dependencies."""
    print("Checking HER framework dependencies...\n")
    
    # Required dependencies
    required_deps = [
        ("numpy", "numpy", "pip install numpy"),
        ("torch", "torch", "pip install torch"),
        ("transformers", "transformers", "pip install transformers"),
    ]
    
    # Optional dependencies
    optional_deps = [
        ("playwright", "playwright", "pip install playwright && python -m playwright install chromium"),
        ("pandas", "pandas", "pip install pandas"),
        ("sklearn", "scikit-learn", "pip install scikit-learn"),
    ]
    
    print("Required Dependencies:")
    print("-" * 30)
    required_ok = True
    for module, package, install_cmd in required_deps:
        if not check_dependency(module, package, install_cmd):
            required_ok = False
    
    print("\nOptional Dependencies:")
    print("-" * 30)
    for module, package, install_cmd in optional_deps:
        check_optional_dependency(module, package)
    
    print("\n" + "=" * 50)
    if required_ok:
        print("🎉 All required dependencies are available!")
        print("HER framework should work correctly.")
    else:
        print("❌ Some required dependencies are missing.")
        print("Please install the missing dependencies before using HER.")
        sys.exit(1)

if __name__ == "__main__":
    main()