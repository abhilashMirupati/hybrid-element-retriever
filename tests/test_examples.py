"""Comprehensive tests for real-world examples with edge cases."""

import json
import pytest
from pathlib import Path
from typing import Dict, Any, List
import time

from her.cli_api import HybridClient
from her.bridge.snapshot import compute_dom_hash
from her.locator.verify import LocatorVerifier
from her.executor.actions import ActionExecutor

# Get examples directory
EXAMPLES_DIR = Path(__file__).parent.parent / "examples"
DOM_SAMPLES_DIR = EXAMPLES_DIR / "dom_samples" / "realworld"
INTENTS_DIR = EXAMPLES_DIR / "intents" / "realworld"


class TestRealWorldExamples:
    """Test suite for real-world DOM examples with edge cases."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment."""
        self.client = HybridClient(headless=True, auto_index=True)
        self.verifier = LocatorVerifier()
        yield
        self.client.close()

    def test_login_with_modal(self):
        """Test login form with modal popup handling."""
        html_path = DOM_SAMPLES_DIR / "login_with_modal.html"
        intents_path = INTENTS_DIR / "login_intents.json"
        
        assert html_path.exists(), f"HTML file not found: {html_path}"
        assert intents_path.exists(), f"Intents file not found: {intents_path}"
        
        with open(intents_path) as f:
            intents = json.load(f)["intents"]
        
        # Test each intent
        for intent in intents:
            result = self.client.query(
                intent["step"],
                url=f"file://{html_path.absolute()}"
            )
            
            # Verify result structure
            assert "selector" in result, f"Missing selector for {intent['id']}"
            assert "confidence" in result, f"Missing confidence for {intent['id']}"
            assert "element" in result, f"Missing element for {intent['id']}"
            assert "rationale" in result, f"Missing rationale for {intent['id']}"
            
            # Verify confidence is reasonable
            assert result["confidence"] > 0.5, f"Low confidence for {intent['id']}: {result['confidence']}"
            
            # Verify selector is unique
            is_unique = self.verifier.verify_uniqueness(
                self.client.executor.page,
                result["selector"]
            )
            assert is_unique, f"Non-unique selector for {intent['id']}: {result['selector']}"
            
            # Verify no empty fields in JSON
            assert result["selector"], f"Empty selector for {intent['id']}"
            assert result["element"], f"Empty element for {intent['id']}"

    def test_spa_route_changes(self):
        """Test SPA with route changes and DOM updates."""
        html_path = DOM_SAMPLES_DIR / "spa_route_change.html"
        intents_path = INTENTS_DIR / "spa_intents.json"
        
        assert html_path.exists(), f"HTML file not found: {html_path}"
        assert intents_path.exists(), f"Intents file not found: {intents_path}"
        
        with open(intents_path) as f:
            intents = json.load(f)["intents"]
        
        # Navigate to the SPA
        url = f"file://{html_path.absolute()}"
        self.client.executor.page.goto(url)
        
        # Track DOM changes
        initial_hash = None
        dom_hashes = []
        
        for intent in intents[:3]:  # Test first few intents that trigger route changes
            # Get current DOM hash
            snapshot = self.client.session_manager.get_current_snapshot()
            if snapshot:
                current_hash = compute_dom_hash(snapshot["descriptors"])
                dom_hashes.append(current_hash)
                
                if initial_hash is None:
                    initial_hash = current_hash
                elif current_hash != initial_hash:
                    # DOM changed, verify re-indexing happened
                    assert self.client.session_manager.needs_reindex(
                        self.client.current_session_id
                    ), "DOM changed but re-indexing not triggered"
            
            # Execute the intent
            result = self.client.act(intent["step"], url=url)
            
            # Verify action was successful
            assert result["success"], f"Action failed for {intent['id']}: {result.get('error')}"
            assert result["used_locator"], f"No locator used for {intent['id']}"
            
            # Wait for any DOM updates
            time.sleep(0.5)
        
        # Verify we detected DOM changes
        assert len(set(dom_hashes)) > 1, "No DOM changes detected in SPA navigation"

    def test_shadow_dom_nested(self):
        """Test nested shadow DOM component traversal."""
        html_path = DOM_SAMPLES_DIR / "shadow_dom_nested.html"
        intents_path = INTENTS_DIR / "shadow_dom_intents.json"
        
        assert html_path.exists(), f"HTML file not found: {html_path}"
        assert intents_path.exists(), f"Intents file not found: {intents_path}"
        
        with open(intents_path) as f:
            intents = json.load(f)["intents"]
        
        url = f"file://{html_path.absolute()}"
        
        for intent in intents:
            result = self.client.query(intent["step"], url=url)
            
            # Shadow DOM elements should still be found
            assert result["selector"], f"Could not find shadow DOM element for {intent['id']}"
            assert result["confidence"] > 0.4, f"Low confidence for shadow DOM element {intent['id']}"
            
            # Check if element indicates shadow DOM context
            element = result.get("element", {})
            if "shadow" in intent["description"].lower():
                # Verify the element was found within shadow DOM
                assert element, f"No element data for shadow DOM {intent['id']}"

    def test_iframe_forms(self):
        """Test iframe form field detection and interaction."""
        html_path = DOM_SAMPLES_DIR / "iframe_forms.html"
        intents_path = INTENTS_DIR / "iframe_intents.json"
        
        assert html_path.exists(), f"HTML file not found: {html_path}"
        assert intents_path.exists(), f"Intents file not found: {intents_path}"
        
        with open(intents_path) as f:
            intents = json.load(f)["intents"]
        
        url = f"file://{html_path.absolute()}"
        
        for intent in intents:
            result = self.client.query(intent["step"], url=url)
            
            # Iframe elements should be detected
            assert result["selector"], f"Could not find element in iframe for {intent['id']}"
            
            # Check if it's an iframe element
            if "iframe" in intent["description"].lower():
                # Verify frame context is captured
                element = result.get("element", {})
                # Frame elements should have frame context or be detected
                assert element, f"No element data for iframe element {intent['id']}"

    def test_overlay_auto_dismiss(self):
        """Test automatic overlay/modal dismissal."""
        html_path = DOM_SAMPLES_DIR / "login_with_modal.html"
        
        url = f"file://{html_path.absolute()}"
        
        # Trigger modal by submitting form
        result = self.client.act(
            "Click Sign In button to show modal",
            url=url
        )
        
        assert result["success"], "Failed to trigger modal"
        
        # Try to interact with element behind modal
        # The system should auto-dismiss the modal
        result = self.client.act(
            "Click Forgot Password link",
            url=url
        )
        
        # Check if overlays were dismissed
        if "dismissed_overlays" in result:
            assert len(result["dismissed_overlays"]) > 0, "No overlays dismissed"

    def test_occlusion_detection(self):
        """Test occlusion detection and handling."""
        # This would test elementFromPoint logic
        # Create a scenario where an element is occluded
        html = """
        <html>
        <body>
            <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
                        background: rgba(0,0,0,0.5); z-index: 1000;" id="overlay"></div>
            <button id="target" style="position: relative; z-index: 1;">Click Me</button>
        </body>
        </html>
        """
        
        # Save temporary HTML
        temp_path = Path("/tmp/occlusion_test.html")
        temp_path.write_text(html)
        
        try:
            url = f"file://{temp_path.absolute()}"
            
            # Try to click the occluded button
            result = self.client.act("Click the Click Me button", url=url)
            
            # System should detect occlusion
            if not result["success"]:
                assert "occluded" in result.get("error", "").lower() or \
                       "overlay" in result.get("error", "").lower(), \
                       "Occlusion not properly detected"
        finally:
            temp_path.unlink(missing_ok=True)

    def test_post_action_verification(self):
        """Test post-action verification logic."""
        html_path = DOM_SAMPLES_DIR / "spa_route_change.html"
        url = f"file://{html_path.absolute()}"
        
        # Navigate to products
        result = self.client.act("Click on Products in navigation", url=url)
        assert result["success"], "Failed to navigate"
        
        # Verify URL changed (for SPAs using hash routing)
        if "verification" in result:
            verification = result["verification"]
            # Check if URL or DOM changed
            assert verification.get("url_changed") or \
                   verification.get("dom_changed"), \
                   "No post-action changes detected"
        
        # Add item to cart
        result = self.client.act("Add Laptop Pro to cart", url=url)
        assert result["success"], "Failed to add to cart"
        
        # Verify cart count updated
        if "verification" in result:
            assert result["verification"].get("dom_changed"), \
                   "DOM change not detected after adding to cart"

    def test_self_heal_fallback(self):
        """Test self-healing with fallback locators."""
        # Create HTML with dynamic IDs
        html = """
        <html>
        <body>
            <button id="btn_12345" class="submit-btn" aria-label="Submit Form">Submit</button>
        </body>
        </html>
        """
        
        temp_path = Path("/tmp/self_heal_test.html")
        temp_path.write_text(html)
        
        try:
            url = f"file://{temp_path.absolute()}"
            
            # First attempt - learn the element
            result = self.client.act("Click Submit button", url=url)
            assert result["success"], "Initial action failed"
            
            # Change the ID to simulate dynamic content
            html_changed = html.replace("btn_12345", "btn_67890")
            temp_path.write_text(html_changed)
            
            # Second attempt - should use fallback locators
            result = self.client.act("Click Submit button", url=url)
            assert result["success"], "Self-healing failed"
            
            # Check if fallback was used
            if "used_fallback" in result:
                assert result["used_fallback"], "Fallback locator not used"
        finally:
            temp_path.unlink(missing_ok=True)

    def test_cache_performance(self):
        """Test embedding cache hit/miss behavior."""
        html_path = DOM_SAMPLES_DIR / "spa_route_change.html"
        url = f"file://{html_path.absolute()}"
        
        # First query - cache miss
        start_time = time.time()
        result1 = self.client.query("Search for products", url=url)
        time1 = time.time() - start_time
        
        # Second identical query - cache hit
        start_time = time.time()
        result2 = self.client.query("Search for products", url=url)
        time2 = time.time() - start_time
        
        # Cache hit should be faster
        assert time2 < time1 * 0.5, "Cache not improving performance"
        
        # Results should be identical
        assert result1["selector"] == result2["selector"], "Cached results differ"

    def test_strict_json_output(self):
        """Test that all outputs are strict JSON with no empty fields."""
        html_path = DOM_SAMPLES_DIR / "login_with_modal.html"
        url = f"file://{html_path.absolute()}"
        
        # Test act output
        act_result = self.client.act("Enter email address", url=url)
        self._verify_no_empty_fields(act_result, "act")
        
        # Test query output
        query_result = self.client.query("Find login button", url=url)
        self._verify_no_empty_fields(query_result, "query")

    def _verify_no_empty_fields(self, data: Any, context: str):
        """Recursively verify no empty fields in JSON output."""
        if isinstance(data, dict):
            for key, value in data.items():
                assert value is not None, f"Null value for {key} in {context}"
                if isinstance(value, str):
                    assert value.strip(), f"Empty string for {key} in {context}"
                elif isinstance(value, (list, dict)):
                    assert value, f"Empty collection for {key} in {context}"
                    self._verify_no_empty_fields(value, f"{context}.{key}")
        elif isinstance(data, list):
            assert data, f"Empty list in {context}"
            for item in data:
                self._verify_no_empty_fields(item, context)


