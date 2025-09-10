#!/usr/bin/env python3
"""
Setup Script for English Automation Framework
=============================================

This script sets up all dependencies and validates the framework is ready
for real-world testing.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def check_python_version():
    """Check Python version."""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python {version.major}.{version.minor} is not supported. Need Python 3.8+")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is supported")
    return True

def install_dependencies():
    """Install required dependencies."""
    print("\n📦 Installing dependencies...")
    
    # Install Playwright
    if not run_command("pip install --break-system-packages playwright", "Installing Playwright"):
        return False
    
    # Install Playwright browsers
    if not run_command("python3 -m playwright install chromium", "Installing Chromium browser"):
        return False
    
    # Install other dependencies
    dependencies = [
        "pytest",
        "pytest-timeout",
        "pytest-xdist",
    ]
    
    for dep in dependencies:
        if not run_command(f"pip install --break-system-packages {dep}", f"Installing {dep}"):
            return False
    
    return True

def setup_her_framework():
    """Setup HER framework."""
    print("\n🤖 Setting up HER framework...")
    
    # Check if HER framework exists
    her_path = Path(__file__).parent.parent / "src" / "her"
    if not her_path.exists():
        print("❌ HER framework not found. Please ensure you're in the correct directory.")
        return False
    
    print("✅ HER framework found")
    
    # Check if models are installed
    models_path = Path(__file__).parent.parent / "src" / "her" / "models"
    if not models_path.exists():
        print("⚠️  HER models not found. Installing models...")
        
        # Try to install models
        install_script = Path(__file__).parent.parent / "scripts" / "install_models.sh"
        if install_script.exists():
            if not run_command(f"bash {install_script}", "Installing HER models"):
                print("⚠️  Model installation failed, but continuing...")
        else:
            print("⚠️  Model installation script not found, but continuing...")
    else:
        print("✅ HER models found")
    
    return True

def validate_framework():
    """Validate the framework is working."""
    print("\n🔍 Validating framework...")
    
    try:
        # Test Playwright
        from playwright.sync_api import sync_playwright
        print("✅ Playwright import successful")
        
        # Test HER framework
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
        from her.core.runner import Runner
        print("✅ HER framework import successful")
        
        # Test our automation framework
        from english_automation_framework import EnglishAutomationRunner
        print("✅ English automation framework import successful")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return False

def run_quick_test():
    """Run a quick test to verify everything works."""
    print("\n🧪 Running quick test...")
    
    try:
        from english_automation_framework import run_english_automation
        
        # Simple test steps
        test_steps = [
            "Open https://www.google.com/",
            "Wait 2 seconds"
        ]
        
        print("Running quick test with Google...")
        result = run_english_automation(test_steps, headless=True)
        
        if result.success_rate >= 50:
            print("✅ Quick test passed")
            return True
        else:
            print(f"❌ Quick test failed: {result.success_rate:.1f}% success rate")
            return False
            
    except Exception as e:
        print(f"❌ Quick test failed: {e}")
        return False

def main():
    """Main setup function."""
    print("🚀 Setting up English Automation Framework")
    print("=" * 60)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Dependency installation failed")
        sys.exit(1)
    
    # Setup HER framework
    if not setup_her_framework():
        print("❌ HER framework setup failed")
        sys.exit(1)
    
    # Validate framework
    if not validate_framework():
        print("❌ Framework validation failed")
        sys.exit(1)
    
    # Run quick test
    if not run_quick_test():
        print("❌ Quick test failed")
        sys.exit(1)
    
    print("\n🎉 Setup completed successfully!")
    print("=" * 60)
    print("You can now run the Verizon test with:")
    print("  python run_verizon_test.py")
    print("\nOr run with debug mode:")
    print("  python run_verizon_test.py --debug")
    print("\nOr run in headless mode:")
    print("  python run_verizon_test.py --headless")

if __name__ == "__main__":
    main()