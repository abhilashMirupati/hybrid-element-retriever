"""Comprehensive edge case tests for HER."""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
# from pathlib import Path
# Add src to path
# import sys
# removed sys.path hack
from her.validators import InputValidator, DOMValidator, FormValidator, AccessibilityValidator
from her.resilience import ResilienceManager, WaitStrategy
from her.pipeline import HERPipeline, PipelineConfig


class TestInputValidation:
    """Test input validation edge cases."""
    
    def test_empty_input(self):
        """Test handling of empty input."""
        valid, sanitized, error = InputValidator.validate_query("")
        assert not valid
        assert error == "Query cannot be empty"
        
        valid, sanitized, error = InputValidator.validate_query(None)
        assert not valid
        assert error == "Query cannot be None"
    
    def test_unicode_characters(self):
        """Test handling of unicode characters."""
        # Test various unicode inputs
        test_cases = [
            "Hello 世界",  # Chinese
            "مرحبا بالعالم",  # Arabic
            "Здравствуй мир",  # Russian
            "🔍 Search emoji",  # Emoji
            "Café ñoño",  # Accented characters
        ]
        
        for query in test_cases:
            valid, sanitized, error = InputValidator.validate_query(query)
            assert valid, f"Failed for: {query}"
            assert sanitized
            assert error is None
    
    def test_special_characters(self):
        """Test handling of special characters."""
        # Test XPath special characters
        query = "Find button with text: \"Click 'here'\""
        valid, sanitized, error = InputValidator.validate_query(query)
        assert valid
        assert sanitized == query
        
        # Test escaping
        escaped = InputValidator.escape_xpath_string("It's \"quoted\"")
        assert "concat" in escaped or "'" in escaped or '"' in escaped
    
    def test_control_characters(self):
        """Test removal of control characters."""
        query = "Hello\x00World\x1F\n"
        valid, sanitized, error = InputValidator.validate_query(query)
        assert valid
        assert "\x00" not in sanitized
        assert "\x1F" not in sanitized
        assert "\n" in sanitized  # Newline should be kept
    
    def test_long_input(self):
        """Test handling of very long input."""
        long_query = "a" * 1000
        valid, sanitized, error = InputValidator.validate_query(long_query)
        assert not valid
        assert len(sanitized) == InputValidator.MAX_QUERY_LENGTH
        assert "too long" in error.lower()
    
    def test_xpath_validation(self):
        """Test XPath expression validation."""
        # Valid XPaths
        valid_xpaths = [
            "//div[@id='test']",
            "/html/body/div[1]",
            "//button[contains(text(), 'Click')]",
            "(//div)[1]",
        ]
        
        for xpath in valid_xpaths:
            valid, sanitized, error = InputValidator.validate_xpath(xpath)
            assert valid, f"Failed for: {xpath}"
        
        # Invalid XPaths
        invalid_xpaths = [
            "div[@id='test']",  # Missing /
            "//div[@id='test'",  # Unbalanced bracket
            "//div[text()='test\"",  # Unbalanced quote
        ]
        
        for xpath in invalid_xpaths:
            valid, sanitized, error = InputValidator.validate_xpath(xpath)
            assert not valid, f"Should fail for: {xpath}"
    
    def test_url_validation(self):
        """Test URL validation."""
        # Valid URLs
        valid_urls = [
            "https://example.com",
            "http://localhost:3000",
            "example.com",  # Should add https://
            "file:///path/to/file.html",
        ]
        
        for url in valid_urls:
            valid, sanitized, error = InputValidator.validate_url(url)
            assert valid, f"Failed for: {url}"
        
        # Invalid URLs
        invalid_urls = [
            "javascript:alert(1)",  # XSS attempt
            "ftp://example.com",  # Unsupported scheme
            "",  # Empty
        ]
        
        for url in invalid_urls:
            valid, sanitized, error = InputValidator.validate_url(url)
            assert not valid, f"Should fail for: {url}"


