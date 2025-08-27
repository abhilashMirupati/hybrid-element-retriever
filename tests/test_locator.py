"""Tests for locator synthesis and verification."""
import pytest
from unittest.mock import Mock, patch

from her.locator.synthesize import LocatorSynthesizer
from her.locator.verify import LocatorVerifier


class TestLocatorSynthesizer:
    """Test locator synthesis."""
    
    def test_init(self):
        """Test initialization."""
        synth = LocatorSynthesizer()
        assert synth.prefer_css == True
        assert synth.max_candidates == 5
    
    def test_synthesize_with_id(self):
        """Test synthesis for element with ID."""
        synth = LocatorSynthesizer()
        
        element = {
            "tag": "button",
            "id": "submit-btn",
            "text": "Submit"
        }
        
        locators = synth.synthesize(element)
        
        assert len(locators) > 0
        assert "#submit-btn" in locators or "button#submit-btn" in locators
    
    def test_synthesize_with_role(self):
        """Test synthesis with accessibility role."""
        synth = LocatorSynthesizer()
        
        element = {
            "tag": "button",
            "role": "button",
            "name": "Submit Form"
        }
        
        locators = synth.synthesize(element)
        
        assert any("role=button" in loc for loc in locators)
        assert any("Submit Form" in loc for loc in locators)
    
    def test_synthesize_css_selectors(self):
        """Test CSS selector synthesis."""
        synth = LocatorSynthesizer()
        
        element = {
            "tag": "input",
            "type": "email",
            "placeholder": "Enter email",
            "classes": ["form-control", "email-input"],
            "data": {"testid": "email-field"}
        }
        
        locators = synth.synthesize(element)
        
        # Should include various CSS selectors
        assert any("input[type=\"email\"]" in loc for loc in locators)
        assert any("placeholder=\"Enter email\"" in loc for loc in locators)
        assert any("data-testid=\"email-field\"" in loc for loc in locators)
    
    def test_synthesize_xpath_selectors(self):
        """Test XPath selector synthesis."""
        synth = LocatorSynthesizer()
        
        element = {
            "tag": "button",
            "text": "Click me",
            "classes": ["btn", "primary"]
        }
        
        locators = synth.synthesize(element)
        
        # Should include XPath selectors
        assert any("//" in loc for loc in locators)
        assert any("Click me" in loc for loc in locators)
    
    def test_is_stable_id(self):
        """Test stable ID detection."""
        synth = LocatorSynthesizer()
        
        # Stable IDs
        assert synth._is_stable_id("submit-button") == True
        assert synth._is_stable_id("user-email") == True
        assert synth._is_stable_id("nav-menu") == True
        
        # Unstable IDs
        assert synth._is_stable_id("a1b2c3d4e5f6") == False  # Hex hash
        assert synth._is_stable_id("ember123") == False  # Ember.js
        assert synth._is_stable_id("react-select-1-option") == False  # React
        assert synth._is_stable_id("__private") == False  # Private
    
    def test_is_meaningful_class(self):
        """Test meaningful class detection."""
        synth = LocatorSynthesizer()
        
        # Meaningful classes
        assert synth._is_meaningful_class("submit-button") == True
        assert synth._is_meaningful_class("user-form") == True
        assert synth._is_meaningful_class("navigation") == True
        
        # Utility classes
        assert synth._is_meaningful_class("mt-4") == False  # Tailwind
        assert synth._is_meaningful_class("text-center") == False  # Tailwind
        assert synth._is_meaningful_class("col-md-6") == False  # Bootstrap
        assert synth._is_meaningful_class("fa-user") == False  # Font Awesome
        assert synth._is_meaningful_class("xs") == False  # Too short
    
    def test_explain_locator(self):
        """Test locator explanation."""
        synth = LocatorSynthesizer()
        
        assert "role" in synth.explain_locator("role=button")
        assert "ID" in synth.explain_locator("#submit")
        assert "text" in synth.explain_locator("text=\"Click\"")
        assert "XPath" in synth.explain_locator("//button")
        assert "CSS" in synth.explain_locator("button.primary")