class TestEdgeCases:
    """Test specific edge cases and error conditions."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment."""
        self.client = HybridClient(headless=True)
        yield
        self.client.close()

    def test_ambiguous_elements(self):
        """Test disambiguation of multiple similar elements."""
        html = """
        <html>
        <body>
            <div class="container">
                <button class="submit">Submit</button>
                <button class="submit">Submit</button>
                <button class="submit">Submit Form</button>
            </div>
        </body>
        </html>
        """
        
        temp_path = Path("/tmp/ambiguous_test.html")
        temp_path.write_text(html)
        
        try:
            url = f"file://{temp_path.absolute()}"
            
            # Query for specific submit button
            result = self.client.query("Click Submit Form button", url=url)
            
            # Should find the one with different text
            assert "Submit Form" in str(result.get("element", {})), \
                   "Wrong element selected from ambiguous set"
            
            # Verify uniqueness
            assert self.verifier.verify_uniqueness(
                self.client.executor.page,
                result["selector"]
            ), "Generated non-unique selector for ambiguous elements"
        finally:
            temp_path.unlink(missing_ok=True)

    def test_delayed_element_loading(self):
        """Test handling of dynamically loaded elements."""
        html = """
        <html>
        <body>
            <div id="container"></div>
            <script>
                setTimeout(() => {
                    document.getElementById('container').innerHTML = 
                        '<button id="delayed">Loaded Button</button>';
                }, 2000);
            </script>
        </body>
        </html>
        """
        
        temp_path = Path("/tmp/delayed_test.html")
        temp_path.write_text(html)
        
        try:
            url = f"file://{temp_path.absolute()}"
            
            # Try to find delayed element
            result = self.client.act(
                "Click Loaded Button",
                url=url
            )
            
            # Should wait for element to appear
            assert result["success"], "Failed to handle delayed element"
        finally:
            temp_path.unlink(missing_ok=True)

    def test_stale_element_handling(self):
        """Test handling of stale element references."""
        html = """
        <html>
        <body>
            <div id="dynamic">
                <button onclick="recreate()">Click Me</button>
            </div>
            <script>
                function recreate() {
                    const div = document.getElementById('dynamic');
                    div.innerHTML = '<button onclick="recreate()">New Button</button>';
                }
            </script>
        </body>
        </html>
        """
        
        temp_path = Path("/tmp/stale_test.html")
        temp_path.write_text(html)
        
        try:
            url = f"file://{temp_path.absolute()}"
            
            # Click button that recreates itself
            result1 = self.client.act("Click the button", url=url)
            assert result1["success"], "First click failed"
            
            # Click again - element is now stale
            result2 = self.client.act("Click the button", url=url)
            assert result2["success"], "Failed to handle stale element"
        finally:
            temp_path.unlink(missing_ok=True)


