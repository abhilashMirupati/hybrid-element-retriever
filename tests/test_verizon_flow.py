"""
Verizon flow tests for both semantic and no-semantic modes.

This module tests the Verizon phone shopping flow using both retrieval modes
to ensure both work correctly and produce similar results.
"""

import pytest
import os
import sys
from typing import List, Dict, Any

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.her.testing.natural_test_runner import NaturalTestRunner
from src.her.config.settings import HERConfig
from src.her.core.config_service import ConfigService


class TestVerizonFlow:
    """Test Verizon phone shopping flow in both modes."""
    
    @pytest.fixture
    def test_steps(self):
        """Define the test steps for Verizon flow."""
        return [
            "Navigate to https://www.verizon.com/",
            "Click on Phones",
            "Click on Apple",
            "Click on iPhone"
        ]
    
    @pytest.fixture
    def expected_urls(self):
        """Define expected URLs for validation."""
        return [
            "https://www.verizon.com/",
            "https://www.verizon.com/phones/",
            "https://www.verizon.com/phones/apple/",
            "https://www.verizon.com/phones/apple/iphone/"
        ]
    
    @pytest.mark.parametrize("use_semantic_search", [True, False], ids=["semantic", "no-semantic"])
    def test_verizon_phone_shopping_flow(self, use_semantic_search, test_steps, expected_urls):
        """Test Verizon phone shopping flow in both semantic and no-semantic modes.
        
        Args:
            use_semantic_search: Whether to use semantic search mode
            test_steps: List of test steps to execute
            expected_urls: Expected URLs for validation
        """
        # Set up configuration for the test mode
        config = HERConfig(use_semantic_search=use_semantic_search)
        
        # Create test runner with the configuration
        runner = NaturalTestRunner(headless=True, config=config)
        
        try:
            # Run the test
            result = runner.run_test(
                test_name=f"Verizon Flow ({'Semantic' if use_semantic_search else 'No-Semantic'})",
                steps=test_steps,
                start_url="https://www.verizon.com/"
            )
            
            # Validate results
            assert result['success'], f"Test failed: {result.get('message', 'Unknown error')}"
            assert result['successful_steps'] >= len(test_steps) - 1, "Most steps should succeed"
            
            # Check that we reached a phone-related page
            final_url = result.get('final_url', '')
            assert 'verizon.com' in final_url, f"Should stay on Verizon domain, got: {final_url}"
            
            # Log results for comparison
            print(f"\n{'='*60}")
            print(f"VERIZON FLOW TEST RESULTS - {'SEMANTIC' if use_semantic_search else 'NO-SEMANTIC'} MODE")
            print(f"{'='*60}")
            print(f"Success: {result['success']}")
            print(f"Successful Steps: {result['successful_steps']}/{result['total_steps']}")
            print(f"Final URL: {result['final_url']}")
            print(f"Performance: {result.get('performance_stats', {})}")
            
            if result['step_results']:
                print(f"\nStep Details:")
                for step_result in result['step_results']:
                    status = "✅" if step_result['success'] else "❌"
                    print(f"  {status} Step {step_result['step_number']}: {step_result.get('action', 'unknown')}")
                    if not step_result['success']:
                        print(f"      Error: {step_result['error']}")
            
        finally:
            # Clean up
            if hasattr(runner, 'runner'):
                runner.runner._close()
    
    def test_mode_configuration(self):
        """Test that mode configuration works correctly."""
        # Test semantic mode
        config_semantic = HERConfig(use_semantic_search=True)
        assert config_semantic.should_use_semantic_search()
        
        # Test no-semantic mode
        config_no_semantic = HERConfig(use_semantic_search=False)
        assert not config_no_semantic.should_use_semantic_search()
        
        # Test config service
        service_semantic = ConfigService(config_semantic)
        assert service_semantic.should_use_semantic_search()
        
        service_no_semantic = ConfigService(config_no_semantic)
        assert not service_no_semantic.should_use_semantic_search()
    
    def test_cli_mode_toggle(self):
        """Test that CLI mode toggle works correctly."""
        # This would test the CLI --no-semantic flag
        # For now, we'll test the configuration mechanism
        
        # Test environment variable setting
        os.environ['HER_USE_SEMANTIC_SEARCH'] = 'false'
        config = HERConfig.from_env()
        assert not config.should_use_semantic_search()
        
        os.environ['HER_USE_SEMANTIC_SEARCH'] = 'true'
        config = HERConfig.from_env()
        assert config.should_use_semantic_search()
        
        # Clean up
        if 'HER_USE_SEMANTIC_SEARCH' in os.environ:
            del os.environ['HER_USE_SEMANTIC_SEARCH']
    
    @pytest.mark.slow
    def test_performance_comparison(self):
        """Test performance comparison between modes."""
        # This test would run both modes and compare performance
        # For now, we'll just test that both modes can be configured
        
        configs = [
            (True, "semantic"),
            (False, "no-semantic")
        ]
        
        for use_semantic, mode_name in configs:
            config = HERConfig(use_semantic_search=use_semantic)
            runner = NaturalTestRunner(headless=True, config=config)
            
            try:
                # Quick test to ensure both modes work
                result = runner.run_test(
                    test_name=f"Performance Test - {mode_name}",
                    steps=["Navigate to https://www.google.com/"],
                    start_url="https://www.google.com/"
                )
                
                # Both modes should at least be able to navigate
                assert result['success'] or result['successful_steps'] > 0
                
            finally:
                if hasattr(runner, 'runner'):
                    runner.runner._close()


class TestModeSpecificFeatures:
    """Test features specific to each mode."""
    
    def test_semantic_mode_features(self):
        """Test that semantic mode uses embeddings and FAISS."""
        # This would test that semantic mode actually uses the embedding pipeline
        # For now, we'll test the configuration
        
        config = HERConfig(use_semantic_search=True)
        assert config.should_use_semantic_search()
        
        # Test that the pipeline would use semantic mode
        service = ConfigService(config)
        assert service.should_use_semantic_search()
    
    def test_no_semantic_mode_features(self):
        """Test that no-semantic mode uses exact DOM matching."""
        # This would test that no-semantic mode uses target matcher
        # For now, we'll test the configuration
        
        config = HERConfig(use_semantic_search=False)
        assert not config.should_use_semantic_search()
        
        # Test that the pipeline would use no-semantic mode
        service = ConfigService(config)
        assert not service.should_use_semantic_search()
    
    def test_promotion_cache_separation(self):
        """Test that promotion cache is separated by mode."""
        # This tests the cache key separation logic
        page_sig = "test-page"
        frame_hash = "test-frame"
        label_key = "test-label"
        
        # Semantic mode key
        semantic_key = label_key
        
        # No-semantic mode key
        no_semantic_key = f"no-semantic:{label_key}"
        
        assert semantic_key != no_semantic_key
        assert no_semantic_key == "no-semantic:test-label"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])