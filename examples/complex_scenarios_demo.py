#!/usr/bin/env python3
"""
Demo of HER's advanced complex scenario handling capabilities.

This demonstrates how HER handles:
- Dynamic content (AJAX, lazy loading)
- Stale elements
- iFrames
- Shadow DOM
- Single Page Applications (SPAs)
- Popups and modals
"""

import logging
from her.cli_api import HybridClient

# Enable detailed logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def demo_dynamic_content():
    """Demo handling of dynamic content."""
    print("\n" + "=" * 60)
    print("DEMO: Dynamic Content Handling")
    print("=" * 60)
    
    with HybridClient(headless=False) as client:
        # Example: Handle infinite scroll
        print("\n1. Handling infinite scroll on a news site...")
        result = client.act_complex(
            "Click on the 10th article",
            url="https://example-news-site.com",
            handle_dynamic=True  # Will scroll to load content
        )
        print(f"   Result: {result['status']}")
        
        # Example: Wait for AJAX content
        print("\n2. Handling AJAX-loaded search results...")
        client.act_complex(
            "Type 'machine learning' in the search box",
            url="https://example-search.com"
        )
        
        # The complex handler will wait for results to load
        result = client.act_complex(
            "Click the first search result",
            handle_dynamic=True
        )
        print(f"   Result: {result['status']}")
        
        # Example: Lazy-loaded images
        print("\n3. Handling lazy-loaded content...")
        result = client.act_complex(
            "Click on the last image in the gallery",
            url="https://example-gallery.com",
            handle_dynamic=True  # Will scroll through page to load images
        )
        print(f"   Result: {result['status']}")


def demo_stale_elements():
    """Demo handling of stale element references."""
    print("\n" + "=" * 60)
    print("DEMO: Stale Element Handling")
    print("=" * 60)
    
    with HybridClient(headless=False) as client:
        # Example: Elements that get re-rendered
        print("\n1. Handling elements that get re-rendered...")
        client.act_complex(
            "Navigate to dynamic form",
            url="https://example-form.com"
        )
        
        # This might cause the form to re-render
        client.act_complex("Select 'Premium' from the plan dropdown")
        
        # The element might be stale now, but complex handler will retry
        result = client.act_complex(
            "Fill 'john.doe@example.com' in the email field",
            handle_dynamic=True,
            max_retries=3  # Will retry up to 3 times if element becomes stale
        )
        print(f"   Result: {result['status']}")
        
        # Example: React/Vue components that re-render
        print("\n2. Handling React component re-renders...")
        result = client.act_complex(
            "Click the submit button",
            handle_dynamic=True  # Will handle if button gets re-rendered
        )
        print(f"   Result: {result['status']}")


def demo_iframe_handling():
    """Demo handling of iframes."""
    print("\n" + "=" * 60)
    print("DEMO: iFrame Handling")
    print("=" * 60)
    
    with HybridClient(headless=False) as client:
        # Example: Form inside iframe
        print("\n1. Handling form inside iframe...")
        client.act_complex(
            "Navigate to page with embedded form",
            url="https://example-with-iframe.com"
        )
        
        # Automatically searches in iframes
        result = client.act_complex(
            "Fill 'John Doe' in the name field",
            handle_frames=True  # Will search in all frames
        )
        print(f"   Result: {result['status']}")
        
        # Example: Nested iframes
        print("\n2. Handling nested iframes...")
        result = client.act_complex(
            "Click the accept button in the payment frame",
            handle_frames=True  # Will search even in nested frames
        )
        print(f"   Result: {result['status']}")
        
        # Example: Cross-origin iframe (limited access)
        print("\n3. Handling cross-origin iframe...")
        result = client.act_complex(
            "Click the video play button",
            url="https://example-with-video.com",
            handle_frames=True
        )
        print(f"   Result: {result['status']}")


