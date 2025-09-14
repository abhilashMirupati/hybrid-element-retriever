#!/usr/bin/env python3
"""
Minimal test to verify HER functionality without browser dependencies.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.her.core.pipeline import HybridPipeline
from src.her.config.settings import HERConfig

def test_pipeline_initialization():
    """Test that the pipeline can be initialized."""
    print("🧪 Testing Pipeline Initialization...")
    
    try:
        # Test semantic mode
        print("  Testing semantic mode...")
        os.environ['HER_USE_SEMANTIC_SEARCH'] = 'true'
        pipeline_semantic = HybridPipeline(models_root="src/her/models")
        print("  ✅ Semantic pipeline initialized")
        
        # Test no-semantic mode
        print("  Testing no-semantic mode...")
        os.environ['HER_USE_SEMANTIC_SEARCH'] = 'false'
        pipeline_no_semantic = HybridPipeline(models_root="src/her/models")
        print("  ✅ No-semantic pipeline initialized")
        
        return True
    except Exception as e:
        print(f"  ❌ Pipeline initialization failed: {e}")
        return False

def test_query_semantic():
    """Test semantic query."""
    print("\n🧪 Testing Semantic Query...")
    
    try:
        os.environ['HER_USE_SEMANTIC_SEARCH'] = 'true'
        pipeline = HybridPipeline(models_root="src/her/models")
        
        # Mock elements
        elements = [
            {
                'tag': 'button',
                'text': 'Click me',
                'attributes': {'id': 'test-button', 'class': 'btn'},
                'visible': True,
                'interactive': True,
                'meta': {'frame_hash': 'main'}
            },
            {
                'tag': 'div',
                'text': 'Some content',
                'attributes': {'class': 'content'},
                'visible': True,
                'interactive': False,
                'meta': {'frame_hash': 'main'}
            }
        ]
        
        result = pipeline.query("click button", elements, top_k=3)
        print(f"  ✅ Semantic query result: {result}")
        return True
    except Exception as e:
        print(f"  ❌ Semantic query failed: {e}")
        return False

def test_query_no_semantic():
    """Test no-semantic query."""
    print("\n🧪 Testing No-Semantic Query...")
    
    try:
        os.environ['HER_USE_SEMANTIC_SEARCH'] = 'false'
        pipeline = HybridPipeline(models_root="src/her/models")
        
        # Mock elements
        elements = [
            {
                'tag': 'button',
                'text': 'Click me',
                'attributes': {'id': 'test-button', 'class': 'btn'},
                'visible': True,
                'interactive': True,
                'meta': {'frame_hash': 'main'}
            },
            {
                'tag': 'div',
                'text': 'Some content',
                'attributes': {'class': 'content'},
                'visible': True,
                'interactive': False,
                'meta': {'frame_hash': 'main'}
            }
        ]
        
        result = pipeline.query("click button", elements, top_k=3)
        print(f"  ✅ No-semantic query result: {result}")
        return True
    except Exception as e:
        print(f"  ❌ No-semantic query failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🎯 HER Minimal Test Suite")
    print("=" * 50)
    
    tests = [
        test_pipeline_initialization,
        test_query_semantic,
        test_query_no_semantic
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())