"""Tests for descriptors module."""
from her.descriptors import normalize_descriptor


class TestDescriptors:
    """Test descriptor functions."""
    
    def test_normalize_descriptor_basic(self):
        """Test basic descriptor normalization."""
        desc = {
            "tagName": "BUTTON",
            "text": "  Click Me  ",
            "attributes": {
                "id": "btn1",
                "class": "btn primary"
            }
        }
        
        normalized = normalize_descriptor(desc)
        
        assert normalized["tagName"] == "button"
        assert normalized["text"] == "Click Me"
        assert normalized["id"] == "btn1"
        assert normalized["className"] == "btn primary"
    
    def test_normalize_descriptor_with_value(self):
        """Test descriptor with value attribute."""
        desc = {
            "tagName": "INPUT",
            "attributes": {
                "value": "test value",
                "type": "text"
            }
        }
        
        normalized = normalize_descriptor(desc)
        
        assert normalized["tagName"] == "input"
        assert normalized["value"] == "test value"
        assert normalized["type"] == "text"
    
    def test_normalize_descriptor_empty(self):
        """Test empty descriptor."""
        desc = {}
        normalized = normalize_descriptor(desc)
        
        assert normalized["tagName"] == ""
        assert normalized["text"] == ""
        assert normalized.get("id") is None
    
    def test_normalize_descriptor_none_values(self):
        """Test descriptor with None values."""
        desc = {
            "tagName": None,
            "text": None,
            "attributes": None
        }
        
        normalized = normalize_descriptor(desc)
        
        assert normalized["tagName"] == ""
        assert normalized["text"] == ""
    
    def test_normalize_descriptor_nested_attributes(self):
        """Test descriptor with nested attributes."""
        desc = {
            "tagName": "div",
            "attributes": {
                "data-test": "value",
                "aria-label": "Test Label",
                "role": "button"
            }
        }
        
        normalized = normalize_descriptor(desc)
        
        assert normalized["data-test"] == "value"
        assert normalized["aria-label"] == "Test Label"
        assert normalized["role"] == "button"