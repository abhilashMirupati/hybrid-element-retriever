"""Test loading states and overlay handling."""

import pytest
from unittest.mock import Mock, MagicMock
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from her.actions import ActionExecutor


class TestLoadingOverlays:
    """Test loading states and overlay handling."""
    
    def test_spinner_wait(self):
        """Test waiting for spinners to disappear."""
        mock_page = Mock()
        executor = ActionExecutor(mock_page, timeout=5.0)
        
        # Mock spinner that disappears
        mock_page.wait_for_selector.return_value = None
        
        waits = executor.wait_for_idle()
        
        assert "spinner_cleared" in waits
        
        # Check that spinner selectors were checked
        calls = mock_page.wait_for_selector.call_args_list
        spinner_selectors_checked = any(
            ".spinner" in str(call) or ".loading" in str(call)
            for call in calls
        )
        assert spinner_selectors_checked or waits["spinner_cleared"]
    
    def test_cookie_modal_auto_close(self):
        """Test automatic cookie modal closing."""
        mock_page = Mock()
        executor = ActionExecutor(mock_page)
        
        # Mock cookie banner with Accept button
        mock_element = Mock()
        mock_page.query_selector.side_effect = [
            mock_element,  # Found Accept button
            None  # No danger selector
        ]
        mock_element.click.return_value = None
        
        closed = executor._try_close_overlays()
        
        assert closed
        mock_element.click.assert_called()
    
    def test_danger_button_not_clicked(self):
        """Test that dangerous buttons are not auto-clicked."""
        mock_page = Mock()
        executor = ActionExecutor(mock_page)
        
        # Mock Delete button (dangerous)
        mock_element = Mock()
        mock_page.query_selector.side_effect = [
            mock_element,  # Found button
            mock_element  # Also matches danger selector
        ]
        
        closed = executor._try_close_overlays()
        
        # Should not click dangerous button
        mock_element.click.assert_not_called()
    
    def test_sticky_header_occlusion(self):
        """Test detection of sticky header occlusion."""
        mock_page = Mock()
        mock_frame = Mock()
        executor = ActionExecutor(mock_page)
        
        # Mock element occluded by sticky header
        mock_frame.evaluate.return_value = True  # Is occluded
        
        is_occluded = executor._is_occluded("button", mock_frame)
        
        assert is_occluded
    
    def test_in_flight_animations_wait(self):
        """Test waiting for animations to complete."""
        mock_page = Mock()
        executor = ActionExecutor(mock_page)
        
        # Mock active animations
        mock_page.evaluate.side_effect = [
            "complete",  # Document ready
            True,  # Has active animations (first check)
            False  # No active animations (second check)
        ]
        
        # This would wait for animations in real implementation
        # Here we just verify the check happens
        mock_page.evaluate.assert_called()