@pytest.mark.integration
class TestIntegration:
    """Integration tests for complete workflows."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment."""
        self.client = HybridClient(headless=True)
        yield
        self.client.close()

    def test_complete_login_flow(self):
        """Test complete login flow with modal."""
        html_path = DOM_SAMPLES_DIR / "login_with_modal.html"
        url = f"file://{html_path.absolute()}"
        
        # Complete login flow
        steps = [
            "Enter 'user@example.com' in email field",
            "Enter 'password123' in password field",
            "Click Sign In button",
            "Click Accept & Continue in modal"
        ]
        
        for step in steps:
            result = self.client.act(step, url=url)
            assert result["success"], f"Step failed: {step}"
            time.sleep(0.5)  # Allow for animations

    def test_complete_shopping_flow(self):
        """Test complete shopping flow in SPA."""
        html_path = DOM_SAMPLES_DIR / "spa_route_change.html"
        url = f"file://{html_path.absolute()}"
        
        # Shopping flow
        steps = [
            "Click Products in navigation",
            "Add Laptop Pro to cart",
            "Add Wireless Mouse to cart",
            "Click Cart in navigation",
            "Click Proceed to Checkout"
        ]
        
        for step in steps:
            result = self.client.act(step, url=url)
            assert result["success"], f"Step failed: {step}"
            time.sleep(0.5)  # Allow for route changes

    def test_complete_checkout_flow(self):
        """Test complete checkout with iframes."""
        html_path = DOM_SAMPLES_DIR / "iframe_forms.html"
        url = f"file://{html_path.absolute()}"
        
        # Checkout flow
        steps = [
            "Enter 'John Smith' in Full Name field",
            "Enter 'john@example.com' in email field",
            "Enter '123 Main St' in billing address",
            "Select United States from country dropdown",
            "Enter '4111111111111111' in card number field",
            "Enter '12/25' in expiry field",
            "Enter '123' in CVV field",
            "Click Validate Card button",
            "Select Express Shipping option",
            "Click Complete Order button"
        ]
        
        for step in steps:
            result = self.client.act(step, url=url)
            assert result["success"], f"Step failed: {step}"
            time.sleep(0.3)  # Allow for iframe communication