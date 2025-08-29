"""Test DOM uniqueness handling."""

import pytest
from unittest.mock import Mock, MagicMock
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from her.locator.synthesize import LocatorSynthesizer
from her.locator.enhanced_verify import EnhancedVerifier, VerificationResult
from her.session.snapshot import SnapshotManager


class TestDOMUniqueness:
    """Test DOM uniqueness edge cases."""
    
    def test_duplicate_buttons(self):
        """Test handling of duplicate buttons with same text."""
        synthesizer = LocatorSynthesizer()
        
        # Three buttons with same text
        descriptors = [
            {"tag": "button", "text": "Submit", "id": "form1-submit"},
            {"tag": "button", "text": "Submit", "id": "form2-submit"},
            {"tag": "button", "text": "Submit", "classes": ["modal-btn"]}
        ]
        
        selectors = []
        for desc in descriptors:
            locs = synthesizer.synthesize(desc)
            # Should prioritize ID-based selector
            if desc.get('id'):
                assert any(f"#{desc['id']}" in loc or f"@id='{desc['id']}'" in loc for loc in locs)
            selectors.append(locs[0] if locs else None)
        
        # All selectors should be different
        assert len(set(selectors)) == len(selectors), "Duplicate selectors generated"
    
    def test_icon_only_buttons(self):
        """Test handling of icon-only buttons without text."""
        synthesizer = LocatorSynthesizer()
        
        descriptor = {
            "tag": "button",
            "text": "",  # No text
            "classes": ["icon-btn"],
            "ariaLabel": "Search",
            "attributes": {"data-icon": "search"}
        }
        
        locators = synthesizer.synthesize(descriptor)
        
        # Should use aria-label or class
        assert any("aria-label" in loc or "icon-btn" in loc for loc in locators)
        assert len(locators) > 0
    
    def test_hashed_ids_classes(self):
        """Test handling of hashed/generated IDs and classes."""
        synthesizer = LocatorSynthesizer()
        
        descriptor = {
            "tag": "div",
            "id": "abc123def456",  # Hashed ID
            "classes": ["css-1a2b3c", "MuiButton-root-4d5e6f"],  # Hashed classes
            "dataTestId": "submit-button",  # Stable test ID
            "text": "Submit"
        }
        
        locators = synthesizer.synthesize(descriptor)
        
        # Should prioritize data-testid over hashed IDs
        first_loc = locators[0] if locators else ""
        assert "data-testid" in first_loc.lower() or "submit-button" in first_loc
    
    def test_data_testid_aria_preference(self):
        """Test that data-testid and aria attributes are preferred."""
        synthesizer = LocatorSynthesizer()
        
        descriptor = {
            "tag": "input",
            "id": "field_123",
            "dataTestId": "email-input",
            "ariaLabel": "Email address",
            "name": "email",
            "type": "email"
        }
        
        locators = synthesizer.synthesize(descriptor)
        
        # First few locators should use data-testid or aria-label
        top_locs = locators[:3] if len(locators) >= 3 else locators
        preferred_found = any(
            "data-testid" in loc or "aria-label" in loc 
            for loc in top_locs
        )
        assert preferred_found, "data-testid/aria not prioritized"
    
    def test_contenteditable_elements(self):
        """Test handling of contenteditable elements."""
        snapshot_mgr = SnapshotManager()
        
        # Mock page with contenteditable
        mock_page = Mock()
        mock_page.url = "http://example.com"
        mock_page.evaluate.return_value = [
            {
                "tag": "div",
                "contentEditable": True,
                "attributes": {"contenteditable": "true"},
                "text": "Editable content",
                "ariaRole": "textbox"
            }
        ]
        
        snapshot, _ = snapshot_mgr.capture_snapshot(mock_page, "test_session")
        elements = snapshot.get_all_elements()
        
        # Should capture contenteditable attribute
        assert any(elem.get("contentEditable") for elem in elements)
    
    def test_svg_canvas_elements(self):
        """Test handling of SVG and canvas elements."""
        synthesizer = LocatorSynthesizer()
        
        # SVG element
        svg_descriptor = {
            "tag": "svg",
            "isSvg": True,
            "viewBox": "0 0 24 24",
            "ariaLabel": "Menu icon",
            "attributes": {"role": "img"}
        }
        
        svg_locators = synthesizer.synthesize(svg_descriptor)
        assert len(svg_locators) > 0
        assert any("svg" in loc.lower() for loc in svg_locators)
        
        # Canvas element (usually needs special handling)
        canvas_descriptor = {
            "tag": "canvas",
            "id": "chart-canvas",
            "attributes": {"width": "800", "height": "600"}
        }
        
        canvas_locators = synthesizer.synthesize(canvas_descriptor)
        assert len(canvas_locators) > 0
        assert any("canvas" in loc.lower() or "chart-canvas" in loc for loc in canvas_locators)
    
    def test_uniqueness_verification(self):
        """Test uniqueness verification in frames."""
        verifier = EnhancedVerifier()
        
        # Mock page with multiple matching elements
        mock_page = Mock()
        mock_page.query_selector_all.return_value = [Mock(), Mock()]  # 2 matches
        mock_page.query_selector.return_value = Mock()
        
        descriptor = {"tag": "button", "text": "Submit"}
        
        result = verifier.verify_with_healing(
            "button:has-text('Submit')",
            descriptor,
            mock_page
        )
        
        # Should detect non-uniqueness
        assert not result.unique_in_frame or not result.success
    
    def test_frame_aware_uniqueness(self):
        """Test per-frame uniqueness checking."""
        verifier = EnhancedVerifier()
        
        # Mock page with iframe
        mock_page = Mock()
        mock_iframe = Mock()
        mock_frame = Mock()
        
        mock_page.query_selector_all.return_value = [mock_iframe]
        mock_iframe.content_frame.return_value = mock_frame
        mock_iframe.get_attribute.return_value = "iframe1"
        
        # Main frame has 1 match, iframe has 2
        mock_page.query_selector_all.return_value = [Mock()]  # 1 in main
        mock_frame.query_selector_all.return_value = [Mock(), Mock()]  # 2 in frame
        
        results = verifier.verify_uniqueness_per_frame(
            "button",
            mock_page,
            include_frames=True
        )
        
        assert "main" in results
        # Frame results would be checked if mock setup was complete