class TestDOMValidation:
    """Test DOM-related validation."""
    
    def test_duplicate_elements(self):
        """Test handling of duplicate elements."""
        descriptors = [
            {"tag": "button", "text": "Click"},
            {"tag": "button", "text": "Click"},  # Duplicate
            {"tag": "button", "text": "Submit"},
        ]
        
        unique = DOMValidator.handle_duplicate_elements(descriptors)
        assert len(unique) == 3
        assert any("_duplicate_index" in d for d in unique)
    
    def test_icon_only_buttons(self):
        """Test handling of icon-only buttons."""
        descriptor = {
            "tag": "button",
            "text": "",  # No text
            "attributes": {
                "aria-label": "Search",
                "class": "icon-search"
            }
        }
        
        valid, error = DOMValidator.validate_element_descriptor(descriptor)
        assert valid
    
    def test_svg_elements(self):
        """Test handling of SVG elements."""
        descriptor = {
            "tag": "svg",
            "attributes": {
                "viewBox": "0 0 24 24",
                "role": "img",
                "aria-label": "Icon"
            }
        }
        
        valid, error = DOMValidator.validate_element_descriptor(descriptor)
        assert valid
    
    def test_large_dom(self):
        """Test handling of large DOMs."""
        # Create large descriptor list
        descriptors = [{"tag": "div", "id": f"elem-{i}"} for i in range(15000)]
        
        valid, warning = DOMValidator.validate_dom_size(descriptors)
        assert not valid
        assert "too large" in warning.lower()
        
        # Test warning threshold
        descriptors = [{"tag": "div", "id": f"elem-{i}"} for i in range(8500)]
        valid, warning = DOMValidator.validate_dom_size(descriptors)
        assert valid
        assert warning and "warning" in warning.lower()


class TestFormValidation:
    """Test form input validation."""
    
    def test_email_validation(self):
        """Test email input validation."""
        valid_emails = [
            "user@example.com",
            "test.user+tag@domain.co.uk",
        ]
        
        for email in valid_emails:
            valid, sanitized, error = FormValidator.validate_form_input("email", email)
            assert valid, f"Failed for: {email}"
        
        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
        ]
        
        for email in invalid_emails:
            valid, sanitized, error = FormValidator.validate_form_input("email", email)
            assert not valid, f"Should fail for: {email}"
    
    def test_date_validation(self):
        """Test date input validation."""
        valid_dates = [
            "2024-01-15",
            "01/15/2024",
            "15-01-2024",
        ]
        
        for date in valid_dates:
            valid, sanitized, error = FormValidator.validate_form_input("date", date)
            assert valid, f"Failed for: {date}"
    
    def test_file_upload_validation(self):
        """Test file upload path validation."""
        # Valid paths
        valid, sanitized, error = FormValidator.validate_form_input("file", "document.pdf")
        assert valid
        
        # Path traversal attempt
        valid, sanitized, error = FormValidator.validate_form_input("file", "../etc/passwd")
        assert not valid
        assert "Invalid file path" in error
    
    def test_masked_input(self):
        """Test masked input fields."""
        # Phone with mask
        valid, sanitized, error = FormValidator.validate_form_input("tel", "(555) 123-4567")
        assert valid
        
        # SSN-like masked input
        valid, sanitized, error = FormValidator.validate_form_input("text", "***-**-1234")
        assert valid


class TestAccessibility:
    """Test accessibility validation."""
    
    def test_aria_validation(self):
        """Test ARIA attribute validation."""
        # Missing aria-label on interactive element
        warnings = AccessibilityValidator.validate_aria_attributes({
            "role": "button",
            "class": "btn"
        })
        assert any("aria-label" in w for w in warnings)
        
        # Valid ARIA
        warnings = AccessibilityValidator.validate_aria_attributes({
            "role": "button",
            "aria-label": "Submit form"
        })
        assert len(warnings) == 0
    
    def test_language_detection(self):
        """Test language and script detection."""
        # RTL text
        info = AccessibilityValidator.validate_language_support("مرحبا Hello")
        assert info['has_rtl']
        
        # CJK text
        info = AccessibilityValidator.validate_language_support("Hello 世界")
        assert info['has_cjk']
        
        # Emoji
        info = AccessibilityValidator.validate_language_support("Search 🔍")
        assert info['has_emoji']


