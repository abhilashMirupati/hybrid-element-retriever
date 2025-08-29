"""Test JSON contract compliance."""

import pytest
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from her.actions import ActionResult, ActionType
from her.locator.enhanced_verify import VerificationResult


class TestJSONContract:
    """Test that JSON output meets strict contract requirements."""
    
    def test_action_result_json_schema(self):
        """Test ActionResult JSON has all required fields."""
        result = ActionResult(
            success=True,
            action_type=ActionType.CLICK,
            selector="button#submit",
            frame_path="iframe[id='form']",
            frame_id="form",
            frame_url="http://example.com/form"
        )
        
        result.waits = {
            "readyState_ok": True,
            "network_idle_ok": True,
            "spinner_cleared": True,
            "overlay_closed": False
        }
        
        result.post_action = {
            "url_changed": True,
            "dom_changed": True,
            "value_set": False,
            "toggled": False
        }
        
        json_dict = result.to_dict()
        
        # Check all required fields exist
        assert "success" in json_dict
        assert "action_type" in json_dict
        assert "selector" in json_dict
        
        # Check frame metadata
        assert "frame" in json_dict
        frame = json_dict["frame"]
        assert "used_frame_id" in frame
        assert "frame_url" in frame
        assert "frame_path" in frame
        
        # Check waits
        assert "waits" in json_dict
        waits = json_dict["waits"]
        assert "readyState_ok" in waits
        assert "network_idle_ok" in waits
        assert "spinner_cleared" in waits
        assert "overlay_closed" in waits
        
        # Check post_action
        assert "post_action" in json_dict
        post = json_dict["post_action"]
        assert "url_changed" in post
        assert "dom_changed" in post
        assert "value_set" in post
        assert "toggled" in post
        
        # Check no None values (should be empty strings)
        assert json_dict["error"] == ""
        assert frame["used_frame_id"] == "form"
        assert frame["frame_url"] == "http://example.com/form"
    
    def test_verification_result_json_schema(self):
        """Test VerificationResult JSON has all required fields."""
        result = VerificationResult(
            success=True,
            selector="button",
            frame_path="main",
            unique_in_frame=True,
            element_count=1,
            strategy_used="semantic"
        )
        
        json_dict = result.to_dict()
        
        # Check all required fields
        assert "success" in json_dict
        assert "selector" in json_dict
        assert "unique_in_frame" in json_dict
        assert "element_count" in json_dict
        assert "strategy_used" in json_dict
        assert "promoted_from" in json_dict
        assert "error" in json_dict
        
        # Check frame metadata
        assert "frame" in json_dict
        frame = json_dict["frame"]
        assert "used_frame_id" in frame
        assert "frame_url" in frame
        assert "frame_path" in frame
        
        # No None values
        assert json_dict["promoted_from"] == ""
        assert json_dict["error"] == ""
        assert frame["used_frame_id"] == ""
        assert frame["frame_url"] == ""
    
    def test_no_empty_required_fields(self):
        """Test that required fields are never None or missing."""
        # Minimal result
        result = ActionResult(
            success=False,
            action_type=ActionType.TYPE,
            selector="input"
        )
        
        json_dict = result.to_dict()
        
        # Even with minimal input, all fields should exist
        assert json_dict["frame"]["frame_path"] == "main"
        assert json_dict["waits"]["readyState_ok"] is False
        assert json_dict["post_action"]["url_changed"] is False
        assert json_dict["error"] == ""
        assert json_dict["strategy_used"] == "primary"
        assert json_dict["duration_ms"] == 0.0
        
        # Verify it's valid JSON
        json_str = json.dumps(json_dict)
        parsed = json.loads(json_str)
        assert parsed == json_dict
    
    def test_deterministic_output(self):
        """Test that output is deterministic."""
        result1 = ActionResult(
            success=True,
            action_type=ActionType.CLICK,
            selector="button"
        )
        
        result2 = ActionResult(
            success=True,
            action_type=ActionType.CLICK,
            selector="button"
        )
        
        # Same input should produce same output
        assert result1.to_dict() == result2.to_dict()
        
        # JSON serialization should be consistent
        json1 = json.dumps(result1.to_dict(), sort_keys=True)
        json2 = json.dumps(result2.to_dict(), sort_keys=True)
        assert json1 == json2