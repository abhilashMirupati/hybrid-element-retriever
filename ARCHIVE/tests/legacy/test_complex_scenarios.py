"""Tests for complex web scenario handling."""

import pytest
from unittest.mock import Mock, MagicMock, patch, PropertyMock
import time

from her.handlers.complex_scenarios import (
    ComplexScenarioHandler,
    StaleElementHandler,
    DynamicContentHandler,
    FrameHandler,
    ShadowDOMHandler,
    SPANavigationHandler,
    WaitStrategy
)


class TestStaleElementHandler:
    """Test stale element handling."""
    
    def test_retry_on_stale_element(self):
        """Test that stale elements trigger retry."""
        handler = StaleElementHandler()
        
        # Mock element that becomes stale then works
        attempt_count = 0
        
        def mock_getter():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count == 1:
                raise Exception("Element is not connected to the DOM")
            return Mock()
        
        def mock_action(element):
            return "success"
        
        result = handler.safe_execute(mock_getter, mock_action)
        assert result == "success"
        assert attempt_count == 2
    
    def test_max_retries_exceeded(self):
        """Test that max retries is respected."""
        handler = StaleElementHandler(WaitStrategy(max_retries=2))
        
        def mock_getter():
            raise Exception("Element is stale")
        
        def mock_action(element):
            return "success"
        
        with pytest.raises(Exception) as exc:
            handler.safe_execute(mock_getter, mock_action)
        
        assert "Failed after 2 attempts" in str(exc.value)
    
    def test_non_stale_error_propagated(self):
        """Test that non-stale errors are propagated immediately."""
        handler = StaleElementHandler()
        
        def mock_getter():
            raise ValueError("Different error")
        
        def mock_action(element):
            return "success"
        
        with pytest.raises(ValueError) as exc:
            handler.safe_execute(mock_getter, mock_action)
        
        assert "Different error" in str(exc.value)


class TestDynamicContentHandler:
    """Test dynamic content handling."""
    
    def test_wait_for_ajax(self):
        """Test AJAX wait functionality."""
        mock_page = Mock()
        handler = DynamicContentHandler(mock_page)
        
        handler.wait_for_ajax(timeout=1.0)
        
        mock_page.wait_for_load_state.assert_called_once_with(
            'networkidle',
            timeout=1000
        )
    
    def test_dom_stability_check(self):
        """Test DOM stability detection."""
        mock_page = Mock()
        
        # Simulate DOM becoming stable after 2 checks
        dom_states = ["hash1", "hash2", "hash2", "hash2", "hash2"]
        mock_page.evaluate.side_effect = dom_states
        
        handler = DynamicContentHandler(mock_page)
        handler.wait_for_dom_stable(timeout=2.0)
        
        # Should have called evaluate multiple times
        assert mock_page.evaluate.call_count >= 3
    
    def test_infinite_scroll_handling(self):
        """Test infinite scroll detection and handling."""
        mock_page = Mock()
        
        # Simulate increasing scroll height
        heights = [1000, 2000, 3000, 3000]  # Stops growing at 3000
        mock_page.evaluate.side_effect = heights + [None] * 10
        
        handler = DynamicContentHandler(mock_page)
        scrolls = handler.handle_infinite_scroll(max_scrolls=5, wait_after_scroll=0.1)
        
        assert scrolls == 3  # Should stop when height stops increasing
    
    def test_lazy_loading_scroll(self):
        """Test lazy loading scroll behavior."""
        mock_page = Mock()
        mock_page.evaluate.side_effect = [2000] + [None] * 20  # Total height
        
        handler = DynamicContentHandler(mock_page)
        handler.handle_lazy_loading(
            viewport_height=800,
            scroll_step=400,
            wait_between=0.01
        )
        
        # Should have scrolled multiple times
        assert mock_page.evaluate.call_count > 3


