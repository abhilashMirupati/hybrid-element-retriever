#!/usr/bin/env python3
"""Real integration test - does HER actually produce XPaths?"""
# import sys
# from pathlib import Path
# removed sys.path hack
print("=" * 70)
print("REAL INTEGRATION TEST - DOES HER ACTUALLY PRODUCE XPATHS?")
print("=" * 70)

# Test 1: Can we import the main client?
try:
    from her.cli_api import HybridElementRetrieverClient
    print("✓ HybridElementRetrieverClient imports")
except Exception as e:
    print(f"✗ Failed to import client: {e}")
    sys.exit(1)

# Test 2: Can we create a client?
try:
    client = HybridElementRetrieverClient(use_enhanced=True)
    print("✓ Client created")
except Exception as e:
    print(f"✗ Failed to create client: {e}")
    sys.exit(1)

# Test 3: Does the pipeline exist and work?
try:
    from her.pipeline import HERPipeline
    pipeline = HERPipeline()
    print("✓ Pipeline created")
except Exception as e:
    print(f"✗ Pipeline failed: {e}")

# Test 4: Can we generate XPath from a descriptor?
print("\n" + "=" * 70)
print("TESTING XPATH GENERATION")
print("=" * 70)

try:
    from her.locator.synthesize import LocatorSynthesizer
    synthesizer = LocatorSynthesizer()
    
    # Test case 1: Button with ID
    descriptor1 = {
        "tag": "button",
        "id": "submit-btn",
        "text": "Submit"
    }
    
    locators1 = synthesizer.synthesize(descriptor1)
    print(f"\nButton with ID:")
    print(f"  Input: {descriptor1}")
    print(f"  Generated XPaths: {locators1[:3] if len(locators1) > 3 else locators1}")
    
    # Check if we got XPath
    has_xpath = any(loc.startswith('//') or loc.startswith('/') for loc in locators1)
    print(f"  Has XPath: {'✓' if has_xpath else '✗'}")
    
    # Test case 2: Duplicate buttons
    descriptor2 = {
        "tag": "button",
        "text": "Submit",
        "classes": ["btn", "btn-primary"]
    }
    
    locators2 = synthesizer.synthesize(descriptor2)
    print(f"\nButton without ID (duplicate scenario):")
    print(f"  Input: {descriptor2}")
    print(f"  Generated XPaths: {locators2[:3] if len(locators2) > 3 else locators2}")
    
    has_xpath2 = any(loc.startswith('//') or loc.startswith('/') for loc in locators2)
    print(f"  Has XPath: {'✓' if has_xpath2 else '✗'}")
    
except Exception as e:
    print(f"✗ XPath generation failed: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Does the actual query flow work?
print("\n" + "=" * 70)
print("TESTING FULL QUERY FLOW")
print("=" * 70)

try:
    # Mock descriptors as if from a page
    mock_descriptors = [
        {"tag": "button", "id": "login", "text": "Login"},
        {"tag": "input", "id": "email", "type": "email", "placeholder": "Email"},
        {"tag": "button", "text": "Submit", "classes": ["submit-btn"]}
    ]
    
    # Test query through pipeline
    if 'pipeline' in locals():
        result = pipeline.process(
            query="click the submit button",
            descriptors=mock_descriptors
        )
        print(f"Pipeline result: {result}")
        
        if result and 'xpath' in result:
            print(f"✓ Pipeline returned XPath: {result['xpath']}")
        else:
            print(f"✗ Pipeline didn't return XPath")
    
except Exception as e:
    print(f"✗ Full query flow failed: {e}")
    import traceback
    traceback.print_exc()

# Test 6: Check actual integration points
print("\n" + "=" * 70)
print("CHECKING INTEGRATION POINTS")
print("=" * 70)

# Check if cli_api actually uses pipeline
try:
    with open('src/her/cli_api.py', 'r') as f:
        cli_content = f.read()
        
    uses_pipeline = 'HERPipeline' in cli_content or 'pipeline' in cli_content.lower()
    uses_synthesizer = 'synthesize' in cli_content or 'LocatorSynthesizer' in cli_content
    
    print(f"cli_api.py uses Pipeline: {'✓' if uses_pipeline else '✗'}")
    print(f"cli_api.py uses Synthesizer: {'✓' if uses_synthesizer else '✗'}")
    
    if not uses_pipeline:
        print("  WARNING: cli_api might not be using the pipeline!")
    
except Exception as e:
    print(f"✗ Failed to check integration: {e}")

# Test 7: Verify action executor integration
print("\n" + "=" * 70)
print("CHECKING ACTION EXECUTOR")
print("=" * 70)

try:
    from her.actions import ActionExecutor, ActionResult
    
    # Create mock page
    class MockPage:
        def __init__(self):
            self.url = "http://test.com"
        def on(self, event, handler):
            pass
        def evaluate(self, js):
            return "complete"
        def query_selector(self, sel):
            return None
            
    mock_page = MockPage()
    executor = ActionExecutor(mock_page)
    
    result = executor.execute_click("button#test", verify=False)
    
    # Check if result has proper structure
    result_dict = result.to_dict()
    
    has_frame_info = 'frame' in result_dict
    has_waits = 'waits' in result_dict
    has_post_action = 'post_action' in result_dict
    
    print(f"ActionResult has frame info: {'✓' if has_frame_info else '✗'}")
    print(f"ActionResult has waits: {'✓' if has_waits else '✗'}")
    print(f"ActionResult has post_action: {'✓' if has_post_action else '✗'}")
    
except Exception as e:
    print(f"✗ Action executor check failed: {e}")

# Final verdict
print("\n" + "=" * 70)
print("FINAL VERDICT")
print("=" * 70)

issues = []

# Check critical issues
if not has_xpath:
    issues.append("NOT GENERATING XPATHS")
    
if not uses_pipeline:
    issues.append("CLI NOT USING PIPELINE")

if not has_frame_info:
    issues.append("MISSING FRAME METADATA")

if issues:
    print("❌ CRITICAL ISSUES FOUND:")
    for issue in issues:
        print(f"  - {issue}")
    print("\nThe framework is NOT properly integrated!")
else:
    print("✅ All integration points working!")
    print("The framework DOES generate XPaths and is properly integrated.")

print("=" * 70)