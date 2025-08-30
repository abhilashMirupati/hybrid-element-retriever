"""Test frame and shadow DOM handling."""

import pytest
from unittest.mock import Mock, MagicMock, patch
# import sys
# from pathlib import Path
# removed sys.path hack
from her.session.snapshot import SnapshotManager, FrameSnapshot
from her.locator.enhanced_verify import EnhancedVerifier
from her.actions import ActionExecutor


class TestFramesAndShadow:
    """Test frame and shadow DOM edge cases."""
    
    def test_nested_iframes(self):
        """Test handling of nested iframes."""
        snapshot_mgr = SnapshotManager()
        
        # Mock page with nested iframes
        mock_page = Mock()
        mock_page.url = "http://example.com"
        
        # Main frame elements
        mock_page.evaluate.return_value = [
            {"tag": "div", "id": "main-content", "text": "Main"},
            {"tag": "iframe", "id": "frame1"}
        ]
        
        # Mock iframe hierarchy
        mock_iframe1 = Mock()
        mock_iframe1.get_attribute.side_effect = lambda x: "frame1" if x == "id" else None
        
        mock_frame1 = Mock()
        mock_frame1.url = "http://example.com/frame1"
        mock_frame1.evaluate.return_value = [
            {"tag": "div", "id": "frame1-content", "text": "Frame 1"},
            {"tag": "iframe", "id": "frame2"}
        ]
        
        mock_iframe2 = Mock()
        mock_iframe2.get_attribute.side_effect = lambda x: "frame2" if x == "id" else None
        
        mock_frame2 = Mock()
        mock_frame2.url = "http://example.com/frame2"
        mock_frame2.evaluate.return_value = [
            {"tag": "button", "id": "nested-button", "text": "Click me"}
        ]
        
        mock_iframe1.content_frame.return_value = mock_frame1
        mock_iframe2.content_frame.return_value = mock_frame2
        
        mock_page.query_selector_all.return_value = [mock_iframe1]
        mock_frame1.query_selector_all.return_value = [mock_iframe2]
        
        snapshot, _ = snapshot_mgr.capture_snapshot(
            mock_page,
            "test_session",
            include_frames=True
        )
        
        # Should have main frame and child frames
        assert snapshot.main_frame is not None
        assert len(snapshot.child_frames) > 0
    
    def test_shadow_dom_penetration(self):
        """Test shadow DOM penetration."""
        snapshot_mgr = SnapshotManager()
        
        # Mock page with shadow DOM
        mock_page = Mock()
        mock_page.url = "http://example.com"
        
        # JavaScript that would extract shadow DOM
        mock_page.evaluate.return_value = [
            {"tag": "div", "id": "host", "text": ""},
            {"tag": "button", "text": "Shadow Button", "path": "::shadow"}
        ]
        
        snapshot, _ = snapshot_mgr.capture_snapshot(
            mock_page,
            "test_session",
            include_shadow=True
        )
        
        elements = snapshot.get_all_elements()
        
        # Should have shadow DOM elements
        shadow_elements = [e for e in elements if "::shadow" in e.get("path", "")]
        assert len(shadow_elements) > 0
    
    def test_cross_origin_guard(self):
        """Test cross-origin iframe handling."""
        snapshot_mgr = SnapshotManager()
        
        # Mock page with cross-origin iframe
        mock_page = Mock()
        mock_page.url = "http://example.com"
        mock_page.evaluate.side_effect = [
            # Window origin
            "http://example.com",
            # Main frame elements
            [{"tag": "div", "id": "main"}]
        ]
        
        mock_iframe = Mock()
        mock_iframe.get_attribute.side_effect = lambda x: {
            "id": "external-frame",
            "src": "http://different-origin.com/page"
        }.get(x)
        
        mock_page.query_selector_all.return_value = [mock_iframe]
        
        # Cross-origin frame should fail to get content
        mock_iframe.content_frame.side_effect = Exception("Cross-origin")
        
        snapshot, _ = snapshot_mgr.capture_snapshot(
            mock_page,
            "test_session",
            include_frames=True
        )
        
        # Should skip cross-origin frames without crashing
        assert snapshot.main_frame is not None
        # Cross-origin frame should not be in child_frames
        assert all(
            "different-origin" not in (f.frame_url or "")
            for f in snapshot.child_frames
        )
    
    def test_frame_path_in_results(self):
        """Test that frame path is included in verification results."""
        verifier = EnhancedVerifier()
        
        # Mock frame
        mock_frame = Mock()
        mock_frame.query_selector.return_value = Mock()
        mock_frame.query_selector_all.return_value = [Mock()]
        mock_frame.evaluate.return_value = "button"
        mock_frame.url = "http://example.com/frame"
        
        descriptor = {"tag": "button", "text": "Submit"}
        
        result = verifier.verify_with_healing(
            "button",
            descriptor,
            mock_frame,
            frame_path="iframe[id='form-frame']"
        )
        
        # Should include frame metadata
        assert result.frame_path == "iframe[id='form-frame']"
        result_dict = result.to_dict()
        assert "frame" in result_dict
        assert result_dict["frame"]["frame_path"] == "iframe[id='form-frame']"
    
    def test_frame_switching_in_actions(self):
        """Test frame switching during action execution."""
        mock_page = Mock()
        executor = ActionExecutor(mock_page)
        
        # Mock frame hierarchy
        mock_iframe = Mock()
        mock_frame = Mock()
        mock_iframe.content_frame.return_value = mock_frame
        
        mock_page.query_selector.return_value = mock_iframe
        mock_frame.click.return_value = None
        mock_frame.url = "http://example.com/frame"
        mock_frame.evaluate.return_value = ""
        
        # Execute click in frame
        result = executor.execute_click(
            "button",
            frame_path="iframe[id='payment']"
        )
        
        # Should have attempted frame switch
        mock_page.query_selector.assert_called()
        assert result.frame_path == "iframe[id='payment']"
    
    def test_shadow_dom_selector_generation(self):
        """Test selector generation for shadow DOM elements."""
        synthesizer = LocatorSynthesizer()
        
        descriptor = {
            "tag": "button",
            "text": "Shadow Button",
            "path": "::shadow",
            "attributes": {
                "slot": "actions"
            }
        }
        
        # Note: Real shadow DOM selectors would need special handling
        # This tests that we at least generate something
        locators = synthesizer.synthesize(descriptor)
        assert len(locators) > 0
    
    def test_per_frame_uniqueness(self):
        """Test that uniqueness is verified per frame."""
        verifier = EnhancedVerifier()
        
        # Mock page with button in main and iframe
        mock_page = Mock()
        mock_iframe = Mock()
        mock_frame = Mock()
        
        # Main frame has 1 button
        mock_page.query_selector_all.side_effect = [
            [Mock()],  # 1 button in main
            [mock_iframe]  # 1 iframe
        ]
        
        # Frame has 1 button (same selector)
        mock_frame.query_selector_all.return_value = [Mock()]  # 1 button in frame
        
        mock_iframe.content_frame.return_value = mock_frame
        mock_iframe.get_attribute.return_value = "iframe1"
        mock_frame.url = "http://example.com/frame"
        
        results = verifier.verify_uniqueness_per_frame(
            "button[type='submit']",
            mock_page,
            include_frames=True
        )
        
        # Both frames should show unique
        assert results["main"].unique_in_frame
        assert results["main"].element_count == 1
        
        # Frame result would be checked if mock was complete
        frame_keys = [k for k in results.keys() if k != "main"]
        for frame_key in frame_keys:
            assert results[frame_key].element_count == 1