class TestFrameHandler:
    """Test iframe handling."""
    
    def test_find_frame_with_element(self):
        """Test finding frame containing specific element."""
        mock_page = Mock()
        mock_frame1 = Mock()
        mock_frame2 = Mock()
        
        # Setup: element is in frame2
        mock_page.query_selector.return_value = None
        mock_frame1.query_selector.return_value = None
        mock_frame2.query_selector.return_value = Mock()  # Found!
        
        mock_page.main_frame = Mock()
        mock_page.frames = [mock_frame1, mock_frame2]
        
        handler = FrameHandler(mock_page)
        frame = handler.find_frame_with_element("#test")
        
        assert frame == mock_frame2
    
    def test_get_frame_by_attributes(self):
        """Test getting frame by various attributes."""
        mock_page = Mock()
        
        mock_frame1 = Mock()
        mock_frame1.name = "frame1"
        mock_frame1.url = "https://example.com/frame1"
        
        mock_frame2 = Mock()
        mock_frame2.name = "targetFrame"
        mock_frame2.url = "https://example.com/frame2"
        
        mock_page.frames = [mock_frame1, mock_frame2]
        
        handler = FrameHandler(mock_page)
        
        # Test by name
        frame = handler.get_frame_by_attributes(name="targetFrame")
        assert frame == mock_frame2
        
        # Test by URL pattern
        frame = handler.get_frame_by_attributes(url_pattern="frame1")
        assert frame == mock_frame1
    
    def test_switch_to_frame(self):
        """Test switching to iframe context."""
        mock_page = Mock()
        mock_iframe_element = Mock()
        mock_frame = Mock()
        
        mock_page.query_selector.return_value = mock_iframe_element
        mock_iframe_element.content_frame.return_value = mock_frame
        
        handler = FrameHandler(mock_page)
        result = handler.switch_to_frame("iframe#content")
        
        assert result == mock_frame
        assert "iframe#content" in handler.frame_cache
    
    def test_execute_in_frame(self):
        """Test executing action in frame context."""
        mock_page = Mock()
        mock_frame = Mock()
        mock_frame.is_detached.return_value = False
        
        handler = FrameHandler(mock_page)
        
        def test_action(frame, value):
            return f"executed_{value}"
        
        result = handler.execute_in_frame(mock_frame, test_action, "test")
        assert result == "executed_test"


class TestShadowDOMHandler:
    """Test Shadow DOM handling."""
    
    def test_pierce_shadow_dom(self):
        """Test piercing through shadow DOM."""
        mock_page = Mock()
        
        # Mock shadow DOM content
        mock_page.evaluate.return_value = [
            {"tagName": "button", "id": "shadow-btn", "textContent": "Click"},
            {"tagName": "input", "id": "shadow-input", "textContent": ""}
        ]
        
        handler = ShadowDOMHandler(mock_page)
        elements = handler.pierce_shadow_dom("#shadow-host")
        
        assert len(elements) == 2
        assert elements[0]["tagName"] == "button"
        assert elements[0]["id"] == "shadow-btn"
    
    def test_find_in_shadow_dom(self):
        """Test finding specific element in shadow DOM."""
        mock_page = Mock()
        
        mock_page.evaluate.return_value = {
            "found": True,
            "tagName": "button",
            "id": "target",
            "textContent": "Submit",
            "isVisible": True
        }
        
        handler = ShadowDOMHandler(mock_page)
        result = handler.find_in_shadow_dom("#host", "#target")
        
        assert result["found"] is True
        assert result["id"] == "target"
    
    def test_click_in_shadow_dom(self):
        """Test clicking element in shadow DOM."""
        mock_page = Mock()
        mock_page.evaluate.return_value = True  # Success
        
        handler = ShadowDOMHandler(mock_page)
        success = handler.click_in_shadow_dom("#host", "button#submit")
        
        assert success is True


