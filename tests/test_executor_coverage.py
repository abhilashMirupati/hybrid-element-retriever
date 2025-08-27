"""Tests to improve executor coverage."""
from unittest.mock import Mock, patch, MagicMock, PropertyMock
import pytest

from her.executor.actions import ActionExecutor, ActionResult


class TestExecutorCoverage:
    """Test executor for coverage."""
    
    def test_action_result_init(self):
        """Test ActionResult initialization."""
        result = ActionResult()
        assert result.success is False
        assert result.action == ""
        assert result.locator == ""
        assert result.error is None
        assert result.retries == 0
        assert result.duration_ms == 0
        assert result.verification == {}
        assert result.dismissed_overlays == []
        assert result.screenshot is None
    
    def test_action_result_with_values(self):
        """Test ActionResult with values."""
        result = ActionResult(
            success=True,
            action="click",
            locator="button",
            retries=2,
            duration_ms=500
        )
        assert result.success is True
        assert result.action == "click"
        assert result.locator == "button"
        assert result.retries == 2
        assert result.duration_ms == 500
    
    @patch('her.executor.actions.PLAYWRIGHT_AVAILABLE', False)
    def test_executor_no_playwright(self):
        """Test executor when Playwright is not available."""
        executor = ActionExecutor()
        assert executor.playwright is None
        assert executor.browser is None
        assert executor.page is None
    
    @patch('her.executor.actions.PLAYWRIGHT_AVAILABLE', True)
    @patch('her.executor.actions.sync_playwright')
    def test_executor_init_with_playwright(self, mock_sync_playwright):
        """Test executor initialization with Playwright."""
        # Mock playwright
        mock_playwright = Mock()
        mock_sync = Mock()
        mock_sync.start.return_value = mock_playwright
        mock_sync_playwright.return_value = mock_sync
        
        mock_browser = Mock()
        mock_playwright.chromium.launch.return_value = mock_browser
        
        mock_context = Mock()
        mock_browser.new_context.return_value = mock_context
        
        mock_page = Mock()
        mock_context.new_page.return_value = mock_page
        
        executor = ActionExecutor(headless=False, timeout_ms=5000)
        
        assert executor.headless is False
        assert executor.timeout_ms == 5000
        assert executor.page is not None
    
    def test_executor_navigate_no_page(self):
        """Test navigate with no page."""
        executor = ActionExecutor()
        executor.page = None
        result = executor.navigate("http://example.com")
        assert result is False
    
    @patch('her.executor.actions.PLAYWRIGHT_AVAILABLE', True)
    def test_executor_navigate_with_page(self):
        """Test navigate with page."""
        executor = ActionExecutor()
        mock_page = Mock()
        executor.page = mock_page
        
        result = executor.navigate("http://example.com")
        assert result is True
        mock_page.goto.assert_called_once_with("http://example.com", wait_until="domcontentloaded")
    
    def test_executor_execute_no_page(self):
        """Test execute with no page."""
        executor = ActionExecutor()
        executor.page = None
        
        result = executor.execute("click", "button")
        assert result.success is False
        assert result.error == "Page not initialized"
    
    @patch('her.executor.actions.PLAYWRIGHT_AVAILABLE', True)
    def test_executor_wait_for_condition(self):
        """Test wait for condition."""
        executor = ActionExecutor()
        mock_page = Mock()
        executor.page = mock_page
        
        # Test load condition
        result = executor.wait_for_condition("load")
        assert result is True
        mock_page.wait_for_load_state.assert_called_with("load", timeout=executor.timeout_ms)
        
        # Test networkidle condition
        result = executor.wait_for_condition("networkidle", timeout=5000)
        assert result is True
        mock_page.wait_for_load_state.assert_called_with("networkidle", timeout=5000)
        
        # Test selector condition
        result = executor.wait_for_condition("button.submit")
        assert result is True
        mock_page.wait_for_selector.assert_called_with("button.submit", timeout=executor.timeout_ms)
    
    def test_executor_close(self):
        """Test executor close."""
        executor = ActionExecutor()
        
        mock_page = Mock()
        mock_context = Mock()
        mock_browser = Mock()
        mock_playwright = Mock()
        
        executor.page = mock_page
        executor.context = mock_context
        executor.browser = mock_browser
        executor.playwright = mock_playwright
        
        executor.close()
        
        mock_page.close.assert_called_once()
        mock_context.close.assert_called_once()
        mock_browser.close.assert_called_once()
        mock_playwright.stop.assert_called_once()
    
    def test_executor_close_with_errors(self):
        """Test executor close with errors."""
        executor = ActionExecutor()
        
        mock_page = Mock()
        mock_page.close.side_effect = Exception("Page close error")
        
        mock_context = Mock()
        mock_context.close.side_effect = Exception("Context close error")
        
        executor.page = mock_page
        executor.context = mock_context
        
        # Should not raise even with errors
        executor.close()
        
        mock_page.close.assert_called_once()
        mock_context.close.assert_called_once()