#!/usr/bin/env python3
"""
Demo Verizon Test - Shows XPath selectors used in each step
"""

import os
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set environment variables
os.environ.setdefault('HER_MODELS_DIR', str(project_root / 'src' / 'her' / 'models'))
os.environ.setdefault('HER_CACHE_DIR', str(project_root / '.her_cache'))

def demo_verizon_flow():
    """Demo the Verizon flow and show XPath selectors."""
    print("🚀 DEMO: Verizon Flow with XPath Analysis")
    print("=" * 60)
    
    # Test steps as specified in requirements
    steps = [
        "Open https://www.verizon.com/smartphones/apple/",
        "Click \"iPhone 16 Pro\"",
        "Validate \"Apple iPhone 16 Pro\""
    ]
    
    print("\n📋 Test Steps:")
    for i, step in enumerate(steps, 1):
        print(f"   {i}. {step}")
    
    print("\n🔍 Expected XPath Patterns:")
    print("   Step 1: Navigate to URL (no XPath needed)")
    print("   Step 2: Click action -> Relative XPath starting with //")
    print("   Step 3: Validate action -> Text validation (no XPath needed)")
    
    print("\n📊 Expected XPath Characteristics:")
    print("   ✅ All XPaths start with // (relative)")
    print("   ❌ No XPaths start with /html or /body (absolute)")
    print("   ✅ Prioritizes text content: //button[normalize-space()='iPhone 16 Pro']")
    print("   ✅ Falls back to attributes: //*[@id='...'] or //*[@data-testid='...']")
    print("   ✅ Uses stable selectors: //*[@aria-label='...'] or //*[@class='...']")
    
    print("\n🎯 Sample XPath Examples (Expected):")
    print("   //button[normalize-space()='iPhone 16 Pro']")
    print("   //*[@data-testid='iphone-16-pro-button']")
    print("   //a[contains(@href, 'iphone-16-pro')]")
    print("   //*[@aria-label='iPhone 16 Pro']")
    print("   //button[contains(@class, 'product-button')]")
    
    print("\n⚠️  Invalid XPath Examples (Should NOT be generated):")
    print("   /html/body/div[1]/section[2]/button[3]  (absolute path)")
    print("   /body/div/section/button                (absolute path)")
    print("   /html/body/...                          (absolute path)")
    
    print("\n🔧 XPath Generation Logic:")
    print("   1. Check for unique ID: //*[@id='unique-id']")
    print("   2. Check for data-testid: //*[@data-testid='test-id']")
    print("   3. Check for aria-label: //*[@aria-label='label']")
    print("   4. Check for name attribute: //input[@name='field-name']")
    print("   5. Check for class (first class only): //button[contains(@class, 'btn')]")
    print("   6. Use text content: //button[normalize-space()='Button Text']")
    print("   7. Fallback to tag only: //button")
    
    print("\n🎭 Frame and Shadow DOM Support:")
    print("   ✅ Automatic frame detection and switching")
    print("   ✅ Shadow DOM element location")
    print("   ✅ JavaScript execution in correct context")
    print("   ✅ Enhanced scrolling and off-screen handling")
    
    print("\n📈 Promotion System:")
    print("   ✅ Cold start: First run generates and caches XPath selectors")
    print("   ✅ Warm hit: Subsequent runs reuse cached selectors")
    print("   ✅ Performance: Warm runs should be faster than cold runs")
    print("   ✅ Persistence: Selectors stored in SQLite database")
    
    print("\n" + "=" * 60)
    print("🎯 DEMO COMPLETE - XPath patterns and characteristics shown")
    print("=" * 60)

if __name__ == "__main__":
    demo_verizon_flow()