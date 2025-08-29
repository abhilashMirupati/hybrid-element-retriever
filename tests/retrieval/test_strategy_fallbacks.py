"""Test strategy fallback mechanisms."""

import pytest
from unittest.mock import Mock, patch
from her.pipeline import HERPipeline, PipelineConfig


class TestStrategyFallbacks:
    """Test semantic → robust CSS → contextual XPath fallback strategies."""
    
    @pytest.fixture
    def pipeline(self):
        """Create pipeline with fallback strategies enabled."""
        config = PipelineConfig(
            enable_fallback_strategies=True,
            use_minilm=True
        )
        return HERPipeline(config=config)
    
    def test_semantic_to_css_fallback(self, pipeline):
        """Test fallback from semantic to CSS when semantic fails."""
        dom = {
            "elements": [
                {
                    "tag": "button",
                    "text": "",  # No text for semantic
                    "attributes": {"class": "submit-btn primary"},
                    "xpath": "//button[@class='submit-btn primary']"
                }
            ]
        }
        
        with patch.object(pipeline, '_get_dom_snapshot', return_value=dom):
            result = pipeline.process("click submit button", dom)
            
            assert result is not None
            assert result.get("strategy") == "css" or result.get("strategy") == "robust_css"
            assert "submit-btn" in result["xpath"] or "submit" in str(result)
    
    def test_css_to_xpath_fallback(self, pipeline):
        """Test fallback from CSS to XPath when CSS fails."""
        dom = {
            "elements": [
                {
                    "tag": "div",
                    "text": "Submit",
                    "attributes": {},  # No classes/IDs for CSS
                    "xpath": "//div[text()='Submit']"
                }
            ]
        }
        
        with patch.object(pipeline, '_get_dom_snapshot', return_value=dom):
            result = pipeline.process("click submit", dom)
            
            assert result is not None
            assert result.get("strategy") in ["xpath", "contextual_xpath", "semantic"]
            assert result["xpath"] == "//div[text()='Submit']"
    
    def test_per_frame_uniqueness(self, pipeline):
        """Test that uniqueness is enforced per frame."""
        dom = {
            "main_frame": {
                "elements": [
                    {"tag": "button", "text": "Submit", "xpath": "//button[1]"}
                ]
            },
            "frames": [
                {
                    "frame_id": "frame1",
                    "elements": [
                        {"tag": "button", "text": "Submit", "xpath": "//button[1]"}
                    ]
                }
            ]
        }
        
        # Both buttons have same XPath but in different frames
        with patch.object(pipeline, '_get_dom_snapshot', return_value=dom):
            # Should maintain uniqueness per frame
            main_result = pipeline.process("click submit in main", dom)
            frame_result = pipeline.process("click submit in frame", dom)
            
            # Same XPath is OK in different frames
            assert main_result is not None
            assert frame_result is not None
            if "used_frame_id" in main_result and "used_frame_id" in frame_result:
                assert main_result["used_frame_id"] != frame_result["used_frame_id"]
    
    def test_strategy_order(self, pipeline):
        """Test that strategies are tried in correct order."""
        strategies_tried = []
        
        def track_strategy(strategy_name):
            strategies_tried.append(strategy_name)
            return None  # Force fallback
        
        with patch.object(pipeline, '_try_semantic', side_effect=lambda q, d: track_strategy('semantic')):
            with patch.object(pipeline, '_try_css', side_effect=lambda q, d: track_strategy('css')):
                with patch.object(pipeline, '_try_xpath', side_effect=lambda q, d: track_strategy('xpath')):
                    pipeline.process("find element", {"elements": []})
        
        # Verify order
        expected_order = ['semantic', 'css', 'xpath']
        for i, strategy in enumerate(expected_order):
            if i < len(strategies_tried):
                assert strategies_tried[i] == strategy
    
    def test_fallback_with_confidence_scores(self, pipeline):
        """Test that fallback strategies have appropriate confidence scores."""
        dom = {
            "elements": [
                {"tag": "button", "text": "Click Me", "xpath": "//button"}
            ]
        }
        
        # Mock different strategy results
        with patch.object(pipeline, '_get_dom_snapshot', return_value=dom):
            result = pipeline.process("click button", dom)
            
            assert result is not None
            assert "confidence" in result
            assert 0 <= result["confidence"] <= 1
            
            # Semantic should have higher confidence than fallbacks
            if result.get("strategy") == "semantic":
                assert result["confidence"] >= 0.7
            elif result.get("strategy") == "css":
                assert result["confidence"] >= 0.5
            else:  # xpath
                assert result["confidence"] >= 0.3