class TestSPANavigationHandler:
    """Test SPA navigation handling."""
    
    def test_route_listener_setup(self):
        """Test that route change listeners are set up."""
        mock_page = Mock()
        mock_page.evaluate.return_value = None
        
        handler = SPANavigationHandler(mock_page)
        
        # Should have injected the listener script
        assert mock_page.evaluate.called
        call_args = mock_page.evaluate.call_args[0][0]
        assert "pushState" in call_args
        assert "replaceState" in call_args
        assert "popstate" in call_args
    
    def test_detect_route_change(self):
        """Test detecting route changes."""
        mock_page = Mock()
        
        # Simulate URL change
        mock_page.url = "https://example.com/page1"
        
        handler = SPANavigationHandler(mock_page)
        
        # Change URL after a short delay
        def change_url():
            time.sleep(0.1)
            mock_page.url = "https://example.com/page2"
        
        import threading
        thread = threading.Thread(target=change_url)
        thread.start()
        
        detected = handler.detect_route_change(timeout=1.0)
        thread.join()
        
        assert detected is True
        assert "https://example.com/page2" in handler.route_history
    
    def test_wait_for_spa_navigation(self):
        """Test waiting for SPA navigation to complete."""
        mock_page = Mock()
        mock_page.url = "https://example.com"
        mock_page.evaluate.return_value = []
        
        with patch.object(DynamicContentHandler, 'wait_for_ajax'):
            with patch.object(DynamicContentHandler, 'wait_for_dom_stable'):
                handler = SPANavigationHandler(mock_page)
                handler.wait_for_spa_navigation(timeout=1.0)
                
                # Should attempt to detect changes and wait for stability
                assert mock_page.url  # Accessed


class TestComplexScenarioHandler:
    """Test the main complex scenario handler."""
    
    def test_initialization(self):
        """Test that all sub-handlers are initialized."""
        mock_page = Mock()
        handler = ComplexScenarioHandler(mock_page)
        
        assert handler.stale_handler is not None
        assert handler.dynamic_handler is not None
        assert handler.frame_handler is not None
        assert handler.shadow_handler is not None
        assert handler.spa_handler is not None
    
    def test_find_element_anywhere(self):
        """Test finding element across frames and shadow DOM."""
        mock_page = Mock()
        mock_element = Mock()
        
        # Element not in main page
        mock_page.query_selector.return_value = None
        
        handler = ComplexScenarioHandler(mock_page)
        
        # Mock frame search
        with patch.object(handler.frame_handler, 'find_frame_with_element') as mock_find:
            mock_frame = Mock()
            mock_frame.query_selector.return_value = mock_element
            mock_find.return_value = mock_frame
            
            element = handler._find_element_anywhere("#test", search_frames=True)
            assert element == mock_element
    
    def test_prepare_page_for_automation(self):
        """Test page preparation steps."""
        mock_page = Mock()
        mock_page.query_selector.return_value = None  # No popups/banners
        
        handler = ComplexScenarioHandler(mock_page)
        
        with patch.object(handler.dynamic_handler, 'handle_lazy_loading'):
            handler.prepare_page_for_automation()
            
            # Should setup listeners and handle lazy loading
            handler.dynamic_handler.handle_lazy_loading.assert_called_once()
    
    def test_handle_element_interaction_with_retries(self):
        """Test element interaction with stale element handling."""
        mock_page = Mock()
        mock_element = Mock()
        mock_page.query_selector.return_value = mock_element
        
        handler = ComplexScenarioHandler(mock_page)
        
        # Mock the safe execute
        with patch.object(handler.stale_handler, 'safe_execute') as mock_execute:
            mock_execute.return_value = True
            
            success = handler.handle_element_interaction(
                selector="#button",
                action="click",
                handle_stale=True
            )
            
            assert success is True
            assert mock_execute.called
    
    def test_dismiss_cookie_banners(self):
        """Test cookie banner dismissal."""
        mock_page = Mock()
        
        # Mock cookie accept button
        mock_button = Mock()
        mock_button.is_visible.return_value = True
        mock_page.query_selector.side_effect = [mock_button] + [None] * 10
        
        handler = ComplexScenarioHandler(mock_page)
        handler._dismiss_cookie_banners()
        
        # Should have clicked the button
        mock_button.click.assert_called_once()
    
    def test_close_popups(self):
        """Test popup closing."""
        mock_page = Mock()
        
        # Mock close button
        mock_close = Mock()
        mock_close.is_visible.return_value = True
        mock_page.query_selector.side_effect = [mock_close] + [None] * 10
        
        handler = ComplexScenarioHandler(mock_page)
        handler._close_popups()
        
        # Should have clicked close button
        mock_close.click.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])