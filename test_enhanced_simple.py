#!/usr/bin/env python3
"""
Simplified test runner for enhanced HER implementation.

This script tests the enhanced functionality without requiring pytest
or other external dependencies.
"""

import sys
import os
import time
from unittest.mock import Mock, patch

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

def test_enhanced_handlers():
    """Test enhanced handler functionality."""
    print("🧪 Testing Enhanced Handlers...")
    
    try:
        from src.her.locator.frame_handler import FrameHandler, FrameContext, FrameType
        from src.her.locator.shadow_dom_handler import ShadowDOMHandler, ShadowRoot, ShadowDOMType
        from src.her.locator.dynamic_handler import DynamicHandler, DynamicElement, DynamicType
        
        # Test frame handler
        frame_handler = FrameHandler()
        test_elements = [
            {'tag': 'iframe', 'attributes': {'src': 'https://example.com'}, 'xpath': '//iframe'},
            {'tag': 'div', 'text': 'Main content', 'xpath': '//div'}
        ]
        frames = frame_handler.detect_frames(test_elements)
        assert len(frames) >= 2  # Main + iframe
        print("  ✅ Frame handler works correctly")
        
        # Test shadow DOM handler
        shadow_handler = ShadowDOMHandler()
        shadow_elements = [
            {'tag': 'custom-element', 'attributes': {'shadowroot': 'open'}, 'xpath': '//custom-element'},
            {'tag': 'div', 'text': 'Regular content', 'xpath': '//div'}
        ]
        shadow_roots = shadow_handler.detect_shadow_roots(shadow_elements)
        assert len(shadow_roots) >= 1
        print("  ✅ Shadow DOM handler works correctly")
        
        # Test dynamic handler
        dynamic_handler = DynamicHandler()
        dynamic_elements = [
            {'tag': 'div', 'attributes': {'data-ajax': 'true'}, 'xpath': '//div[@data-ajax]'},
            {'tag': 'button', 'attributes': {'data-modal': 'true'}, 'xpath': '//button[@data-modal]'},
            {'tag': 'div', 'text': 'Regular content', 'xpath': '//div'}
        ]
        dynamic_detected = dynamic_handler.detect_dynamic_elements(dynamic_elements)
        assert len(dynamic_detected) >= 1  # At least one should be detected
        print("  ✅ Dynamic handler works correctly")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Enhanced handlers test failed: {e}")
        return False

def test_performance_metrics():
    """Test performance metrics functionality."""
    print("🧪 Testing Performance Metrics...")
    
    try:
        from src.her.monitoring.performance_metrics import PerformanceMetrics, get_metrics
        
        metrics = PerformanceMetrics()
        
        # Test basic metrics recording
        metrics.record_timing("test_operation", 0.5, "semantic")
        metrics.record_timing("test_operation", 0.3, "no-semantic")
        metrics.record_counter("test_counter", 1, "semantic")
        metrics.record_gauge("test_gauge", 100.0, "semantic")
        
        # Test metrics retrieval
        semantic_stats = metrics.get_timing_stats("test_operation", "semantic")
        assert semantic_stats['count'] == 1
        assert semantic_stats['mean'] == 0.5
        
        counter_value = metrics.get_counter_value("test_counter")
        assert counter_value == 1
        
        gauge_value = metrics.get_gauge_value("test_gauge")
        assert gauge_value == 100.0
        
        # Test mode comparison
        comparison = metrics.get_mode_comparison()
        assert "semantic" in comparison
        assert "no-semantic" in comparison
        
        print("  ✅ Performance metrics work correctly")
        return True
        
    except Exception as e:
        print(f"  ❌ Performance metrics test failed: {e}")
        return False

def test_enhanced_target_matcher():
    """Test enhanced target matcher functionality."""
    print("🧪 Testing Enhanced Target Matcher...")
    
    try:
        from src.her.locator.target_matcher import TargetMatcher, MatchResult
        
        matcher = TargetMatcher(case_sensitive=False)
        
        # Test comprehensive element matching
        elements = [
            {
                'tag': 'button',
                'text': 'Submit Form',
                'attributes': {
                    'id': 'submit-btn',
                    'aria-label': 'Submit the form',
                    'data-testid': 'submit-button',
                    'title': 'Click to submit'
                },
                'visible': True
            },
            {
                'tag': 'input',
                'text': '',
                'attributes': {
                    'type': 'text',
                    'placeholder': 'Enter your name',
                    'name': 'username',
                    'value': 'test'
                },
                'visible': True
            }
        ]
        
        # Test basic matching
        matches = matcher.match_elements(elements, 'Submit Form')
        assert len(matches) == 1
        assert matches[0].score == 1.0
        assert matches[0].matched_attribute == 'innerText'
        
        # Test quoted target extraction
        assert matcher.extract_quoted_target('click "Submit"') == 'Submit'
        assert matcher.extract_quoted_target("click 'Cancel'") == 'Cancel'
        assert matcher.extract_quoted_target('click Submit') == 'click Submit'
        
        print("  ✅ Enhanced target matcher works correctly")
        return True
        
    except Exception as e:
        print(f"  ❌ Enhanced target matcher test failed: {e}")
        return False