def demo_shadow_dom():
    """Demo handling of Shadow DOM."""
    print("\n" + "=" * 60)
    print("DEMO: Shadow DOM Handling")
    print("=" * 60)
    
    with HybridClient(headless=False) as client:
        # Example: Web Components with Shadow DOM
        print("\n1. Handling custom web components...")
        client.act_complex(
            "Navigate to web components demo",
            url="https://example-webcomponents.com"
        )
        
        # Will pierce through Shadow DOM
        result = client.act_complex(
            "Click the custom button component",
            handle_shadow=True  # Will search in shadow roots
        )
        print(f"   Result: {result['status']}")
        
        # Example: Polymer/LitElement components
        print("\n2. Handling Polymer elements...")
        result = client.act_complex(
            "Type 'test@example.com' in the paper-input element",
            handle_shadow=True
        )
        print(f"   Result: {result['status']}")
        
        # Example: Nested Shadow DOM
        print("\n3. Handling nested shadow roots...")
        result = client.act_complex(
            "Click the submit button inside the form component",
            handle_shadow=True  # Will search in nested shadow DOMs
        )
        print(f"   Result: {result['status']}")


def demo_spa_navigation():
    """Demo handling of Single Page Applications."""
    print("\n" + "=" * 60)
    print("DEMO: SPA Navigation Handling")
    print("=" * 60)
    
    with HybridClient(headless=False) as client:
        # Example: React Router navigation
        print("\n1. Handling React Router navigation...")
        client.act_complex(
            "Navigate to React SPA",
            url="https://example-react-app.com"
        )
        
        # Click will trigger client-side navigation
        result = client.act_complex(
            "Click the 'About' link",
            handle_spa=True  # Will wait for route change
        )
        print(f"   Result: {result['status']}")
        
        # Content is loaded dynamically after route change
        result = client.act_complex(
            "Click the 'Contact Us' button",
            handle_spa=True,
            handle_dynamic=True  # Wait for new content to load
        )
        print(f"   Result: {result['status']}")
        
        # Example: Vue Router with lazy loading
        print("\n2. Handling Vue Router with code splitting...")
        result = client.act_complex(
            "Navigate to the dashboard",
            handle_spa=True  # Will wait for chunk to load
        )
        print(f"   Result: {result['status']}")
        
        # Example: Angular routing
        print("\n3. Handling Angular route changes...")
        result = client.act_complex(
            "Click on user profile",
            handle_spa=True,
            handle_dynamic=True  # Angular might update DOM after routing
        )
        print(f"   Result: {result['status']}")


def demo_popup_handling():
    """Demo handling of popups and modals."""
    print("\n" + "=" * 60)
    print("DEMO: Popup and Modal Handling")
    print("=" * 60)
    
    with HybridClient(headless=False) as client:
        # Example: Cookie consent banner
        print("\n1. Auto-dismissing cookie banners...")
        result = client.act_complex(
            "Click the main navigation menu",
            url="https://example-with-cookies.com"
            # Cookie banner will be auto-dismissed
        )
        print(f"   Result: {result['status']}")
        
        # Example: Newsletter popup
        print("\n2. Handling newsletter popups...")
        result = client.act_complex(
            "Click the product image",
            url="https://example-shop.com"
            # Popup will be auto-closed if it appears
        )
        print(f"   Result: {result['status']}")
        
        # Example: Modal dialog
        print("\n3. Interacting with modal content...")
        client.act_complex("Click the 'Open Settings' button")
        
        # Can interact with elements in the modal
        result = client.act_complex(
            "Toggle the dark mode switch",
            handle_dynamic=True  # Modal might have animation
        )
        print(f"   Result: {result['status']}")


