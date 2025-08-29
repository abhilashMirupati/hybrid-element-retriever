#!/usr/bin/env python3
"""Advanced feature examples for HER."""

from her import (
    HERPipeline, 
    PipelineConfig,
    ResilienceManager, 
    WaitStrategy,
    InputValidator,
    DOMValidator,
    FormValidator
)


def pipeline_example():
    """Demonstrate pipeline configuration and usage."""
    print("\n🔧 Pipeline Configuration Example")
    print("-" * 40)
    
    # Configure pipeline for maximum accuracy
    config = PipelineConfig(
        use_minilm=False,
        use_e5_small=True,
        use_markuplm=True,
        enable_cold_start_detection=True,
        enable_incremental_updates=True,
        enable_spa_tracking=True,
        verify_url=True,
        verify_dom_state=True,
        max_retry_attempts=3,
        embedding_batch_size=64,
        similarity_threshold=0.8
    )
    
    pipeline = HERPipeline(config)
    
    # Process a query
    descriptors = [
        {"tag": "button", "text": "Submit", "id": "submit-btn"},
        {"tag": "button", "text": "Cancel", "id": "cancel-btn"},
        {"tag": "input", "type": "email", "id": "email-field"}
    ]
    
    result = pipeline.process(
        query="Find the submit button",
        descriptors=descriptors,
        session_id="demo-session"
    )
    
    print(f"XPath: {result['xpath']}")
    print(f"Confidence: {result['confidence']:.2f}")
    print(f"Context: {result['context']}")
    print(f"Fallbacks: {len(result['fallbacks'])} alternatives available")


def resilience_example():
    """Demonstrate resilience features."""
    print("\n🛡️ Resilience Features Example")
    print("-" * 40)
    
    manager = ResilienceManager()
    
    # Mock page object for demonstration
    class MockPage:
        def evaluate(self, script):
            return "complete"
        
        @property
        def url(self):
            return "https://example.com"
    
    page = MockPage()
    
    # Wait strategies
    print("Testing wait strategies:")
    strategies = [
        WaitStrategy.IDLE,
        WaitStrategy.LOAD_COMPLETE,
        WaitStrategy.NETWORK_IDLE
    ]
    
    for strategy in strategies:
        result = manager.wait_for_idle(page, strategy)
        print(f"  {strategy.value}: {'✓' if result else '✗'}")
    
    # Error recovery
    print("\nTesting error recovery:")
    errors = [
        Exception("stale element reference"),
        Exception("timeout waiting for selector"),
        Exception("CDP connection lost")
    ]
    
    for error in errors:
        recovery = manager.recover_from_error(error, page, {})
        if recovery:
            print(f"  {str(error)[:30]}: {recovery['action']} ({recovery['reason']})")
    
    # Snapshot creation
    print("\nCreating stable snapshot:")
    snapshot = manager.create_stable_snapshot(page)
    print(f"  Snapshot created with {len(snapshot)} items")


def validation_example():
    """Demonstrate input validation."""
    print("\n✅ Input Validation Example")
    print("-" * 40)
    
    # Query validation
    print("Query validation:")
    test_queries = [
        "Find submit button",
        "",  # Empty
        "A" * 600,  # Too long
        "Search for 世界",  # Unicode
        "Find button with text: \"Click 'here'\""  # Special chars
    ]
    
    for query in test_queries[:3]:  # Show first 3 for brevity
        valid, sanitized, error = InputValidator.validate_query(query)
        status = "✓" if valid else "✗"
        display_query = query[:30] + "..." if len(query) > 30 else query
        print(f"  [{status}] '{display_query}': {error or 'Valid'}")
    
    # XPath validation
    print("\nXPath validation:")
    test_xpaths = [
        "//div[@id='test']",
        "div[@id='test']",  # Missing /
        "//div[@id='test'"  # Unbalanced
    ]
    
    for xpath in test_xpaths:
        valid, sanitized, error = InputValidator.validate_xpath(xpath)
        status = "✓" if valid else "✗"
        print(f"  [{status}] {xpath}: {error or 'Valid'}")
    
    # Form validation
    print("\nForm input validation:")
    form_inputs = [
        ("email", "user@example.com"),
        ("email", "invalid-email"),
        ("date", "2024-01-15"),
        ("tel", "(555) 123-4567")
    ]
    
    for input_type, value in form_inputs:
        valid, sanitized, error = FormValidator.validate_form_input(input_type, value)
        status = "✓" if valid else "✗"
        print(f"  [{status}] {input_type}: {value} -> {error or 'Valid'}")


def dom_handling_example():
    """Demonstrate DOM handling features."""
    print("\n📄 DOM Handling Example")
    print("-" * 40)
    
    # Handle duplicate elements
    print("Handling duplicate elements:")
    descriptors = [
        {"tag": "button", "text": "Click"},
        {"tag": "button", "text": "Click"},  # Duplicate
        {"tag": "button", "text": "Submit"}
    ]
    
    unique = DOMValidator.handle_duplicate_elements(descriptors)
    print(f"  Original: {len(descriptors)} elements")
    print(f"  After deduplication: {len(unique)} elements")
    
    # Validate DOM size
    print("\nDOM size validation:")
    large_dom = [{"tag": "div", "id": f"elem-{i}"} for i in range(5000)]
    valid, warning = DOMValidator.validate_dom_size(large_dom)
    print(f"  5000 nodes: {'✓' if valid else '✗'} {warning or 'OK'}")
    
    huge_dom = [{"tag": "div", "id": f"elem-{i}"} for i in range(15000)]
    valid, warning = DOMValidator.validate_dom_size(huge_dom)
    print(f"  15000 nodes: {'✓' if valid else '✗'} {warning or 'OK'}")


def caching_example():
    """Demonstrate caching features."""
    print("\n💾 Caching Example")
    print("-" * 40)
    
    from her.cache.two_tier import TwoTierCache
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = TwoTierCache(cache_dir=tmpdir)
        
        # Store items
        print("Storing items in cache:")
        for i in range(10):
            cache.set(f"key-{i}", f"value-{i}")
        print(f"  Stored 10 items")
        
        # Retrieve items
        print("\nRetrieving from cache:")
        hits = 0
        for i in range(15):
            value = cache.get(f"key-{i}")
            if value:
                hits += 1
        print(f"  Cache hits: {hits}/15")
        
        # Clear old entries
        cache.clear_old_entries(max_age_seconds=0)
        print(f"\nAfter clearing old entries:")
        remaining = sum(1 for i in range(10) if cache.get(f"key-{i}"))
        print(f"  Remaining items: {remaining}")


def main():
    """Run all advanced examples."""
    print("=" * 50)
    print("Hybrid Element Retriever - Advanced Features")
    print("=" * 50)
    
    try:
        pipeline_example()
    except Exception as e:
        print(f"Pipeline example error: {e}")
    
    try:
        resilience_example()
    except Exception as e:
        print(f"Resilience example error: {e}")
    
    try:
        validation_example()
    except Exception as e:
        print(f"Validation example error: {e}")
    
    try:
        dom_handling_example()
    except Exception as e:
        print(f"DOM handling example error: {e}")
    
    try:
        caching_example()
    except Exception as e:
        print(f"Caching example error: {e}")
    
    print("\n" + "=" * 50)
    print("Advanced examples completed!")


if __name__ == "__main__":
    main()