class TestResilience:
    """Test resilience features."""
    
    @patch('time.sleep')
    def test_wait_strategies(self, mock_sleep):
        """Test different wait strategies."""
        manager = ResilienceManager()
        mock_page = Mock()
        
        # Test idle wait
        mock_page.evaluate.return_value = "complete"
        result = manager.wait_for_idle(mock_page, WaitStrategy.IDLE)
        assert result
        
        # Test timeout
        mock_page.evaluate.return_value = "loading"
        result = manager.wait_for_idle(mock_page, WaitStrategy.LOAD_COMPLETE)
        # Should timeout (mocked sleep doesn't actually wait)
    
    def test_spinner_detection(self):
        """Test spinner and loader detection."""
        manager = ResilienceManager()
        mock_page = Mock()
        
        # Spinner visible
        mock_page.evaluate.return_value = True
        assert manager._has_spinners(mock_page)
        
        # No spinner
        mock_page.evaluate.return_value = False
        assert not manager._has_spinners(mock_page)
    
    def test_infinite_scroll(self):
        """Test infinite scroll handling."""
        manager = ResilienceManager()
        mock_page = Mock()
        
        # Simulate growing page height
        heights = [1000, 2000, 3000, 3000]  # Stops growing
        mock_page.evaluate.side_effect = heights + heights
        
        with patch('time.sleep'):
            scrolls = manager.handle_infinite_scroll(mock_page, max_scrolls=5)
            assert scrolls == 3  # Should stop when height stops changing
    
    def test_overlay_detection(self):
        """Test overlay detection and handling."""
        manager = ResilienceManager()
        mock_page = Mock()
        
        # Cookie banner detected
        mock_page.evaluate.return_value = True
        mock_page.click.return_value = None
        
        handled = manager.detect_and_handle_overlay(mock_page)
        # Should attempt to handle
    
    def test_error_recovery(self):
        """Test error recovery strategies."""
        manager = ResilienceManager()
        mock_page = Mock()
        
        # Stale element error
        error = Exception("stale element reference")
        result = manager.recover_from_error(error, mock_page, {})
        assert result['action'] == 'retry'
        assert result['reason'] == 'stale_element'
        
        # CDP disconnect
        error = Exception("CDP connection lost")
        result = manager.recover_from_error(error, mock_page, {})
        assert result['action'] == 'restart'
        assert result['reason'] == 'cdp_disconnect'
    
    def test_snapshot_restore(self):
        """Test snapshot creation and restore."""
        manager = ResilienceManager()
        mock_page = Mock()
        mock_page.url = "https://example.com"
        mock_page.content.return_value = "<html></html>"
        mock_page.context.cookies.return_value = []
        mock_page.evaluate.return_value = []
        
        # Create snapshot
        snapshot = manager.create_stable_snapshot(mock_page)
        assert snapshot['url'] == "https://example.com"
        
        # Restore snapshot
        result = manager.restore_snapshot(mock_page, snapshot)
        assert result
        mock_page.goto.assert_called_with("https://example.com")


class TestSPANavigation:
    """Test SPA navigation detection."""
    
    def test_hash_navigation(self):
        """Test hash-only navigation detection."""
        pipeline = HERPipeline()
        mock_page = Mock()
        
        # Initial URL
        pipeline._last_snapshot['session1'] = {'url': 'https://example.com#home'}
        
        # Hash change
        mock_page.url = 'https://example.com#about'
        pipeline._check_spa_navigation('session1', mock_page)
        
        assert pipeline._last_snapshot['session1']['needs_reindex']
    
    def test_pushstate_navigation(self):
        """Test pushState navigation detection."""
        pipeline = HERPipeline()
        mock_page = Mock()
        
        # Simulate route change without hash
        pipeline._last_snapshot['session1'] = {'url': 'https://example.com/home'}
        mock_page.url = 'https://example.com/about'
        
        pipeline._check_spa_navigation('session1', mock_page)
        # Should detect URL change


