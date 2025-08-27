"""Tests for utils module."""
import pytest
from her.utils import sanitize_text, truncate_text


class TestUtils:
    """Test utility functions."""
    
    def test_sanitize_text_basic(self):
        """Test basic text sanitization."""
        assert sanitize_text("  Hello World  ") == "Hello World"
        assert sanitize_text("Line1\nLine2") == "Line1 Line2"
        assert sanitize_text("Tab\tSeparated") == "Tab Separated"
    
    def test_sanitize_text_multiple_spaces(self):
        """Test sanitization of multiple spaces."""
        assert sanitize_text("Multiple   Spaces") == "Multiple Spaces"
        assert sanitize_text("  Leading and trailing  ") == "Leading and trailing"
    
    def test_sanitize_text_empty(self):
        """Test sanitization of empty text."""
        assert sanitize_text("") == ""
        assert sanitize_text("   ") == ""
        assert sanitize_text(None) == ""
    
    def test_truncate_text_basic(self):
        """Test basic text truncation."""
        assert truncate_text("Short", 10) == "Short"
        assert truncate_text("This is a long text", 10) == "This is a..."
    
    def test_truncate_text_exact_length(self):
        """Test truncation at exact length."""
        assert truncate_text("Exactly 10", 10) == "Exactly 10"
        assert truncate_text("Exactly 11!", 10) == "Exactly..."
    
    def test_truncate_text_empty(self):
        """Test truncation of empty text."""
        assert truncate_text("", 10) == ""
        assert truncate_text(None, 10) == ""
    
    def test_truncate_text_short_max_length(self):
        """Test truncation with very short max length."""
        assert truncate_text("Hello", 3) == "..."
        assert truncate_text("Hi", 3) == "Hi"