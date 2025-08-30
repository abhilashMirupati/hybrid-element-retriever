#!/usr/bin/env python3
"""Reality check - what actually works with complex HTML."""
# import sys
# removed sys.path hack
def test_complex_html_scenario():
    """Test with actual complex HTML scenarios."""
    
    print("=" * 60)
    print("REALITY CHECK: Testing HER with Complex HTML")
    print("=" * 60)
    
    # Complex HTML descriptor that would come from a real page
    complex_descriptors = [
        # Duplicate buttons with same text
        {"tag": "button", "text": "Submit", "attributes": {"class": "btn primary"}},
        {"tag": "button", "text": "Submit", "attributes": {"class": "btn modal-btn"}},
        {"tag": "button", "text": "Submit", "attributes": {"id": "form-submit"}},
        
        # Nested elements
        {"tag": "div", "attributes": {"class": "container"},
         "children": [{"tag": "button", "text": "Click me"}]},
        
        # SVG elements
        {"tag": "svg", "attributes": {"viewBox": "0 0 24 24"},
         "children": [{"tag": "text", "text": "Icon"}]},
        
        # Elements with special characters
        {"tag": "button", "text": "Save & Continue", "attributes": {}},
        {"tag": "input", "attributes": {"placeholder": "Enter your \"name\""}},
        
        # Dynamic Vue/React attributes
        {"tag": "div", "attributes": {"v-if": "loaded", ":class": "dynamicClass"}},
        {"tag": "button", "attributes": {"@click": "handleClick", "v-show": "visible"}},
        
        # Shadow DOM host
        {"tag": "custom-element", "attributes": {"class": "shadow-host"}},
        
        # Iframe
        {"tag": "iframe", "attributes": {"src": "/form.html", "id": "payment-frame"}},
    ]
    
    print("\n1. Testing basic import:")
    try:
        from her.cli_api import HybridElementRetrieverClient
        print("   ✓ Client imported")
    except ImportError as e:
        print(f"   ✗ Import failed: {e}")
        return
    
    print("\n2. Testing pipeline import:")
    try:
        from her.pipeline import HERPipeline
        print("   ✓ Pipeline imported")
    except ImportError as e:
        print(f"   ✗ Pipeline import failed: {e}")
        print("   Note: Pipeline exists but has dependency issues")
    
    print("\n3. Testing locator synthesis:")
    try:
        from her.locator.synthesize import LocatorSynthesizer
        synth = LocatorSynthesizer()
        
        # Test with duplicate Submit buttons
        submit_button = complex_descriptors[0]
        locators = synth.synthesize(submit_button)
        print(f"   Generated {len(locators)} locators for Submit button:")
        for loc in locators[:3]:
            print(f"     - {loc}")
        
        # Check if XPath or CSS
        has_xpath = any(loc.startswith('//') or loc.startswith('/') for loc in locators)
        has_css = any('.' in loc or '#' in loc for loc in locators)
        print(f"   Has XPath: {has_xpath}, Has CSS: {has_css}")
        
        # Check uniqueness
        all_submits = [d for d in complex_descriptors if d.get('text') == 'Submit']
        print(f"   Problem: {len(all_submits)} buttons with 'Submit' text")
        print(f"   Locators are NOT guaranteed unique!")
        
    except Exception as e:
        print(f"   ✗ Synthesis failed: {e}")
    
    print("\n4. Testing validation:")
    try:
        from her.validators import InputValidator, DOMValidator
        
        # Test special characters
        query = "Find button with text: \"Save & Continue\""
        valid, sanitized, error = InputValidator.validate_query(query)
        print(f"   Query validation: {valid} - {error or 'OK'}")
        
        # Test DOM size
        large_dom = complex_descriptors * 1000  # 12,000 elements
        valid, warning = DOMValidator.validate_dom_size(large_dom)
        print(f"   Large DOM ({len(large_dom)} nodes): {valid} - {warning}")
        
    except Exception as e:
        print(f"   ✗ Validation failed: {e}")
    
    print("\n5. Testing resilience features:")
    try:
        from her.resilience import ResilienceManager
        manager = ResilienceManager()
        print("   ✓ ResilienceManager created")
        print("   ✗ But NOT integrated with main flow!")
    except Exception as e:
        print(f"   ✗ Resilience failed: {e}")
    
    print("\n6. Testing actual query flow:")
    try:
        # This is what actually gets called
        client = HybridElementRetrieverClient()
        
        # Check what it's really using
        print(f"   Session manager type: {type(client.session_manager).__name__}")
        print(f"   Has pipeline? {hasattr(client, 'pipeline')}")  # Should be False
        
        # Look at the actual query implementation
        import inspect
        source = inspect.getsource(client.query)
        uses_pipeline = 'pipeline' in source.lower()
        uses_find_candidates = '_find_candidates' in source
        
        print(f"   Uses HERPipeline? {uses_pipeline}")  # False
        print(f"   Uses old _find_candidates? {uses_find_candidates}")  # True
        
    except Exception as e:
        print(f"   ✗ Client check failed: {e}")
    
    print("\n7. Edge case reality check:")
    print("   Would fail on:")
    print("   ✗ Shadow DOM - no piercing implementation")
    print("   ✗ Iframes - no context switching")
    print("   ✗ Duplicate elements - no uniqueness guarantee")
    print("   ✗ Vue/React - no wait for rendering")
    print("   ✗ SVG - not properly handled")
    print("   ✗ Cookie banners - no auto-dismiss")
    
    print("\n8. Performance reality:")
    print("   ✗ No actual embeddings (numpy missing)")
    print("   ✗ Models not present in models/ directory")
    print("   ✗ Falls back to fake [0.0] vectors")
    print("   ✗ <2s resolution not tested on real DOM")
    
    print("\n" + "=" * 60)
    print("VERDICT: Implementation is ~60% complete")
    print("- Looks production-ready in structure")
    print("- Actually disconnected components")
    print("- Would fail on complex HTML")
    print("- Needs major integration work")
    print("=" * 60)


