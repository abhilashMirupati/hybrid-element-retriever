"""Test frame and shadow DOM handling."""

import pytest
from unittest.mock import Mock, patch
from her.pipeline import HERPipeline, PipelineConfig


class TestFramesShadow:
    """Test nested frames and shadow DOM handling."""
    
    @pytest.fixture
    def pipeline(self):
        """Create pipeline with frame support."""
        config = PipelineConfig(
            handle_frames=True,
            handle_shadow_dom=True
        )
        return HERPipeline(config=config)
    
    def test_nested_iframe_handling(self, pipeline):
        """Test handling of nested iframes."""
        dom_with_frames = {
            "main_frame": {
                "elements": [
                    {"tag": "div", "text": "Main content", "xpath": "//div[1]"}
                ],
                "frames": [
                    {
                        "frame_id": "frame1",
                        "frame_path": ["frame1"],
                        "elements": [
                            {"tag": "button", "text": "Frame button", "xpath": "//button[1]"}
                        ],
                        "frames": [
                            {
                                "frame_id": "frame1_1", 
                                "frame_path": ["frame1", "frame1_1"],
                                "elements": [
                                    {"tag": "input", "text": "", "xpath": "//input[1]"}
                                ]
                            }
                        ]
                    }
                ]
            }
        }
        
        with patch.object(pipeline, '_get_dom_snapshot', return_value=dom_with_frames):
            # Search for element in nested frame
            result = pipeline.process("click frame button", dom_with_frames)
            
            assert result is not None
            assert "used_frame_id" in result
            assert "frame_path" in result
            assert result["used_frame_id"] == "frame1"
            assert result["frame_path"] == ["frame1"]
    
    def test_shadow_dom_traversal(self, pipeline):
        """Test shadow DOM traversal and element location."""
        dom_with_shadow = {
            "elements": [
                {
                    "tag": "custom-element",
                    "shadow_root": True,
                    "shadow_elements": [
                        {"tag": "button", "text": "Shadow button", "xpath": "//button[1]"}
                    ],
                    "xpath": "//custom-element"
                }
            ]
        }
        
        with patch.object(pipeline, '_get_dom_snapshot', return_value=dom_with_shadow):
            result = pipeline.process("click shadow button", dom_with_shadow)
            
            assert result is not None
            assert "in_shadow_dom" in result.get("metadata", {})
            assert result["metadata"]["in_shadow_dom"] is True
    
    def test_frame_xpath_uniqueness(self, pipeline):
        """Test that XPaths are unique within each frame."""
        dom = {
            "main_frame": {
                "elements": [
                    {"tag": "button", "text": "Main Submit", "xpath": "//button[1]"}
                ],
                "frames": [
                    {
                        "frame_id": "frame1",
                        "elements": [
                            # Same XPath but in different frame
                            {"tag": "button", "text": "Frame Submit", "xpath": "//button[1]"}
                        ]
                    }
                ]
            }
        }
        
        # Both buttons have same XPath but in different contexts
        with patch.object(pipeline, '_get_dom_snapshot', return_value=dom):
            # Should find main frame button
            main_result = pipeline.process("click main submit", dom)
            assert main_result["xpath"] == "//button[1]"
            assert main_result.get("used_frame_id") is None or main_result["used_frame_id"] == "main"
            
            # Should find frame button
            frame_result = pipeline.process("click frame submit", dom)
            assert frame_result["xpath"] == "//button[1]"
            assert frame_result["used_frame_id"] == "frame1"
    
    def test_cross_frame_element_search(self, pipeline):
        """Test searching across multiple frames."""
        dom = {
            "main_frame": {
                "elements": [
                    {"tag": "div", "text": "Header", "xpath": "//div[1]"}
                ],
                "frames": [
                    {
                        "frame_id": "nav_frame",
                        "elements": [
                            {"tag": "a", "text": "Home", "xpath": "//a[1]"},
                            {"tag": "a", "text": "About", "xpath": "//a[2]"}
                        ]
                    },
                    {
                        "frame_id": "content_frame",
                        "elements": [
                            {"tag": "h1", "text": "Welcome", "xpath": "//h1[1]"},
                            {"tag": "p", "text": "Content", "xpath": "//p[1]"}
                        ]
                    }
                ]
            }
        }
        
        with patch.object(pipeline, '_get_dom_snapshot', return_value=dom):
            # Should find element in nav_frame
            nav_result = pipeline.process("click about link", dom)
            assert nav_result["used_frame_id"] == "nav_frame"
            assert nav_result["xpath"] == "//a[2]"
            
            # Should find element in content_frame
            content_result = pipeline.process("find welcome heading", dom)
            assert content_result["used_frame_id"] == "content_frame"
            assert content_result["xpath"] == "//h1[1]"
    
    def test_shadow_dom_with_slots(self, pipeline):
        """Test shadow DOM with slot elements."""
        dom = {
            "elements": [
                {
                    "tag": "custom-card",
                    "shadow_root": True,
                    "shadow_elements": [
                        {"tag": "slot", "name": "header", "slotted_content": "Card Title"},
                        {"tag": "slot", "name": "body", "slotted_content": "Card content"},
                        {"tag": "button", "text": "Action", "xpath": "//button[1]"}
                    ],
                    "xpath": "//custom-card"
                }
            ]
        }
        
        with patch.object(pipeline, '_get_dom_snapshot', return_value=dom):
            # Should find slotted content
            result = pipeline.process("find card title", dom)
            assert result is not None
            
            # Should find shadow button
            button_result = pipeline.process("click action button", dom)
            assert button_result is not None
            assert button_result["metadata"].get("in_shadow_dom") is True
    
    def test_frame_navigation_tracking(self, pipeline):
        """Test that frame navigation is tracked."""
        initial_dom = {
            "main_frame": {
                "url": "https://example.com",
                "frames": [
                    {
                        "frame_id": "frame1",
                        "url": "https://example.com/frame1",
                        "elements": []
                    }
                ]
            }
        }
        
        updated_dom = {
            "main_frame": {
                "url": "https://example.com",
                "frames": [
                    {
                        "frame_id": "frame1",
                        "url": "https://example.com/frame2",  # URL changed
                        "elements": []
                    }
                ]
            }
        }
        
        # Detect frame navigation
        assert pipeline._detect_frame_change(initial_dom, updated_dom) is True
    
    def test_mixed_shadow_and_frames(self, pipeline):
        """Test handling both shadow DOM and frames together."""
        complex_dom = {
            "main_frame": {
                "elements": [
                    {
                        "tag": "custom-widget",
                        "shadow_root": True,
                        "shadow_elements": [
                            {"tag": "span", "text": "Shadow text", "xpath": "//span[1]"}
                        ]
                    }
                ],
                "frames": [
                    {
                        "frame_id": "frame1",
                        "elements": [
                            {
                                "tag": "another-widget",
                                "shadow_root": True,
                                "shadow_elements": [
                                    {"tag": "button", "text": "Frame shadow button", "xpath": "//button[1]"}
                                ]
                            }
                        ]
                    }
                ]
            }
        }
        
        with patch.object(pipeline, '_get_dom_snapshot', return_value=complex_dom):
            # Find element in frame's shadow DOM
            result = pipeline.process("click frame shadow button", complex_dom)
            
            assert result is not None
            assert result["used_frame_id"] == "frame1"
            assert result["metadata"].get("in_shadow_dom") is True
            assert result["xpath"] == "//button[1]"