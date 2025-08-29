"""Test wait strategies and overlay handling."""

import time
import pytest
from unittest.mock import Mock, patch, MagicMock
from her.pipeline import HERPipeline, PipelineConfig
from her.resilience import WaitStrategy, ResilienceManager


class TestWaitsOverlays:
    """Test wait strategies and overlay dismissal."""
    
    @pytest.fixture
    def pipeline(self):
        """Create pipeline with resilience features."""
        config = PipelineConfig(
            wait_for_idle=True,
            auto_dismiss_overlays=True,
            handle_popups=True
        )
        return HERPipeline(config=config)
    
    @pytest.fixture
    def resilience_manager(self):
        """Create resilience manager."""
        return ResilienceManager()
    
    def test_wait_for_idle(self, resilience_manager):
        """Test wait_for_idle with readyState and network-idle."""
        # Mock browser state
        browser_state = {
            "readyState": "loading",
            "activeRequests": 5
        }
        
        def update_state():
            # Simulate loading completion
            browser_state["readyState"] = "complete"
            browser_state["activeRequests"] = 0
        
        # Schedule state update
        timer = patch('time.sleep', side_effect=lambda x: update_state() if x > 0 else None)
        
        with timer:
            with patch.object(resilience_manager, '_get_browser_state', return_value=browser_state):
                result = resilience_manager.wait_for_idle(timeout=5)
                assert result is True
                assert browser_state["readyState"] == "complete"
                assert browser_state["activeRequests"] == 0
    
    def test_spinner_detection_and_wait(self, resilience_manager):
        """Test detection and waiting for spinners to disappear."""
        spinner_visible = True
        
        def check_spinner():
            return spinner_visible
        
        def hide_spinner():
            nonlocal spinner_visible
            spinner_visible = False
        
        with patch.object(resilience_manager, '_is_spinner_visible', side_effect=check_spinner):
            with patch('time.sleep', side_effect=lambda x: hide_spinner()):
                result = resilience_manager.wait_for_spinner_gone(timeout=5)
                assert result is True
                assert not spinner_visible
    
    def test_backdrop_overlay_dismissal(self, resilience_manager):
        """Test automatic dismissal of backdrop overlays."""
        overlay_present = True
        
        def check_overlay():
            return overlay_present
        
        def dismiss_overlay():
            nonlocal overlay_present
            overlay_present = False
            return True
        
        with patch.object(resilience_manager, '_detect_overlay', return_value=check_overlay()):
            with patch.object(resilience_manager, '_dismiss_overlay', side_effect=dismiss_overlay):
                result = resilience_manager.handle_overlays()
                assert result is True
                assert not overlay_present
    
    def test_cookie_modal_auto_close(self, resilience_manager):
        """Test automatic cookie consent modal dismissal."""
        cookie_modal = {
            "present": True,
            "buttons": ["Accept All", "Reject All", "Manage Preferences"]
        }
        
        with patch.object(resilience_manager, '_detect_cookie_modal', return_value=cookie_modal):
            with patch.object(resilience_manager, '_click_element') as mock_click:
                resilience_manager.handle_cookie_modal(action="accept")
                mock_click.assert_called_once()
                # Should click "Accept All" or similar
                args = mock_click.call_args[0][0]
                assert "accept" in args.lower() or "allow" in args.lower()
    
    def test_occlusion_guard_via_element_from_point(self, pipeline):
        """Test occlusion detection using elementFromPoint."""
        target_element = {
            "tag": "button",
            "text": "Submit",
            "xpath": "//button[@id='submit']",
            "bounds": {"x": 100, "y": 200, "width": 100, "height": 40}
        }
        
        # Mock elementFromPoint to return different element (occluded)
        occluding_element = {"tag": "div", "class": "modal-overlay"}
        
        with patch.object(pipeline, '_element_from_point', return_value=occluding_element):
            is_occluded = pipeline._is_element_occluded(target_element)
            assert is_occluded is True
        
        # Mock elementFromPoint to return target element (not occluded)
        with patch.object(pipeline, '_element_from_point', return_value=target_element):
            is_occluded = pipeline._is_element_occluded(target_element)
            assert is_occluded is False
    
    def test_wait_strategy_timeout(self, resilience_manager):
        """Test that wait strategies respect timeout."""
        start_time = time.time()
        
        # Mock a condition that never becomes true
        with patch.object(resilience_manager, '_get_browser_state', return_value={"readyState": "loading"}):
            result = resilience_manager.wait_for_idle(timeout=1)
            elapsed = time.time() - start_time
            
            assert result is False  # Should timeout
            assert elapsed >= 0.9  # Should wait close to timeout
            assert elapsed < 2  # But not much longer
    
    def test_multiple_overlay_handling(self, resilience_manager):
        """Test handling multiple overlays in sequence."""
        overlays = ["cookie-banner", "newsletter-popup", "chat-widget"]
        dismissed = []
        
        def dismiss(overlay_type):
            dismissed.append(overlay_type)
            return True
        
        with patch.object(resilience_manager, '_detect_overlays', return_value=overlays):
            with patch.object(resilience_manager, '_dismiss_overlay', side_effect=dismiss):
                resilience_manager.handle_all_overlays()
                
                # All overlays should be dismissed
                assert len(dismissed) == len(overlays)
                assert set(dismissed) == set(overlays)
    
    def test_network_idle_detection(self, resilience_manager):
        """Test network idle detection for SPA loading."""
        requests = [1, 2, 3, 2, 1, 0]  # Simulating request count over time
        request_iter = iter(requests)
        
        def get_active_requests():
            try:
                return next(request_iter)
            except StopIteration:
                return 0
        
        with patch.object(resilience_manager, '_get_active_request_count', side_effect=get_active_requests):
            with patch('time.sleep', return_value=None):
                is_idle = resilience_manager.wait_for_network_idle(threshold=0, timeout=10)
                assert is_idle is True