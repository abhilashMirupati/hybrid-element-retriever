#!/usr/bin/env python3
"""
Simple test runner for HER feature toggle implementation.

This script runs basic tests to validate the no-semantic mode implementation
without requiring pytest or other external dependencies.
"""

import sys
import os
import traceback
from typing import List, Dict, Any

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

def test_target_matcher():
    """Test target matcher functionality."""
    print("🧪 Testing Target Matcher...")
    
    try:
        from src.her.locator.target_matcher import TargetMatcher, MatchResult
        
        matcher = TargetMatcher(case_sensitive=False)
        
        # Test elements
        elements = [
            {
                'tag': 'button',
                'text': 'Submit Form',
                'attributes': {'id': 'submit-btn'},
                'visible': True
            },
            {
                'tag': 'input',
                'text': '',
                'attributes': {'placeholder': 'Enter your name'},
                'visible': True
            }
        ]
        
        # Test exact match
        matches = matcher.match_elements(elements, 'Submit Form')
        assert len(matches) == 1
        assert matches[0].score == 1.0
        assert matches[0].match_type == 'exact'
        print("  ✅ Exact text matching works")
        
        # Test partial match
        matches = matcher.match_elements(elements, 'Submit')
        assert len(matches) == 1
        assert matches[0].match_type == 'partial'
        print("  ✅ Partial text matching works")
        
        # Test placeholder match
        matches = matcher.match_elements(elements, 'Enter your name')
        assert len(matches) == 1
        assert matches[0].matched_attribute == 'placeholder'
        print("  ✅ Placeholder matching works")
        
        # Test quoted target extraction
        assert matcher.extract_quoted_target('click "Submit"') == 'Submit'
        assert matcher.extract_quoted_target("click 'Cancel'") == 'Cancel'
        print("  ✅ Quoted target extraction works")
        
        print("✅ Target Matcher tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Target Matcher tests failed: {e}")
        traceback.print_exc()
        return False

def test_configuration():
    """Test configuration system."""
    print("🧪 Testing Configuration...")
    
    try:
        from src.her.config.settings import HERConfig
        from src.her.core.config_service import ConfigService
        
        # Test semantic mode
        config_semantic = HERConfig(use_semantic_search=True)
        assert config_semantic.should_use_semantic_search()
        print("  ✅ Semantic mode configuration works")
        
        # Test no-semantic mode
        config_no_semantic = HERConfig(use_semantic_search=False)
        assert not config_no_semantic.should_use_semantic_search()
        print("  ✅ No-semantic mode configuration works")
        
        # Test config service
        service = ConfigService(config_no_semantic)
        assert not service.should_use_semantic_search()
        print("  ✅ Config service works")
        
        print("✅ Configuration tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Configuration tests failed: {e}")
        traceback.print_exc()
        return False

def test_pipeline_branching():
    """Test pipeline branching logic."""
    print("🧪 Testing Pipeline Branching...")
    
    try:
        # Mock the heavy dependencies
        import unittest.mock as mock
        
        with mock.patch('src.her.core.pipeline.preflight_require_models'):
            with mock.patch('src.her.core.pipeline.TextEmbedder'):
                with mock.patch('src.her.core.pipeline.MarkupLMEmbedder'):
                    from src.her.core.pipeline import HybridPipeline
                    
                    # Test that pipeline can be created
                    pipeline = HybridPipeline()
                    assert hasattr(pipeline, 'target_matcher')
                    assert hasattr(pipeline, 'ax_fallback_matcher')
                    print("  ✅ Pipeline initialization works")
                    
                    # Test that no-semantic mode is configured
                    assert hasattr(pipeline, 'use_semantic_search')
                    print("  ✅ Pipeline mode configuration works")
        
        print("✅ Pipeline branching tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Pipeline branching tests failed: {e}")
        traceback.print_exc()
        return False

def test_cli_integration():
    """Test CLI integration."""
    print("🧪 Testing CLI Integration...")
    
    try:
        from src.her.cli.cli_api import HybridElementRetrieverClient
        
        # Test that client can be created with semantic mode
        client = HybridElementRetrieverClient(use_semantic_search=True)
        assert client.use_semantic_search == True
        print("  ✅ Semantic mode client creation works")
        
        # Test that client can be created with no-semantic mode
        client = HybridElementRetrieverClient(use_semantic_search=False)
        assert client.use_semantic_search == False
        print("  ✅ No-semantic mode client creation works")
        
        # Test set_semantic_mode method
        client.set_semantic_mode(True)
        assert client.use_semantic_search == True
        print("  ✅ set_semantic_mode method works")
        
        print("✅ CLI integration tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ CLI integration tests failed: {e}")
        traceback.print_exc()
        return False

def test_accessibility_fallback():
    """Test accessibility fallback functionality."""
    print("🧪 Testing Accessibility Fallback...")
    
    try:
        from src.her.locator.target_matcher import AccessibilityFallbackMatcher
        
        matcher = AccessibilityFallbackMatcher(case_sensitive=False)
        
        # Test accessibility elements
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
        print("  ✅ Accessibility element matching works")
        
        print("✅ Accessibility fallback tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Accessibility fallback tests failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("🚀 Starting HER Feature Toggle Tests")
    print("=" * 60)
    
    tests = [
        test_target_matcher,
        test_configuration,
        test_pipeline_branching,
        test_cli_integration,
        test_accessibility_fallback
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
        print()
    
    print("=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Feature toggle implementation is working.")
        return 0
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return 1

if __name__ == '__main__':
    sys.exit(main())