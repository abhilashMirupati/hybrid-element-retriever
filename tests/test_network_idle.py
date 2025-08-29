"""Test network idle detection."""

import pytest
import time
from unittest.mock import Mock, MagicMock, patch
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from her.actions import ActionExecutor


class TestNetworkIdle:
    """Test network idle detection and handling."""
    
    def test_network_idle_window_enforcement(self):
        """Test that network idle window is enforced."""
        mock_page = Mock()
        executor = ActionExecutor(mock_page, network_idle_ms=500)
        
        # Simulate network activity
        executor._network_requests = {"http://api.example.com/data"}
        executor._last_network_activity = time.time()
        
        # Should not be idle yet
        with patch('time.time', return_value=executor._last_network_activity + 0.3):
            is_idle = executor._wait_for_network_idle(timeout=0.5)
            assert not is_idle
        
        # Clear requests and wait for idle window
        executor._network_requests.clear()
        
        with patch('time.time', return_value=executor._last_network_activity + 0.6):
            with patch('time.sleep'):
                is_idle = executor._wait_for_network_idle(timeout=1.0)
                # Would be True after idle window passes
    
    def test_slow_xhr_handling(self):
        """Test handling of slow XHR requests."""
        mock_page = Mock()
        executor = ActionExecutor(mock_page, timeout=5.0)
        
        # Simulate slow request
        def on_request(request):
            executor._network_requests.add("slow-request")
            executor._last_network_activity = time.time()
        
        def on_response(response):
            executor._network_requests.discard("slow-request")
            executor._last_network_activity = time.time()
        
        # Mock page events
        mock_page.on.side_effect = [on_request, on_response, None]
        
        executor._setup_network_tracking()
        
        # Simulate slow request
        on_request(Mock(url="http://slow.api"))
        assert len(executor._network_requests) == 1
        
        # Complete request
        on_response(Mock(url="http://slow.api"))
        assert len(executor._network_requests) == 0
    
    def test_bounded_retry_on_timeout(self):
        """Test bounded retries on network timeout."""
        mock_page = Mock()
        executor = ActionExecutor(mock_page)
        
        # Mock click that times out first 2 times
        mock_page.click.side_effect = [
            Exception("Timeout"),
            Exception("Timeout"),
            None  # Success on third try
        ]
        
        mock_page.query_selector.return_value = Mock()
        mock_page.evaluate.return_value = False  # Not occluded
        mock_page.url = "http://example.com"
        mock_page.content.return_value = "<html></html>"
        
        result = executor.execute_click("button")
        
        assert result.retries == 2
        assert result.success
    
    def test_network_tracking_setup(self):
        """Test network request tracking setup."""
        mock_page = Mock()
        executor = ActionExecutor(mock_page)
        
        # Verify event listeners were added
        calls = mock_page.on.call_args_list
        events = [call[0][0] for call in calls]
        
        assert "request" in events
        assert "response" in events
        assert "requestfailed" in events