def test_what_xpath_we_actually_get():
    """Show what XPath we actually generate."""
    
    print("\n" + "=" * 60)
    print("WHAT XPATH DO WE ACTUALLY GENERATE?")
    print("=" * 60)
    
    try:
        from her.locator.synthesize import LocatorSynthesizer
        synth = LocatorSynthesizer()
        
        test_cases = [
            {
                "name": "Simple button",
                "descriptor": {"tag": "button", "text": "Click me", "id": "btn1"}
            },
            {
                "name": "Duplicate button (1 of 3)",
                "descriptor": {"tag": "button", "text": "Submit", "attributes": {"class": "primary"}}
            },
            {
                "name": "Complex nested",
                "descriptor": {"tag": "button", "text": "Submit", 
                              "attributes": {"class": "btn btn-primary btn-lg"},
                              "parent": {"tag": "form", "id": "login-form"}}
            },
            {
                "name": "Special characters",
                "descriptor": {"tag": "button", "text": "Save & Continue"}
            }
        ]
        
        for test in test_cases:
            print(f"\n{test['name']}:")
            print(f"  Input: {test['descriptor']}")
            
            locators = synth.synthesize(test['descriptor'])
            print(f"  Generated {len(locators)} locators:")
            
            for i, loc in enumerate(locators[:5], 1):
                loc_type = "XPath" if loc.startswith('/') else "CSS"
                print(f"    {i}. [{loc_type}] {loc}")
            
            # Check if unique XPath exists
            xpath_locs = [l for l in locators if l.startswith('/')]
            if xpath_locs:
                print(f"  ✓ Has {len(xpath_locs)} XPath selectors")
            else:
                print(f"  ✗ No XPath selectors generated!")
    
    except Exception as e:
        print(f"Failed to test XPath generation: {e}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_complex_html_scenario()
    test_what_xpath_we_actually_get()
    
    print("\n🔴 CRITICAL FINDING:")
    print("The implementation has good structure but core components")
    print("are not connected. It would NOT handle complex HTML correctly.")
    print("\nRequired: Complete integration of pipeline with cli_api")
    print("Required: Real embedding models or working fallbacks")
    print("Required: Unique XPath generation and verification")
    print("Required: Actual edge case handling in main flow")