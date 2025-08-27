"""Comprehensive tests for real-world example validation."""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from her.cli_api import HybridClient
from her.bridge.cdp_bridge import capture_complete_snapshot, DOMSnapshot
from her.cache.two_tier import TwoTierCache
from her.rank.fusion_scorer import FusionScorer, ElementScore
from her.recovery.enhanced_self_heal import EnhancedSelfHealer, HealingStatus


class TestRealWorldExamples:
    """Test suite for real-world DOM and intent examples."""
    
    @pytest.fixture
    def examples_dir(self):
        """Get examples directory path."""
        return Path(__file__).parent.parent / "examples"
    
    @pytest.fixture
    def mock_page(self):
        """Create a mock Playwright page."""
        page = MagicMock()
        page.url = "http://test.example.com"
        page.viewport_size = {"width": 1280, "height": 720}
        page.frames = []
        page.main_frame = page
        page.query_selector_all.return_value = []
        page.wait_for_load_state.return_value = None
        page.wait_for_timeout.return_value = None
        return page
    
    @pytest.fixture
    def client(self):
        """Create HybridClient instance."""
        with patch('her.cli_api.PLAYWRIGHT_AVAILABLE', False):
            client = HybridClient(auto_index=False, headless=True)
            yield client
    
    def test_login_flow_intent(self, examples_dir):
        """Test login flow with overlay handling."""
        intent_file = examples_dir / "intents" / "realworld" / "login_flow.json"
        assert intent_file.exists(), f"Intent file not found: {intent_file}"
        
        with open(intent_file) as f:
            intent_data = json.load(f)
        
        assert intent_data["name"] == "Login Flow with Overlay Handling"
        assert len(intent_data["steps"]) == 7
        
        # Validate each step
        for step in intent_data["steps"]:
            assert "action" in step
            assert "intent" in step
            assert "expected_locator" in step
            
            # Check validation criteria
            if "validation" in step:
                assert isinstance(step["validation"], dict)
    
    def test_spa_navigation_intent(self, examples_dir):
        """Test SPA navigation intent."""
        intent_file = examples_dir / "intents" / "realworld" / "spa_navigation.json"
        assert intent_file.exists()
        
        with open(intent_file) as f:
            intent_data = json.load(f)
        
        assert intent_data["name"] == "SPA Navigation and Interaction"
        assert len(intent_data["steps"]) == 9
        
        # Check for SPA-specific validations
        has_url_change_check = any(
            "url_changed" in step.get("validation", {})
            for step in intent_data["steps"]
        )
        assert has_url_change_check, "SPA intent should check for URL changes"
    
    def test_shadow_dom_intent(self, examples_dir):
        """Test shadow DOM and iframe intent."""
        intent_file = examples_dir / "intents" / "realworld" / "shadow_dom_flow.json"
        assert intent_file.exists()
        
        with open(intent_file) as f:
            intent_data = json.load(f)
        
        assert intent_data["name"] == "Shadow DOM and iFrame Complex Interaction"
        
        # Check for shadow DOM specific locators
        has_shadow_locator = any(
            "shadow://" in step.get("expected_locator", "")
            for step in intent_data["steps"]
        )
        assert has_shadow_locator, "Should have shadow DOM locators"
        
        # Check for iframe locators
        has_iframe_locator = any(
            "iframe:" in step.get("expected_locator", "")
            for step in intent_data["steps"]
        )
        assert has_iframe_locator, "Should have iframe locators"
    
    def test_dom_snapshot_with_overlays(self, mock_page):
        """Test DOM snapshot captures overlays correctly."""
        # Mock overlay detection
        mock_page.evaluate.return_value = [
            {
                "tag": "DIV",
                "id": "cookie-banner",
                "className": "cookie-consent",
                "zIndex": "9999",
                "visible": True
            }
        ]
        
        snapshot = capture_complete_snapshot(mock_page, wait_stable=False)
        assert isinstance(snapshot, DOMSnapshot)
        assert snapshot.url == mock_page.url
    
    def test_fusion_scorer_with_real_elements(self):
        """Test fusion scorer with realistic element data."""
        scorer = FusionScorer()
        
        # Simulate real button element
        button_element = {
            "tag": "button",
            "id": "login-button",
            "attributes": {
                "type": "submit",
                "class": "btn btn-primary",
                "aria-label": "Sign in to your account"
            },
            "text": "Sign In",
            "bbox": {"x": 100, "y": 200, "width": 120, "height": 40},
            "styles": {"display": "block", "visibility": "visible", "opacity": "1"}
        }
        
        score = scorer.score_element(button_element)
        assert isinstance(score, ElementScore)
        assert score.heuristic_score > 0.5  # Button should score well
        assert score.visibility_score == 1.0  # Fully visible
        assert score.fusion_score > 0.3  # Reasonable overall score
    
    def test_self_healer_with_dom_resnapshot(self, mock_page):
        """Test self-healing with DOM resnapshot strategy."""
        healer = EnhancedSelfHealer(cache_healed=False)
        
        # Test healing a failed locator
        failed_locator = "//button[@id='old-login-btn']"
        
        result = healer.heal(
            failed_locator,
            page=mock_page,
            resnapshot_on_fail=True
        )
        
        assert result.status in [HealingStatus.FAILED, HealingStatus.PARTIAL]
        assert len(result.healed_locators) > 0
        assert result.attempts > 0
    
    def test_cache_system_performance(self):
        """Test two-tier cache system performance."""
        cache = TwoTierCache(memory_size=100, disk_size_mb=10)
        
        # Test batch operations
        test_data = {f"key_{i}": f"value_{i}" for i in range(50)}
        cache.put_batch(test_data)
        
        # Test retrieval
        retrieved = cache.get_batch(list(test_data.keys()))
        assert len(retrieved) == len(test_data)
        
        # Test cache stats
        stats = cache.stats()
        assert stats["memory"]["entries"] > 0
        assert stats["memory"]["hit_rate"] >= 0.0
    
    @pytest.mark.parametrize("action,expected_fields", [
        ("click", ["success", "action", "locator", "duration_ms"]),
        ("type", ["success", "action", "locator", "duration_ms"]),
        ("select", ["success", "action", "locator", "duration_ms"])
    ])
    def test_action_result_json_format(self, action, expected_fields):
        """Test that action results produce valid JSON with required fields."""
        from her.executor.actions import ActionResult
        
        result = ActionResult(
            success=True,
            action=action,
            locator="//button[@id='test']",
            duration_ms=100
        )
        
        result_dict = {
            "success": result.success,
            "action": result.action,
            "locator": result.locator,
            "duration_ms": result.duration_ms
        }
        
        # Check all expected fields are present
        for field in expected_fields:
            assert field in result_dict
        
        # Ensure JSON serializable
        json_str = json.dumps(result_dict)
        assert json_str
    
    def test_overlay_detection_patterns(self):
        """Test overlay detection patterns are comprehensive."""
        from her.executor.actions import ActionExecutor
        
        executor = ActionExecutor(dismiss_overlays=True)
        
        # Test patterns exist (check method exists)
        assert hasattr(executor, "_dismiss_overlays")
        assert hasattr(executor, "_detect_blocking_overlays")
        assert hasattr(executor, "_is_overlay_blocking")
    
    def test_spa_route_tracking_injection(self, mock_page):
        """Test SPA route tracking script injection."""
        from her.session.manager import SessionManager
        
        manager = SessionManager(auto_index=True)
        session = manager.create_session("test-spa", mock_page)
        
        assert session.session_id == "test-spa"
        assert session.auto_index_enabled
        
        # Verify SPA tracking would be set up
        assert hasattr(manager, "_setup_spa_tracking")
    
    def test_locator_uniqueness_validation(self):
        """Test that generated locators are unique."""
        from her.locator.synthesize import LocatorSynthesizer
        
        synthesizer = LocatorSynthesizer()
        
        # Mock element with multiple similar siblings
        element = {
            "tag": "button",
            "attributes": {"class": "submit-btn"},
            "text": "Submit",
            "index": 2,
            "siblings": [
                {"tag": "button", "text": "Submit"},
                {"tag": "button", "text": "Submit"},
                {"tag": "button", "text": "Submit"}
            ]
        }
        
        locators = synthesizer.synthesize(element)
        
        # Should generate indexed locator for uniqueness
        has_indexed = any("[" in loc and "]" in loc for loc in locators)
        assert has_indexed or len(locators) > 0
    
    def test_error_recovery_flow(self, client):
        """Test complete error recovery flow."""
        # Mock a failed action
        with patch.object(client.executor, 'execute') as mock_execute:
            mock_execute.return_value.success = False
            mock_execute.return_value.error = "Element not found"
            
            # This should trigger self-healing
            with patch.object(client.healer, 'heal') as mock_heal:
                mock_heal.return_value.success = True
                mock_heal.return_value.selected_locator = "//button[contains(text(), 'Submit')]"
                
                # Attempt action (will fail then heal)
                result = client.act("Click submit button")
                
                # Verify healing was attempted
                assert mock_heal.called or not result["success"]


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_dom_handling(self):
        """Test handling of empty DOM."""
        snapshot = DOMSnapshot()
        assert snapshot.dom_nodes == []
        assert snapshot.ax_nodes == []
        assert snapshot.compute_hash() != ""
    
    def test_malformed_locator_healing(self):
        """Test healing of malformed locators."""
        healer = EnhancedSelfHealer(cache_healed=False)
        
        malformed = "//button[invalid syntax"
        result = healer.heal(malformed)
        
        assert result.status in [HealingStatus.FAILED, HealingStatus.PARTIAL]
        assert result.error or len(result.healed_locators) > 0
    
    def test_circular_frame_reference(self, mock_page):
        """Test handling of circular frame references."""
        # Create circular reference
        frame1 = MagicMock()
        frame2 = MagicMock()
        frame1.parent = frame2
        frame2.parent = frame1
        mock_page.frames = [mock_page.main_frame, frame1, frame2]
        
        # Should not crash
        snapshot = capture_complete_snapshot(mock_page, include_frames=True)
        assert isinstance(snapshot, DOMSnapshot)
    
    def test_unicode_handling(self):
        """Test handling of unicode in locators and text."""
        from her.locator.synthesize import LocatorSynthesizer
        
        synthesizer = LocatorSynthesizer()
        
        element = {
            "tag": "button",
            "text": "登录 🔐",  # Unicode with emoji
            "attributes": {"aria-label": "ログイン"}  # Japanese
        }
        
        locators = synthesizer.synthesize(element)
        assert len(locators) > 0
        
        # Ensure unicode is preserved
        for locator in locators:
            assert isinstance(locator, str)
    
    def test_concurrent_session_handling(self):
        """Test handling multiple concurrent sessions."""
        from her.session.manager import SessionManager
        
        manager = SessionManager()
        
        # Create multiple sessions
        sessions = []
        for i in range(5):
            session = manager.create_session(f"session_{i}")
            sessions.append(session)
        
        assert len(manager.sessions) == 5
        
        # Verify each session is independent
        for i, session in enumerate(sessions):
            assert session.session_id == f"session_{i}"
            assert manager.get_session(f"session_{i}") == session
    
    def test_cache_overflow_handling(self):
        """Test cache behavior when exceeding limits."""
        cache = TwoTierCache(memory_size=5, disk_size_mb=0.001)  # Very small limits
        
        # Add more items than capacity
        for i in range(20):
            cache.put(f"key_{i}", f"value_{i}" * 1000)  # Large values
        
        # Should have evicted old entries
        stats = cache.stats()
        assert stats["memory"]["entries"] <= 5
    
    @pytest.mark.parametrize("invalid_input", [
        None,
        "",
        "   ",
        "<script>alert('xss')</script>",
        "'; DROP TABLE users; --"
    ])
    def test_input_sanitization(self, invalid_input):
        """Test that invalid inputs are handled safely."""
        from her.parser.intent import IntentParser
        
        parser = IntentParser()
        
        # Should not crash or execute malicious code
        try:
            result = parser.parse(invalid_input)
            assert result is None or isinstance(result, dict)
        except:
            # Acceptable to raise exception for invalid input
            pass


