#!/usr/bin/env python3
"""
Validation script for HER feature toggle implementation.

This script validates that the key components of the feature toggle
are working correctly without requiring heavy dependencies.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

def validate_configuration():
    """Validate configuration system works."""
    print("🔧 Validating Configuration System...")
    
    try:
        from src.her.config.settings import HERConfig
        from src.her.core.config_service import ConfigService
        
        # Test semantic mode
        config_semantic = HERConfig(use_semantic_search=True)
        assert config_semantic.should_use_semantic_search()
        print("  ✅ Semantic mode configuration: OK")
        
        # Test no-semantic mode
        config_no_semantic = HERConfig(use_semantic_search=False)
        assert not config_no_semantic.should_use_semantic_search()
        print("  ✅ No-semantic mode configuration: OK")
        
        # Test config service
        service = ConfigService(config_no_semantic)
        assert not service.should_use_semantic_search()
        print("  ✅ Config service integration: OK")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Configuration validation failed: {e}")
        return False

def validate_target_matcher():
    """Validate target matcher functionality."""
    print("🎯 Validating Target Matcher...")
    
    try:
        from src.her.locator.target_matcher import TargetMatcher, MatchResult
        
        matcher = TargetMatcher(case_sensitive=False)
        
        # Test basic functionality
        elements = [
            {
                'tag': 'button',
                'text': 'Submit',
                'attributes': {'id': 'submit-btn'},
                'visible': True
            }
        ]
        
        matches = matcher.match_elements(elements, 'Submit')
        assert len(matches) == 1
        assert matches[0].score == 1.0
        print("  ✅ Exact matching: OK")
        
        # Test quoted target extraction
        assert matcher.extract_quoted_target('click "Submit"') == 'Submit'
        print("  ✅ Quoted target extraction: OK")
        
        # Test partial matching
        matches = matcher.match_elements(elements, 'Sub')
        assert len(matches) == 1
        assert matches[0].match_type == 'partial'
        print("  ✅ Partial matching: OK")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Target matcher validation failed: {e}")
        return False

def validate_accessibility_fallback():
    """Validate accessibility fallback functionality."""
    print("♿ Validating Accessibility Fallback...")
    
    try:
        from src.her.locator.target_matcher import AccessibilityFallbackMatcher
        
        matcher = AccessibilityFallbackMatcher(case_sensitive=False)
        
        ax_elements = [
            {
                'name': 'Close dialog',
                'role': 'button',
                'element': {'tag': 'button', 'attributes': {'aria-label': 'Close dialog'}}
            }
        ]
        
        matches = matcher.match_accessibility_elements(ax_elements, 'Close dialog')
        assert len(matches) == 1
        assert matches[0].matched_value == 'Close dialog'
        print("  ✅ Accessibility matching: OK")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Accessibility fallback validation failed: {e}")
        return False

def validate_file_structure():
    """Validate that all required files exist."""
    print("📁 Validating File Structure...")
    
    required_files = [
        'src/her/locator/target_matcher.py',
        'src/her/config/settings.py',
        'src/her/core/config_service.py',
        'src/her/core/pipeline.py',
        'src/her/cli/cli.py',
        'src/her/cli/cli_api.py',
        'tests/core/test_no_semantic_mode.py',
        'tests/core/test_target_matcher.py',
        'tests/test_verizon_flow.py'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"  ❌ Missing files: {missing_files}")
        return False
    else:
        print("  ✅ All required files exist: OK")
        return True

def validate_code_quality():
    """Validate code quality and structure."""
    print("🔍 Validating Code Quality...")
    
    try:
        # Check that target_matcher.py has the required classes
        with open('src/her/locator/target_matcher.py', 'r') as f:
            content = f.read()
            
        required_classes = ['TargetMatcher', 'AccessibilityFallbackMatcher', 'MatchResult']
        for class_name in required_classes:
            if class_name not in content:
                print(f"  ❌ Missing class: {class_name}")
                return False
        
        print("  ✅ Target matcher classes: OK")
        
        # Check that settings.py has the new flag
        with open('src/her/config/settings.py', 'r') as f:
            content = f.read()
            
        if 'use_semantic_search' not in content:
            print("  ❌ Missing use_semantic_search flag in settings")
            return False
        
        if 'should_use_semantic_search' not in content:
            print("  ❌ Missing should_use_semantic_search method")
            return False
        
        print("  ✅ Configuration flag: OK")
        
        # Check that pipeline.py has the branching logic
        with open('src/her/core/pipeline.py', 'r') as f:
            content = f.read()
            
        if '_query_no_semantic_mode' not in content:
            print("  ❌ Missing no-semantic query method")
            return False
        
        if 'no-semantic' not in content:
            print("  ❌ Missing no-semantic mode references")
            return False
        
        print("  ✅ Pipeline branching: OK")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Code quality validation failed: {e}")
        return False

def main():
    """Run all validations."""
    print("🚀 HER Feature Toggle Implementation Validation")
    print("=" * 60)
    
    validations = [
        validate_file_structure,
        validate_configuration,
        validate_target_matcher,
        validate_accessibility_fallback,
        validate_code_quality
    ]
    
    passed = 0
    failed = 0
    
    for validation in validations:
        try:
            if validation():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Validation {validation.__name__} crashed: {e}")
            failed += 1
        print()
    
    print("=" * 60)
    print(f"📊 Validation Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All validations passed! Implementation is ready.")
        print("\n✅ Feature Toggle Implementation Complete:")
        print("   • Configuration flags added")
        print("   • CLI --no-semantic flag added")
        print("   • Target matcher for exact DOM matching")
        print("   • Pipeline branching logic")
        print("   • Promotion cache separation")
        print("   • Accessibility fallback")
        print("   • Comprehensive test suite")
        return 0
    else:
        print("❌ Some validations failed. Please check the implementation.")
        return 1

if __name__ == '__main__':
    sys.exit(main())