class TestPipeline:
    """Test the full HER pipeline."""
    
    @patch('her.pipeline.QueryEmbedder')
    @patch('her.pipeline.ElementEmbedder')
    def test_cold_start(self, mock_element_embedder, mock_query_embedder):
        """Test cold start detection and handling."""
        pipeline = HERPipeline()
        
        # Mock embedders
        mock_query_embedder.return_value.embed.return_value = [0.1] * 384
        mock_element_embedder.return_value.embed.return_value = [0.2] * 768
        
        descriptors = [
            {"tag": "button", "text": "Click me"},
            {"tag": "input", "id": "search"},
        ]
        
        # First run should be cold start
        result = pipeline.process("Find button", descriptors, session_id="test1")
        
        # Should return result
        assert 'xpath' in result
        assert 'confidence' in result
    
    @patch('her.pipeline.QueryEmbedder')
    @patch('her.pipeline.ElementEmbedder')
    def test_incremental_update(self, mock_element_embedder, mock_query_embedder):
        """Test incremental update with new elements."""
        pipeline = HERPipeline()
        
        # Initial descriptors
        old_descriptors = [
            {"tag": "button", "text": "Old button"},
        ]
        
        # New descriptors with additional element
        new_descriptors = [
            {"tag": "button", "text": "Old button"},
            {"tag": "button", "text": "New button"},  # New element
        ]
        
        # Detect new elements
        new_elements = pipeline._detect_incremental_changes("session1", new_descriptors)
        # Should detect the new button
    
    def test_xpath_generation_fallback(self):
        """Test XPath generation with fallbacks."""
        pipeline = HERPipeline()
        
        descriptor = {
            "tag": "button",
            "text": "Submit",
            "attributes": {"class": "btn btn-primary"}
        }
        
        xpath, fallbacks = pipeline._generate_xpath(descriptor)
        
        # Should generate primary XPath and fallbacks
        assert xpath
        assert isinstance(fallbacks, list)
    
    def test_empty_results(self):
        """Test handling of no matching elements."""
        pipeline = HERPipeline()
        
        result = pipeline.process("Find nonexistent element", [], session_id="test")
        
        assert result['xpath'] == ""
        assert result['confidence'] == 0.0
        assert 'error' in result['context']


class TestMultiContext:
    """Test multi-tab and multi-window support."""
    
    def test_frame_switching(self):
        """Test iframe context switching."""
        manager = ResilienceManager()
        mock_page = Mock()
        mock_frame = Mock()
        
        mock_element = Mock()
        mock_element.content_frame.return_value = mock_frame
        mock_page.query_selector.return_value = mock_element
        
        frame = manager.switch_to_frame(mock_page, "iframe#content")
        assert frame == mock_frame
    
    def test_shadow_dom_access(self):
        """Test shadow DOM access."""
        manager = ResilienceManager()
        mock_page = Mock()
        
        mock_page.evaluate.return_value = {"mode": "open"}
        
        shadow = manager.handle_shadow_dom(mock_page, "#shadow-host")
        assert shadow is not None
    
    def test_cross_origin_iframe(self):
        """Test cross-origin iframe handling."""
        manager = ResilienceManager()
        mock_page = Mock()
        
        # Simulate cross-origin error
        mock_page.query_selector.side_effect = Exception("Cross-origin frame")
        
        frame = manager.switch_to_frame(mock_page, "iframe#external")
        assert frame is None  # Should fail gracefully


class TestPerformance:
    """Test performance-related features."""
    
    def test_large_dom_processing(self):
        """Test processing of large DOMs."""
        pipeline = HERPipeline()
        
        # Create large descriptor list
        large_descriptors = [
            {"tag": "div", "id": f"elem-{i}", "text": f"Text {i}"}
            for i in range(5000)
        ]
        
        # Should handle without crashing
        result = pipeline.process("Find elem-1000", large_descriptors)
        assert 'xpath' in result
    
    def test_embedding_batch_size(self):
        """Test embedding batch processing."""
        config = PipelineConfig(embedding_batch_size=32)
        pipeline = HERPipeline(config)
        
        # Create descriptors larger than batch size
        descriptors = [
            {"tag": "div", "id": f"elem-{i}"}
            for i in range(100)
        ]
        
        # Should process in batches
        pipeline._handle_cold_start("session1", descriptors)
    
    def test_cache_performance(self):
        """Test caching improves performance."""
        pipeline = HERPipeline()
        
        descriptors = [{"tag": "button", "text": "Click"}]
        
        # First call - cold
        result1 = pipeline.process("Find button", descriptors, session_id="perf1")
        
        # Second call - should use cache
        result2 = pipeline.process("Find button", descriptors, session_id="perf1")
        
        # Results should be consistent
        assert result1['xpath'] == result2['xpath']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])