class TestLocatorVerifier:
    """Test locator verification."""
    
    def test_init(self):
        """Test initialization."""
        verifier = LocatorVerifier()
        assert verifier.timeout_ms == 5000
    
    def test_verify_no_page(self):
        """Test verification without page."""
        verifier = LocatorVerifier()
        
        is_valid, reason, details = verifier.verify("#submit", None)
        assert is_valid == True
        assert "No page available" in reason
    
    @patch('her.locator.verify.PLAYWRIGHT_AVAILABLE', True)
    def test_verify_unique_element(self):
        """Test verification of unique element."""
        verifier = LocatorVerifier()
        
        mock_page = Mock()
        mock_locator = Mock()
        mock_locator.count.return_value = 1
        mock_locator.is_visible.return_value = True
        mock_locator.is_enabled.return_value = True
        
        verifier._string_to_locator = Mock(return_value=mock_locator)
        
        is_valid, reason, details = verifier.verify("#submit", mock_page)
        
        assert is_valid == True
        assert "successfully" in reason
        assert details["count"] == 1
        assert details["visible"] == True
        assert details["enabled"] == True
    
    @patch('her.locator.verify.PLAYWRIGHT_AVAILABLE', True)
    def test_verify_no_elements(self):
        """Test verification when no elements match."""
        verifier = LocatorVerifier()
        
        mock_page = Mock()
        mock_locator = Mock()
        mock_locator.count.return_value = 0
        
        verifier._string_to_locator = Mock(return_value=mock_locator)
        
        is_valid, reason, details = verifier.verify("#nonexistent", mock_page)
        
        assert is_valid == False
        assert "no elements" in reason.lower()
        assert details["count"] == 0
    
    @patch('her.locator.verify.PLAYWRIGHT_AVAILABLE', True)
    def test_verify_multiple_elements(self):
        """Test verification when multiple elements match."""
        verifier = LocatorVerifier()
        
        mock_page = Mock()
        mock_locator = Mock()
        mock_locator.count.return_value = 3
        
        verifier._string_to_locator = Mock(return_value=mock_locator)
        
        is_valid, reason, details = verifier.verify(".button", mock_page)
        
        assert is_valid == False
        assert "3 elements" in reason
        assert "not unique" in reason
        assert details["count"] == 3
    
    @patch('her.locator.verify.PLAYWRIGHT_AVAILABLE', True)
    def test_find_unique_locator(self):
        """Test finding first unique locator."""
        verifier = LocatorVerifier()
        
        mock_page = Mock()
        
        # Mock verify to return False for first, True for second
        verifier.verify = Mock(side_effect=[
            (False, "Not unique", {}),
            (True, "Success", {}),
            (False, "Not found", {})
        ])
        
        locators = ["#id1", "#id2", "#id3"]
        result = verifier.find_unique_locator(locators, mock_page)
        
        assert result == "#id2"
    
    @patch('her.locator.verify.PLAYWRIGHT_AVAILABLE', True)
    def test_string_to_locator_role(self):
        """Test converting role string to locator."""
        verifier = LocatorVerifier()
        
        mock_page = Mock()
        mock_page.get_by_role = Mock()
        
        verifier._string_to_locator("role=button", mock_page)
        mock_page.get_by_role.assert_called_with("button")
        
        verifier._string_to_locator('role=button[name="Submit"]', mock_page)
        mock_page.get_by_role.assert_called_with("button", name="Submit")
    
    @patch('her.locator.verify.PLAYWRIGHT_AVAILABLE', True)
    def test_string_to_locator_text(self):
        """Test converting text string to locator."""
        verifier = LocatorVerifier()
        
        mock_page = Mock()
        mock_page.get_by_text = Mock()
        
        verifier._string_to_locator('text="Click here"', mock_page)
        mock_page.get_by_text.assert_called_with("Click here", exact=True)
    
    @patch('her.locator.verify.PLAYWRIGHT_AVAILABLE', True)
    def test_string_to_locator_xpath(self):
        """Test converting XPath string to locator."""
        verifier = LocatorVerifier()
        
        mock_page = Mock()
        mock_page.locator = Mock()
        
        verifier._string_to_locator("//button[@id='submit']", mock_page)
        mock_page.locator.assert_called_with("xpath=//button[@id='submit']")
    
    @patch('her.locator.verify.PLAYWRIGHT_AVAILABLE', True)
    def test_string_to_locator_css(self):
        """Test converting CSS string to locator."""
        verifier = LocatorVerifier()
        
        mock_page = Mock()
        mock_page.locator = Mock()
        
        verifier._string_to_locator("#submit-btn", mock_page)
        mock_page.locator.assert_called_with("#submit-btn")