def demo_complex_real_world():
    """Demo a complex real-world scenario combining multiple challenges."""
    print("\n" + "=" * 60)
    print("DEMO: Complex Real-World Scenario")
    print("=" * 60)
    
    with HybridClient(headless=False, log_level="DEBUG") as client:
        print("\nScenario: Complete a purchase on a modern e-commerce SPA")
        print("-" * 50)
        
        # 1. Navigate and handle cookie banner
        print("\n1. Navigating to shop...")
        client.act_complex(
            "Navigate to shop",
            url="https://example-modern-shop.com"
        )
        
        # 2. Search with AJAX autocomplete
        print("\n2. Searching for product...")
        client.act_complex(
            "Type 'wireless headphones' in the search box",
            handle_dynamic=True  # Wait for autocomplete
        )
        
        client.act_complex(
            "Click the first suggestion",
            handle_dynamic=True  # AJAX search results
        )
        
        # 3. Handle infinite scroll product list
        print("\n3. Browsing products (infinite scroll)...")
        client.act_complex(
            "Click on the 5th product",
            handle_dynamic=True  # Will scroll to load more products
        )
        
        # 4. SPA navigation to product page
        print("\n4. Viewing product details...")
        # Page changes without full reload
        client.act_complex(
            "Select 'Black' from color options",
            handle_spa=True,
            handle_dynamic=True  # Product images might update
        )
        
        # 5. Add to cart (might update header cart icon)
        print("\n5. Adding to cart...")
        client.act_complex(
            "Click the 'Add to Cart' button",
            handle_stale=True  # Button might get re-rendered
        )
        
        # 6. Navigate to cart (SPA route change)
        print("\n6. Going to cart...")
        client.act_complex(
            "Click the cart icon",
            handle_spa=True
        )
        
        # 7. Proceed to checkout (might open in iframe)
        print("\n7. Proceeding to checkout...")
        client.act_complex(
            "Click 'Proceed to Checkout'",
            handle_frames=True,  # Payment might be in iframe
            handle_dynamic=True
        )
        
        # 8. Fill form that might have custom components
        print("\n8. Filling checkout form...")
        client.act_complex(
            "Fill 'john.doe@example.com' in the email field",
            handle_shadow=True,  # Might use web components
            handle_stale=True
        )
        
        client.act_complex(
            "Fill '123 Main St' in the address field",
            handle_frames=True  # Might be in iframe
        )
        
        # 9. Handle payment (often in iframe with shadow DOM)
        print("\n9. Entering payment details...")
        client.act_complex(
            "Fill '4111111111111111' in the card number field",
            handle_frames=True,
            handle_shadow=True,  # Payment components often use Shadow DOM
            handle_dynamic=True
        )
        
        # 10. Complete purchase
        print("\n10. Completing purchase...")
        result = client.act_complex(
            "Click the 'Complete Purchase' button",
            handle_spa=True,  # Will navigate to confirmation
            handle_dynamic=True,  # Wait for processing
            max_retries=5  # Important action, retry more
        )
        
        print(f"\n✅ Purchase completed: {result['status']}")
        print(f"   Method used: {result.get('details', {}).get('method')}")


def main():
    """Run all demos."""
    print("\n" + "🎯" * 30)
    print("HER COMPLEX SCENARIO HANDLING DEMOS")
    print("🎯" * 30)
    
    demos = [
        ("Dynamic Content", demo_dynamic_content),
        ("Stale Elements", demo_stale_elements),
        ("iFrame Handling", demo_iframe_handling),
        ("Shadow DOM", demo_shadow_dom),
        ("SPA Navigation", demo_spa_navigation),
        ("Popup Handling", demo_popup_handling),
        ("Complex Real-World", demo_complex_real_world)
    ]
    
    print("\nAvailable demos:")
    for i, (name, _) in enumerate(demos, 1):
        print(f"  {i}. {name}")
    print(f"  {len(demos) + 1}. Run all demos")
    
    choice = input("\nSelect demo (1-8): ").strip()
    
    try:
        choice_num = int(choice)
        if 1 <= choice_num <= len(demos):
            name, demo_func = demos[choice_num - 1]
            print(f"\nRunning: {name}")
            demo_func()
        elif choice_num == len(demos) + 1:
            print("\nRunning all demos...")
            for name, demo_func in demos:
                print(f"\n{'='*60}")
                print(f"Running: {name}")
                demo_func()
        else:
            print("Invalid choice")
    except ValueError:
        print("Invalid input")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "✨" * 30)
    print("Demo complete! HER handles complex scenarios with ease.")
    print("✨" * 30)


if __name__ == "__main__":
    main()