def test_backward_compatibility():
    """Test backward compatibility."""
    print("🧪 Testing Backward Compatibility...")
    
    try:
        from src.her.config.settings import HERConfig
        from src.her.core.config_service import ConfigService
        from src.her.locator.target_matcher import TargetMatcher
        
        # Test that basic functionality still works
        config = HERConfig()
        assert config.should_use_semantic_search()  # Default should be True
        
        config_no_semantic = HERConfig(use_semantic_search=False)
        assert not config_no_semantic.should_use_semantic_search()
        
        # Test config service
        service = ConfigService(config)
        assert service.should_use_semantic_search()
        
        # Test basic target matching
        matcher = TargetMatcher()
        elements = [{'tag': 'button', 'text': 'Test', 'attributes': {}, 'visible': True}]
        matches = matcher.match_elements(elements, 'Test')
        assert len(matches) == 1
        assert matches[0].score == 1.0
        
        print("  ✅ Backward compatibility maintained")
        return True
        
    except Exception as e:
        print(f"  ❌ Backward compatibility test failed: {e}")
        return False

def test_performance_comparison():
    """Test performance comparison between modes."""
    print("🧪 Testing Performance Comparison...")
    
    try:
        from src.her.monitoring.performance_metrics import PerformanceMetrics
        
        metrics = PerformanceMetrics()
        
        # Simulate performance data for both modes
        for i in range(10):
            # Semantic mode: slower but more accurate
            metrics.record_timing("query_duration", 0.4 + i * 0.02, "semantic")
            metrics.record_timing("memory_usage_mb", 600 + i * 5, "semantic")
            
            # No-semantic mode: faster but less flexible
            metrics.record_timing("query_duration", 0.1 + i * 0.01, "no-semantic")
            metrics.record_timing("memory_usage_mb", 50 + i * 2, "no-semantic")
        
        # Get performance comparison
        comparison = metrics.get_mode_comparison()
        
        # Validate that both modes have data
        assert "semantic" in comparison
        assert "no-semantic" in comparison
        assert "query_duration" in comparison["semantic"]
        assert "query_duration" in comparison["no-semantic"]
        
        # Validate performance characteristics
        semantic_duration = comparison["semantic"]["query_duration"]["mean"]
        no_semantic_duration = comparison["no-semantic"]["query_duration"]["mean"]
        
        # No-semantic should be faster
        assert no_semantic_duration < semantic_duration
        
        print("  ✅ Performance comparison works correctly")
        return True
        
    except Exception as e:
        print(f"  ❌ Performance comparison test failed: {e}")
        return False

def test_error_handling():
    """Test error handling in enhanced features."""
    print("🧪 Testing Error Handling...")
    
    try:
        from src.her.locator.frame_handler import FrameHandler
        from src.her.locator.shadow_dom_handler import ShadowDOMHandler
        from src.her.locator.dynamic_handler import DynamicHandler
        
        # Test frame handler with invalid elements
        frame_handler = FrameHandler()
        invalid_elements = [{'invalid': 'data'}]
        
        # Should not crash
        frames = frame_handler.detect_frames(invalid_elements)
        assert isinstance(frames, list)
        
        # Test shadow DOM handler with invalid elements
        shadow_handler = ShadowDOMHandler()
        shadow_roots = shadow_handler.detect_shadow_roots(invalid_elements)
        assert isinstance(shadow_roots, list)
        
        # Test dynamic handler with invalid elements
        dynamic_handler = DynamicHandler()
        dynamic_elements = dynamic_handler.detect_dynamic_elements(invalid_elements)
        assert isinstance(dynamic_elements, list)
        
        print("  ✅ Error handling works correctly")
        return True
        
    except Exception as e:
        print(f"  ❌ Error handling test failed: {e}")
        return False

def main():
    """Run all enhanced tests."""
    print("🚀 HER Enhanced Implementation Test Suite")
    print("=" * 60)
    
    tests = [
        test_enhanced_handlers,
        test_performance_metrics,
        test_enhanced_target_matcher,
        test_backward_compatibility,
        test_performance_comparison,
        test_error_handling
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
    print(f"📊 Enhanced Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All enhanced tests passed! Implementation is working correctly.")
        return 0
    else:
        print("❌ Some enhanced tests failed. Please check the implementation.")
        return 1

if __name__ == '__main__':
    sys.exit(main())