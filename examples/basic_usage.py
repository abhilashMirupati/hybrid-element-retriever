#!/usr/bin/env python3
"""Basic usage examples for HER."""

from her import HybridElementRetriever


def main():
    """Demonstrate basic HER usage."""
    print("Hybrid Element Retriever - Basic Usage Examples")
    print("=" * 50)
    
    # Initialize HER client
    her = HybridElementRetriever()
    
    # Example 1: Simple element query
    print("\n1. Simple Query:")
    print("   Query: 'Find submit button'")
    results = her.query("Find submit button")
    print(f"   Results: {results}")
    
    # Example 2: Query with navigation
    print("\n2. Query with Navigation:")
    print("   Query: 'Find search box' on example.com")
    results = her.query("Find search box", url="https://example.com")
    print(f"   Results: {results}")
    
    # Example 3: Click action
    print("\n3. Click Action:")
    print("   Action: Click on login button")
    result = her.click("Click on the login button")
    print(f"   Result: {result}")
    
    # Example 4: Type text
    print("\n4. Type Text:")
    print("   Action: Enter email address")
    result = her.type_text("Enter email in the email field", "user@example.com")
    print(f"   Result: {result}")
    
    # Example 5: Find multiple elements
    print("\n5. Find Multiple Elements:")
    print("   Query: 'Find all navigation links'")
    results = her.query("Find all navigation links")
    if isinstance(results, list):
        print(f"   Found {len(results)} links")
    
    # Example 6: Complex query
    print("\n6. Complex Query:")
    print("   Query: 'Find the blue submit button in the login form'")
    results = her.query("Find the blue submit button in the login form")
    print(f"   Results: {results}")
    
    print("\n" + "=" * 50)
    print("Examples completed successfully!")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        print("\nNote: Some examples may require a running browser.")
        print("Install playwright: pip install playwright")
        print("Install browser: playwright install chromium")