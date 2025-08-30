#!/usr/bin/env python3
"""Debug pipeline issue."""
# import sys
# removed sys.path hack
from her.pipeline import HERPipeline, PipelineConfig

# Test data
descriptors = [
    {"tag": "button", "text": "Submit Form", "id": "submit-btn"},
    {"tag": "input", "type": "email", "id": "email-field"},
    {"tag": "a", "text": "Login", "attributes": {"href": "/login"}}
]

# Create pipeline
config = PipelineConfig(
    use_minilm=False,
    use_e5_small=True,
    use_markuplm=True
)
pipeline = HERPipeline(config)

# Process query
print("Testing pipeline with query: 'Find the submit button'")
print("Descriptors:", descriptors)
print()

try:
    result = pipeline.process(
        query="Find the submit button",
        descriptors=descriptors,
        page=None,
        session_id="test"
    )
    
    print("Result:", result)
    
    if result.get('xpath'):
        print(f"✓ SUCCESS: Got XPath: {result['xpath']}")
    else:
        print(f"✗ FAILED: No XPath returned")
        print(f"  Error: {result.get('context', {}).get('error', 'Unknown')}")
        
except Exception as e:
    print(f"✗ Exception: {e}")
    import traceback
    traceback.print_exc()