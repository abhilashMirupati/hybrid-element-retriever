"""
Unit tests for target matcher functionality.

This module tests the target matcher's exact DOM matching capabilities,
including multiple matches, accessibility fallback, and edge cases.
"""

import pytest
from unittest.mock import Mock, patch
from typing import List, Dict, Any

from src.her.locator.target_matcher import TargetMatcher, AccessibilityFallbackMatcher, MatchResult


class TestTargetMatcher:
    """Test target matcher functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.matcher = TargetMatcher(case_sensitive=False)
    
    def test_exact_text_match(self):
        """Test exact text matching."""
        elements = [
            {
                'tag': 'button',
                'text': 'Submit',
                'attributes': {},
                'visible': True
            }
        ]
        
        matches = self.matcher.match_elements(elements, 'Submit')
        assert len(matches) == 1
        assert matches[0].score == 1.0
        assert matches[0].match_type == 'exact'
        assert matches[0].matched_attribute == 'innerText'
    
    def test_aria_label_match(self):
        """Test aria-label matching."""
        elements = [
            {
                'tag': 'button',
                'text': '',
                'attributes': {'aria-label': 'Close dialog'},
                'visible': True
            }
        ]
        
        matches = self.matcher.match_elements(elements, 'Close dialog')
        assert len(matches) == 1
        assert matches[0].matched_attribute == 'aria-label'
        assert matches[0].score == 1.0
    
    def test_placeholder_match(self):
        """Test placeholder matching."""
        elements = [
            {
                'tag': 'input',
                'text': '',
                'attributes': {'placeholder': 'Enter your email'},
                'visible': True
            }
        ]
        
        matches = self.matcher.match_elements(elements, 'Enter your email')
        assert len(matches) == 1
        assert matches[0].matched_attribute == 'placeholder'
    
    def test_id_match(self):
        """Test ID attribute matching."""
        elements = [
            {
                'tag': 'div',
                'text': '',
                'attributes': {'id': 'main-content'},
                'visible': True
            }
        ]
        
        matches = self.matcher.match_elements(elements, 'main-content')
        assert len(matches) == 1
        assert matches[0].matched_attribute == 'id'
    
    def test_partial_match(self):
        """Test partial text matching."""
        elements = [
            {
                'tag': 'button',
                'text': 'Submit Form',
                'attributes': {},
                'visible': True
            }
        ]
        
        matches = self.matcher.match_elements(elements, 'Submit')
        assert len(matches) == 1
        assert matches[0].match_type == 'partial'
        assert matches[0].score < 1.0
        assert matches[0].score > 0.0
    
    def test_word_match(self):
        """Test word-level matching."""
        elements = [
            {
                'tag': 'button',
                'text': 'Save and Continue',
                'attributes': {},
                'visible': True
            }
        ]
        
        matches = self.matcher.match_elements(elements, 'Save Continue')
        assert len(matches) == 1
        assert matches[0].match_type == 'word'
        assert matches[0].score < 1.0
    
    def test_multiple_matches_priority(self):
        """Test that multiple matches are prioritized correctly."""
        elements = [
            {
                'tag': 'button',
                'text': 'Save',
                'attributes': {'id': 'save-btn'},
                'visible': True
            },
            {
                'tag': 'button',
                'text': 'Save Changes',
                'attributes': {'id': 'save-changes-btn'},
                'visible': True
            },
            {
                'tag': 'button',
                'text': 'Save All Files',
                'attributes': {'id': 'save-all-btn'},
                'visible': True
            }
        ]
        
        matches = self.matcher.match_elements(elements, 'Save')
        assert len(matches) == 3
        
        # Exact match should be first
        assert matches[0].score == 1.0
        assert matches[0].matched_value == 'Save'
        
        # Partial matches should follow
        assert matches[1].score < 1.0
        assert matches[2].score < 1.0
    
    def test_hidden_elements_filtered(self):
        """Test that hidden elements are filtered out."""
        elements = [
            {
                'tag': 'button',
                'text': 'Visible',
                'attributes': {},
                'visible': True
            },
            {
                'tag': 'button',
                'text': 'Hidden',
                'attributes': {'style': 'display: none'},
                'visible': False
            },
            {
                'tag': 'button',
                'text': 'Disabled',
                'attributes': {'disabled': 'true'},
                'visible': True
            }
        ]
        
        matches = self.matcher.match_elements(elements, 'Button')
        # Should only find visible, non-disabled elements
        visible_matches = [m for m in matches if m.element['text'] == 'Visible']
        assert len(visible_matches) == 1
    
    def test_case_insensitive_matching(self):
        """Test case-insensitive matching."""
        elements = [
            {
                'tag': 'button',
                'text': 'SUBMIT FORM',
                'attributes': {},
                'visible': True
            }
        ]
        
        matches = self.matcher.match_elements(elements, 'submit form')
        assert len(matches) == 1
        assert matches[0].score == 1.0
    
    def test_case_sensitive_matching(self):
        """Test case-sensitive matching when enabled."""
        matcher = TargetMatcher(case_sensitive=True)
        
        elements = [
            {
                'tag': 'button',
                'text': 'Submit',
                'attributes': {},
                'visible': True
            }
        ]
        
        # Should not match due to case difference
        matches = matcher.match_elements(elements, 'submit')
        assert len(matches) == 0
    
    def test_quoted_target_extraction(self):
        """Test extraction of quoted targets."""
        # Test various quote formats
        assert self.matcher.extract_quoted_target('click "Submit"') == 'Submit'
        assert self.matcher.extract_quoted_target("click 'Cancel'") == 'Cancel'
        assert self.matcher.extract_quoted_target('click `Save`') == 'Save'
        assert self.matcher.extract_quoted_target('click Submit') == 'click Submit'
        assert self.matcher.extract_quoted_target('') is None
        assert self.matcher.extract_quoted_target(None) is None
    
    def test_empty_target_handling(self):
        """Test handling of empty or invalid targets."""
        elements = [
            {
                'tag': 'button',
                'text': 'Submit',
                'attributes': {},
                'visible': True
            }
        ]
        
        # Empty target should return no matches
        matches = self.matcher.match_elements(elements, '')
        assert len(matches) == 0
        
        matches = self.matcher.match_elements(elements, None)
        assert len(matches) == 0
    
    def test_priority_order(self):
        """Test that attributes are matched in priority order."""
        elements = [
            {
                'tag': 'button',
                'text': 'Button Text',
                'attributes': {
                    'id': 'test-id',
                    'aria-label': 'Aria Label',
                    'title': 'Title Text',
                    'placeholder': 'Placeholder Text'
                },
                'visible': True
            }
        ]
        
        # Test that innerText has highest priority
        matches = self.matcher.match_elements(elements, 'Button Text')
        assert len(matches) == 1
        assert matches[0].matched_attribute == 'innerText'
        
        # Test aria-label priority
        matches = self.matcher.match_elements(elements, 'Aria Label')
        assert len(matches) == 1
        assert matches[0].matched_attribute == 'aria-label'
        
        # Test title priority
        matches = self.matcher.match_elements(elements, 'Title Text')
        assert len(matches) == 1
        assert matches[0].matched_attribute == 'title'


class TestAccessibilityFallbackMatcher:
    """Test accessibility fallback matcher."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.matcher = AccessibilityFallbackMatcher(case_sensitive=False)
    
    def test_accessibility_element_matching(self):
        """Test matching accessibility elements."""
        ax_elements = [
            {
                'name': 'Close dialog',
                'role': 'button',
                'element': {'tag': 'button', 'attributes': {'aria-label': 'Close dialog'}}
            },
            {
                'name': 'Open menu',
                'role': 'button',
                'element': {'tag': 'div', 'attributes': {'title': 'Open menu'}}
            }
        ]
        
        matches = self.matcher.match_accessibility_elements(ax_elements, 'Close dialog')
        assert len(matches) == 1
        assert matches[0].matched_value == 'Close dialog'
    
    def test_empty_accessibility_elements(self):
        """Test handling of empty accessibility elements."""
        matches = self.matcher.match_accessibility_elements([], 'test')
        assert len(matches) == 0
        
        matches = self.matcher.match_accessibility_elements(None, 'test')
        assert len(matches) == 0


class TestMatchResult:
    """Test MatchResult data class."""
    
    def test_match_result_creation(self):
        """Test MatchResult creation and properties."""
        element = {'tag': 'button', 'text': 'Test'}
        result = MatchResult(
            element=element,
            score=0.8,
            match_type='partial',
            matched_attribute='innerText',
            matched_value='Test',
            reasons=['partial_innerText_match']
        )
        
        assert result.element == element
        assert result.score == 0.8
        assert result.match_type == 'partial'
        assert result.matched_attribute == 'innerText'
        assert result.matched_value == 'Test'
        assert result.reasons == ['partial_innerText_match']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])