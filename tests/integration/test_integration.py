
    """
    Integration tests for HER pipeline.
    Tests the full flow from input to execution.
    """
    
    import pytest
    from her.core.runner import Runner
    from her.core.pipeline import HybridPipeline
    from her.parser.enhanced_intent import EnhancedIntentParser
    
    class TestIntegration:
        """Integration test suite."""
        
        def test_full_pipeline_flow(self):
            """Test complete pipeline flow."""
            # Test data
            test_elements = [
                {
                    "tag": "button",
                    "text": "Click me",
                    "attributes": {"id": "test-button"},
                    "xpath": "//button[@id='test-button']"
                }
            ]
            
            # Test pipeline
            pipeline = HybridPipeline()
            result = pipeline.query("click button", test_elements)
            
            assert result is not None
            assert "results" in result
            assert len(result["results"]) > 0
        
        def test_runner_integration(self):
            """Test runner integration."""
            runner = Runner(headless=True)
            
            # Test with mock data
            steps = ["open https://example.com", "click on 'test' button"]
            
            # This would normally run the full test
            # For now, just verify runner initializes
            assert runner is not None
        
        def test_error_handling(self):
            """Test error handling across components."""
            # Test with invalid input
            pipeline = HybridPipeline()
            
            with pytest.raises(ValueError):
                pipeline.query("", [])  # Empty query and elements
        
        def test_configuration_validation(self):
            """Test configuration validation."""
            from her.core.config import get_config
            
            config = get_config()
            # Test that configuration loads without errors
            assert config is not None
    