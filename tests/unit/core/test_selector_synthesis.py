"""Test selector synthesis functionality."""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from her.locator.synthesize import synthesize_xpath, LocatorSynthesizer


class TestSelectorSynthesis:
    """Test selector synthesis functionality."""
    
    def test_data_testid_priority(self):
        """Test that data-testid gets highest priority."""
        desc = {
            "tag": "button",
            "text": "Click me",
            "attributes": {
                "data-testid": "submit-btn",
                "id": "btn1",
                "class": "btn-primary"
            }
        }
        
        selectors = synthesize_xpath(desc)
        
        assert len(selectors) > 0, "Should generate selectors"
        assert selectors[0][0] == "data-testid", "First selector should be data-testid"
        assert selectors[0][1] == '//*[@data-testid="submit-btn"]', "Should generate correct XPath"
    
    def test_data_quick_link_priority(self):
        """Test that data-quick-link gets high priority."""
        desc = {
            "tag": "a",
            "text": "Phones",
            "attributes": {
                "data-quick-link": "phones",
                "href": "/phones",
                "class": "nav-link"
            }
        }
        
        selectors = synthesize_xpath(desc)
        
        assert len(selectors) > 0, "Should generate selectors"
        # Should have data-quick-link with text
        data_quick_link_found = any(
            kind == "data-quick-link" and 'normalize-space()="Phones"' in xpath
            for kind, xpath in selectors
        )
        assert data_quick_link_found, "Should generate data-quick-link selector with text"
    
    def test_href_text_priority(self):
        """Test that href+text gets high priority for links."""
        desc = {
            "tag": "a",
            "text": "Learn More",
            "attributes": {
                "href": "/learn-more",
                "class": "link"
            }
        }
        
        selectors = synthesize_xpath(desc)
        
        assert len(selectors) > 0, "Should generate selectors"
        # Should have href+text
        href_text_found = any(
            kind == "href+text" and 'href="/learn-more"' in xpath and 'normalize-space()="Learn More"' in xpath
            for kind, xpath in selectors
        )
        assert href_text_found, "Should generate href+text selector"
    
    def test_aria_label_priority(self):
        """Test that aria-label gets medium priority."""
        desc = {
            "tag": "button",
            "text": "Close",
            "attributes": {
                "aria-label": "Close dialog",
                "class": "close-btn"
            }
        }
        
        selectors = synthesize_xpath(desc)
        
        assert len(selectors) > 0, "Should generate selectors"
        # Should have aria-label
        aria_found = any(
            kind == "aria-label" and 'aria-label="Close dialog"' in xpath
            for kind, xpath in selectors
        )
        assert aria_found, "Should generate aria-label selector"
    
    def test_id_text_priority(self):
        """Test that id+text gets medium priority."""
        desc = {
            "tag": "input",
            "text": "",
            "attributes": {
                "id": "username",
                "type": "text"
            }
        }
        
        selectors = synthesize_xpath(desc)
        
        assert len(selectors) > 0, "Should generate selectors"
        # Should have id
        id_found = any(
            kind == "id" and 'id="username"' in xpath
            for kind, xpath in selectors
        )
        assert id_found, "Should generate id selector"
    
    def test_id_text_combination(self):
        """Test that id+text gets higher priority than just id."""
        desc = {
            "tag": "button",
            "text": "Submit",
            "attributes": {
                "id": "submit-btn",
                "class": "btn"
            }
        }
        
        selectors = synthesize_xpath(desc)
        
        assert len(selectors) > 0, "Should generate selectors"
        
        # Find id+text and id selectors
        id_text_found = any(kind == "id+text" for kind, xpath in selectors)
        id_found = any(kind == "id" for kind, xpath in selectors)
        
        assert id_text_found, "Should generate id+text selector"
        assert id_found, "Should generate id selector"
        
        # id+text should come before id
        id_text_idx = next(i for i, (kind, _) in enumerate(selectors) if kind == "id+text")
        id_idx = next(i for i, (kind, _) in enumerate(selectors) if kind == "id")
        assert id_text_idx < id_idx, "id+text should come before id"
    
    def test_class_text_priority(self):
        """Test that class+text gets medium priority."""
        desc = {
            "tag": "div",
            "text": "Click here",
            "attributes": {
                "class": "clickable-tile",
                "role": "button"
            }
        }
        
        selectors = synthesize_xpath(desc)
        
        assert len(selectors) > 0, "Should generate selectors"
        # Should have class+text
        class_text_found = any(
            kind == "class+text" and 'contains(@class, "clickable-tile")' in xpath and 'normalize-space()="Click here"' in xpath
            for kind, xpath in selectors
        )
        assert class_text_found, "Should generate class+text selector"
    
    def test_id_class_text_combination(self):
        """Test that id+class+text gets high priority."""
        desc = {
            "tag": "button",
            "text": "Filter",
            "attributes": {
                "id": "filter-btn",
                "class": "btn btn-primary",
                "data-testid": "filter"
            }
        }
        
        selectors = synthesize_xpath(desc)
        
        assert len(selectors) > 0, "Should generate selectors"
        
        # Should have id+class+text
        id_class_text_found = any(
            kind == "id+class+text" and 'id="filter-btn"' in xpath and 'contains(@class, "btn")' in xpath and 'normalize-space()="Filter"' in xpath
            for kind, xpath in selectors
        )
        assert id_class_text_found, "Should generate id+class+text selector"
    
    def test_role_text_priority(self):
        """Test that role+text gets lower priority."""
        desc = {
            "tag": "div",
            "text": "Menu",
            "attributes": {
                "role": "button",
                "class": "menu-item"
            }
        }
        
        selectors = synthesize_xpath(desc)
        
        assert len(selectors) > 0, "Should generate selectors"
        # Should have role+text
        role_text_found = any(
            kind == "role+name" and 'role="button"' in xpath and 'normalize-space()="Menu"' in xpath
            for kind, xpath in selectors
        )
        assert role_text_found, "Should generate role+text selector"
    
    def test_text_fallbacks(self):
        """Test text-based fallback selectors."""
        desc = {
            "tag": "button",
            "text": "Click me",
            "attributes": {
                "class": "btn"
            }
        }
        
        selectors = synthesize_xpath(desc)
        
        assert len(selectors) > 0, "Should generate selectors"
        
        # Should have text-exact
        text_exact_found = any(
            kind == "text-exact" and 'normalize-space()="Click me"' in xpath
            for kind, xpath in selectors
        )
        assert text_exact_found, "Should generate text-exact selector"
        
        # Should have text-contains
        text_contains_found = any(
            kind == "text-contains" and 'contains(normalize-space(), "Click me")' in xpath
            for kind, xpath in selectors
        )
        assert text_contains_found, "Should generate text-contains selector"
    
    def test_selector_precedence_order(self):
        """Test that selectors are generated in correct precedence order."""
        desc = {
            "tag": "button",
            "text": "Submit",
            "attributes": {
                "data-testid": "submit-btn",
                "data-quick-link": "submit",
                "href": "/submit",
                "aria-label": "Submit form",
                "id": "submit-btn",
                "class": "btn-primary",
                "role": "button"
            }
        }
        
        selectors = synthesize_xpath(desc)
        
        assert len(selectors) > 0, "Should generate selectors"
        
        # Check precedence order
        expected_order = [
            "data-testid",
            "data-quick-link", 
            "href+text",
            "aria-label",
            "id+text",
            "id",
            "class+text",
            "id+class+text",
            "role+name",
            "text-exact",
            "text-contains"
        ]
        
        # Find actual order
        actual_order = [kind for kind, _ in selectors]
        
        # Check that each expected kind appears in the right relative order
        for i, expected_kind in enumerate(expected_order):
            if expected_kind in actual_order:
                expected_idx = actual_order.index(expected_kind)
                # All previous expected kinds should appear before this one
                for prev_kind in expected_order[:i]:
                    if prev_kind in actual_order:
                        prev_idx = actual_order.index(prev_kind)
                        assert prev_idx < expected_idx, f"{prev_kind} should come before {expected_kind}"
    
    def test_locator_synthesizer_class(self):
        """Test LocatorSynthesizer class wrapper."""
        synthesizer = LocatorSynthesizer()
        
        desc = {
            "tag": "button",
            "text": "Click me",
            "attributes": {
                "data-testid": "click-btn",
                "id": "btn1"
            }
        }
        
        selectors = synthesizer.synthesize(desc)
        
        assert len(selectors) > 0, "Should generate selectors"
        assert all("kind" in sel and "selector" in sel for sel in selectors), "Should have kind and selector keys"
        
        # Check first selector
        first_sel = selectors[0]
        assert first_sel["kind"] == "data-testid", "First should be data-testid"
        assert first_sel["selector"] == '//*[@data-testid="click-btn"]', "Should have correct XPath"
    
    def test_empty_attributes(self):
        """Test handling of empty or missing attributes."""
        desc = {
            "tag": "div",
            "text": "Some text",
            "attributes": {}
        }
        
        selectors = synthesize_xpath(desc)
        
        assert len(selectors) > 0, "Should generate selectors"
        # Should fall back to text-based selectors
        text_selectors = [kind for kind, _ in selectors if kind in ["text-exact", "text-contains"]]
        assert len(text_selectors) > 0, "Should have text-based fallbacks"
    
    def test_missing_text(self):
        """Test handling of missing text."""
        desc = {
            "tag": "button",
            "text": "",
            "attributes": {
                "id": "btn1",
                "class": "btn"
            }
        }
        
        selectors = synthesize_xpath(desc)
        
        assert len(selectors) > 0, "Should generate selectors"
        # Should have id and class selectors
        id_found = any(kind == "id" for kind, _ in selectors)
        class_found = any(kind == "class+text" for kind, _ in selectors)
        
        assert id_found, "Should have id selector"
        # class+text should not be present since text is empty
        assert not class_found, "Should not have class+text without text"
    
    def test_special_characters_in_text(self):
        """Test handling of special characters in text."""
        desc = {
            "tag": "button",
            "text": "Click & Submit",
            "attributes": {
                "id": "btn1"
            }
        }
        
        selectors = synthesize_xpath(desc)
        
        assert len(selectors) > 0, "Should generate selectors"
        # Should have text selectors with properly escaped text
        text_exact_found = any(
            kind == "text-exact" and 'normalize-space()="Click & Submit"' in xpath
            for kind, xpath in selectors
        )
        assert text_exact_found, "Should handle special characters in text"
    
    def test_case_sensitivity(self):
        """Test that selectors are case-sensitive where appropriate."""
        desc = {
            "tag": "Button",  # Capital B
            "text": "Click Me",  # Mixed case
            "attributes": {
                "data-testid": "Submit-Btn",  # Mixed case
                "id": "submitBtn"  # camelCase
            }
        }
        
        selectors = synthesize_xpath(desc)
        
        assert len(selectors) > 0, "Should generate selectors"
        
        # Check that case is preserved in selectors
        data_testid_sel = next((xpath for kind, xpath in selectors if kind == "data-testid"), None)
        assert data_testid_sel is not None, "Should have data-testid selector"
        assert 'data-testid="Submit-Btn"' in data_testid_sel, "Should preserve case in data-testid"
        
        id_sel = next((xpath for kind, xpath in selectors if kind == "id"), None)
        assert id_sel is not None, "Should have id selector"
        assert 'id="submitBtn"' in id_sel, "Should preserve case in id"