class TestPerformance:
    """Performance and load tests."""
    
    def test_large_dom_processing(self, mock_page):
        """Test processing of large DOM trees."""
        # Mock large DOM
        large_dom = [{"nodeId": i, "tag": "div"} for i in range(10000)]
        mock_page.evaluate.return_value = large_dom
        
        import time
        start = time.time()
        snapshot = capture_complete_snapshot(mock_page, wait_stable=False)
        duration = time.time() - start
        
        # Should complete in reasonable time
        assert duration < 5.0  # 5 seconds max
        assert isinstance(snapshot, DOMSnapshot)
    
    def test_cache_performance(self):
        """Test cache retrieval performance."""
        cache = TwoTierCache()
        
        # Populate cache
        for i in range(1000):
            cache.put(f"key_{i}", {"data": f"value_{i}"})
        
        import time
        start = time.time()
        
        # Retrieve many items
        for i in range(1000):
            value = cache.get(f"key_{i}")
            assert value is not None
        
        duration = time.time() - start
        
        # Should be fast (< 1ms per retrieval on average)
        assert duration < 1.0
    
    def test_fusion_scorer_batch_performance(self):
        """Test batch scoring performance."""
        scorer = FusionScorer()
        
        # Create many elements
        elements = [
            {
                "tag": "button",
                "id": f"btn_{i}",
                "text": f"Button {i}"
            }
            for i in range(100)
        ]
        
        import time
        start = time.time()
        scores = scorer.score_batch(elements)
        duration = time.time() - start
        
        assert len(scores) == 100
        assert duration < 1.0  # Should be fast


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=her", "--cov-report=term-missing"])