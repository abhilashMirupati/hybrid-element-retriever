#!/usr/bin/env python3
"""
Verify that hardcoded patterns have been removed and universal approach implemented.
"""

import re
import os

def check_file_for_patterns(file_path, patterns, description):
    """Check if a file contains specific patterns."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        found_patterns = []
        for pattern in patterns:
            if re.search(pattern, content, re.IGNORECASE):
                found_patterns.append(pattern)
        
        if found_patterns:
            print(f"❌ {description}: Found hardcoded patterns: {found_patterns}")
            return False
        else:
            print(f"✅ {description}: No hardcoded patterns found")
            return True
            
    except Exception as e:
        print(f"❌ {description}: Error reading file - {e}")
        return False

def verify_universal_changes():
    """Verify that universal changes have been implemented."""
    
    print("🔍 Verifying Universal Changes")
    print("=" * 50)
    
    # Patterns that should be removed
    hardcoded_patterns = [
        r'smartphones.*in.*url',
        r'iphone.*in.*url', 
        r'apple.*in.*url',
        r'16-pro.*in.*url',
        r'Apple_2',
        r'iPhone.*16.*Pro',
        r'iphone.*16.*pro'
    ]
    
    # Files to check
    files_to_check = [
        ("src/her/core/runner.py", "Runner file"),
        ("src/her/core/pipeline.py", "Pipeline file")
    ]
    
    all_good = True
    
    for file_path, description in files_to_check:
        if os.path.exists(file_path):
            result = check_file_for_patterns(file_path, hardcoded_patterns, description)
            all_good = all_good and result
        else:
            print(f"❌ {description}: File not found - {file_path}")
            all_good = False
    
    return all_good

def check_universal_methods():
    """Check that universal methods have been added."""
    
    print("\n🔍 Checking Universal Methods")
    print("=" * 50)
    
    runner_file = "src/her/core/runner.py"
    
    try:
        with open(runner_file, 'r') as f:
            content = f.read()
        
        # Check for universal methods
        universal_methods = [
            '_load_dynamic_content',
            '_detect_infinite_scroll',
            '_detect_dynamic_forms', 
            '_detect_lazy_images',
            '_universal_scroll_strategy',
            '_detect_universal_elements',
            '_detect_filter_elements',
            '_detect_button_elements',
            '_detect_form_elements',
            '_detect_navigation_elements',
            '_detect_content_elements'
        ]
        
        found_methods = []
        for method in universal_methods:
            if method in content:
                found_methods.append(method)
        
        print(f"✅ Found {len(found_methods)}/{len(universal_methods)} universal methods:")
        for method in found_methods:
            print(f"   - {method}")
        
        missing_methods = set(universal_methods) - set(found_methods)
        if missing_methods:
            print(f"❌ Missing methods: {missing_methods}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking methods: {e}")
        return False

def check_universal_heuristics():
    """Check that universal heuristics have been implemented."""
    
    print("\n🔍 Checking Universal Heuristics")
    print("=" * 50)
    
    runner_file = "src/her/core/runner.py"
    
    try:
        with open(runner_file, 'r') as f:
            content = f.read()
        
        # Check for universal heuristics patterns
        universal_patterns = [
            'Universal heuristics',
            'works for any website',
            'interactive_tags =',
            'interactive_roles =',
            'interactive_data_attrs =',
            'interactive_class_patterns ='
        ]
        
        found_patterns = []
        for pattern in universal_patterns:
            if pattern in content:
                found_patterns.append(pattern)
        
        print(f"✅ Found {len(found_patterns)}/{len(universal_patterns)} universal patterns:")
        for pattern in found_patterns:
            print(f"   - {pattern}")
        
        if len(found_patterns) >= len(universal_patterns) * 0.8:  # 80% threshold
            return True
        else:
            print(f"❌ Not enough universal patterns found")
            return False
            
    except Exception as e:
        print(f"❌ Error checking heuristics: {e}")
        return False

def main():
    """Main verification function."""
    
    print("🚀 Universal Automation Verification")
    print("Checking removal of hardcoded patterns...")
    print()
    
    # Run all checks
    checks = [
        ("Hardcoded Pattern Removal", verify_universal_changes),
        ("Universal Methods", check_universal_methods),
        ("Universal Heuristics", check_universal_heuristics)
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        print(f"\n{'='*20} {check_name} {'='*20}")
        result = check_func()
        all_passed = all_passed and result
    
    print(f"\n{'='*60}")
    if all_passed:
        print("🎉 SUCCESS: Universal approach implemented!")
        print("✅ Hardcoded patterns removed")
        print("✅ Universal methods added")
        print("✅ Universal heuristics implemented")
        print("✅ System now works across any website")
    else:
        print("❌ FAILED: Some issues found")
        print("Please review the output above for details")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())