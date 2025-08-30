> Archived during canonicalization; superseded by docs/ARCHITECTURE.md (2025-08-30).
# HER Complex Scenarios Handling Guide

## Overview

HER is designed to handle the most challenging web automation scenarios that traditional frameworks struggle with. This guide covers our advanced capabilities for dealing with modern web applications.

## Table of Contents

1. [Dynamic Content](#dynamic-content)
2. [Stale Elements](#stale-elements)
3. [iFrames](#iframes)
4. [Shadow DOM](#shadow-dom)
5. [Single Page Applications](#single-page-applications)
6. [Popups and Modals](#popups-and-modals)
7. [Best Practices](#best-practices)
8. [Performance Considerations](#performance-considerations)

## Dynamic Content

### Problem
Modern websites load content dynamically through:
- AJAX requests
- Lazy loading
- Infinite scroll
- Progressive rendering
- Virtual scrolling

### HER's Solution

```python
from her.cli_api import HybridClient

client = HybridClient()

# Automatically handles dynamic content
result = client.act_complex(
    "Click the 50th item in the list",
    url="https://example.com",
    handle_dynamic=True  # Enables dynamic content handling
)
```

#### Features:
- **Automatic scrolling**: Scrolls to load content for infinite scroll
- **AJAX detection**: Waits for network requests to complete
- **DOM stability**: Waits for DOM to stop changing
- **Lazy loading**: Scrolls through page to trigger lazy-loaded elements
- **Smart waiting**: Adaptive wait strategies based on page behavior

#### Wait Strategies:

```python
# Custom wait configuration
from her.handlers.complex_scenarios import WaitStrategy

strategy = WaitStrategy(
    timeout=30.0,           # Maximum wait time
    poll_interval=0.5,      # Check interval
    stable_time=0.5,        # Time DOM must be stable
    retry_on_stale=True,    # Retry if element becomes stale
    max_retries=3           # Maximum retry attempts
)
```

## Stale Elements

### Problem
Elements become "stale" when:
- React/Vue/Angular re-renders components
- DOM is dynamically updated
- Page partially refreshes
- JavaScript modifies element references

### HER's Solution

```python
# HER automatically handles stale elements
result = client.act_complex(
    "Click submit button",
    handle_stale=True,  # Enable stale element protection
    max_retries=5       # Retry up to 5 times
)
```

#### How It Works:
1. Detects stale element exceptions
2. Re-queries for the element
3. Waits for element stability
4. Retries the action
5. Falls back to alternative locators if needed

#### Stale Element Patterns Handled:
- `Element is not attached to the DOM`
- `Element is no longer valid`
- `Stale element reference`
- `Element has been removed`

## iFrames

### Problem
Content in iframes is isolated from the main page:
- Embedded forms
- Payment gateways
- Third-party widgets
- Nested iframes
- Cross-origin restrictions

### HER's Solution

```python
# Automatically searches in all frames
result = client.act_complex(
    "Fill credit card number",
    handle_frames=True  # Search in all frames including nested
)
```

#### Frame Detection Methods:
1. **Automatic search**: Searches all frames for matching elements
2. **Frame attributes**: Find frames by name, URL, or title
3. **Nested frames**: Recursively searches nested iframes
4. **Cross-origin handling**: Graceful degradation for restricted frames

#### Example: Payment Form in iFrame

```python
# Navigate to checkout
client.act_complex("Go to checkout", url="https://shop.example.com")

# Automatically finds and fills fields in payment iframe
client.act_complex(
    "Fill '4111111111111111' in card number",
    handle_frames=True
)
client.act_complex(
    "Fill '12/25' in expiry date",
    handle_frames=True
)
client.act_complex(
    "Fill '123' in CVV",
    handle_frames=True
)
```

## Shadow DOM

### Problem
Shadow DOM encapsulates components:
- Web Components
- Polymer elements
- LitElement
- Custom elements
- Browser native controls

### HER's Solution

```python
# Automatically pierces shadow DOM
result = client.act_complex(
    "Click custom button component",
    handle_shadow=True  # Enable shadow DOM traversal
)
```

#### Shadow DOM Strategies:
1. **Automatic piercing**: Uses CDP to access shadow roots
2. **JavaScript execution**: Falls back to JS for complex cases
3. **Recursive search**: Handles nested shadow roots
4. **Component detection**: Identifies common component libraries

#### Example: Custom Web Components

```python
# Interacting with custom components
client.act_complex(
    "Type 'John' in the fancy-input component",
    handle_shadow=True
)

client.act_complex(
    "Select 'Premium' from custom-dropdown",
    handle_shadow=True
)

client.act_complex(
    "Click the submit button in form-component",
    handle_shadow=True
)
```

## Single Page Applications

### Problem
SPAs present unique challenges:
- Client-side routing
- No page reloads
- Dynamic component loading
- Code splitting
- Virtual DOM updates

### HER's Solution

```python
# Handles SPA navigation automatically
result = client.act_complex(
    "Click the Dashboard link",
    handle_spa=True  # Waits for route changes
)
```

#### SPA Detection Features:
- **Route monitoring**: Detects pushState/replaceState
- **Hash changes**: Monitors hash-based routing
- **DOM mutations**: Watches for significant DOM changes
- **Network activity**: Waits for API calls to complete
- **Component lifecycle**: Waits for components to mount

#### Supported Frameworks:
- ✅ React (React Router)
- ✅ Vue (Vue Router)
- ✅ Angular (Angular Router)
- ✅ Ember
- ✅ Svelte (SvelteKit)
- ✅ Next.js
- ✅ Nuxt.js

## Popups and Modals

### Problem
Popups and overlays interfere with automation:
- Cookie consent banners
- Newsletter popups
- Chat widgets
- Notification toasts
- Modal dialogs

### HER's Solution

```python
# Automatically dismisses common popups
client.act_complex(
    "Click main content",
    url="https://example.com"
    # Cookie banners and popups are auto-handled
)
```

#### Auto-Dismissed Elements:
- Cookie consent banners
- Newsletter signup popups
- Survey requests
- Chat bubbles
- Notification bars

#### Manual Modal Interaction:

```python
# Open modal
client.act_complex("Click Settings button")

# Interact with modal content
client.act_complex(
    "Toggle dark mode",
    handle_dynamic=True  # Modal might animate
)

# Close modal
client.act_complex("Click Save button")
```

## Best Practices

### 1. Use Complex Handlers for Modern Sites

```python
# For modern SPAs and dynamic sites
result = client.act_complex(
    step="Your action",
    handle_dynamic=True,
    handle_frames=True,
    handle_shadow=True,
    handle_spa=True
)
```

### 2. Combine Multiple Strategies

```python
# Handle everything at once
result = client.act_complex(
    "Complete the purchase",
    handle_dynamic=True,   # Dynamic content
    handle_frames=True,    # Payment iframe
    handle_shadow=True,    # Custom components
    handle_spa=True,       # SPA navigation
    handle_stale=True,     # Element re-rendering
    max_retries=5          # Important action
)
```

### 3. Adjust Timeouts for Slow Sites

```python
from her.handlers.complex_scenarios import WaitStrategy

# Custom strategy for slow sites
slow_site_strategy = WaitStrategy(
    timeout=60.0,          # 1 minute timeout
    poll_interval=1.0,     # Check every second
    stable_time=2.0        # Wait 2s for stability
)
```

### 4. Debug Complex Scenarios

```python
# Enable debug logging
client = HybridClient(log_level="DEBUG")

# See what's happening
result = client.act_complex(
    "Your action",
    handle_dynamic=True
)

print(f"Method used: {result['details']['method']}")
print(f"Retries needed: {result['details'].get('retries', 0)}")
```

## Performance Considerations

### 1. Selective Handler Usage

Don't enable all handlers if not needed:

```python
# For static sites
result = client.act("Simple click")  # Use basic method

# For complex sites
result = client.act_complex(  # Use only what's needed
    "Complex action",
    handle_dynamic=True,
    handle_frames=True
)
```

### 2. Caching and Session Reuse

```python
# Reuse session for multiple actions
with HybridClient() as client:
    # Session persists across actions
    client.act_complex("Action 1", url="https://example.com")
    client.act_complex("Action 2")  # Reuses page context
    client.act_complex("Action 3")  # No re-navigation
```

### 3. Parallel Processing

For multiple independent actions:

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

def process_item(item_name):
    with HybridClient() as client:
        return client.act_complex(f"Process {item_name}")

# Process multiple items in parallel
with ThreadPoolExecutor(max_workers=4) as executor:
    items = ["Item 1", "Item 2", "Item 3", "Item 4"]
    results = executor.map(process_item, items)
```

## Troubleshooting

### Element Not Found in Complex Page

```python
# Increase retries and timeouts
result = client.act_complex(
    "Find element",
    handle_dynamic=True,
    handle_frames=True,
    handle_shadow=True,
    max_retries=10
)
```

### Slow Page Loading

```python
# Custom wait strategy
from her.handlers.complex_scenarios import WaitStrategy

strategy = WaitStrategy(timeout=120.0)  # 2 minute timeout
```

### Debugging Frame Issues

```python
# Check which frame contains element
from her.handlers.complex_scenarios import FrameHandler

handler = FrameHandler(page)
frame = handler.find_frame_with_element("#target")
if frame:
    print(f"Element found in frame: {frame.url}")
```

## Advanced Examples

### Complete E-commerce Flow

```python
def complete_purchase(product_name, client):
    """Complete an e-commerce purchase flow."""
    
    # Search for product
    client.act_complex(
        f"Search for {product_name}",
        handle_dynamic=True
    )
    
    # Handle infinite scroll product list
    client.act_complex(
        "Click the first product",
        handle_dynamic=True
    )
    
    # SPA navigation to product page
    client.act_complex(
        "Add to cart",
        handle_spa=True,
        handle_stale=True
    )
    
    # Checkout (might be in iframe)
    client.act_complex(
        "Proceed to checkout",
        handle_frames=True,
        handle_spa=True
    )
    
    # Fill payment (shadow DOM components)
    client.act_complex(
        "Fill payment details",
        handle_frames=True,
        handle_shadow=True
    )
    
    # Complete (with retries for important action)
    return client.act_complex(
        "Complete purchase",
        handle_dynamic=True,
        max_retries=10
    )
```

### Data Extraction from Dynamic Table

```python
def extract_table_data(client, url):
    """Extract data from dynamically loaded table."""
    
    # Navigate and dismiss popups
    client.act_complex(
        "Navigate to data page",
        url=url
    )
    
    # Load all data (infinite scroll)
    client.act_complex(
        "Scroll to bottom of table",
        handle_dynamic=True
    )
    
    # Extract after all data loaded
    data = client.query("table rows")
    return data
```

## Summary

HER's complex scenario handling makes it ideal for:

✅ **Modern SPAs**: React, Vue, Angular applications
✅ **E-commerce Sites**: Dynamic catalogs, complex checkouts
✅ **Banking Applications**: Secure iframes, multiple validations
✅ **Social Media**: Infinite scroll, real-time updates
✅ **Enterprise Apps**: Complex forms, nested components
✅ **Media Sites**: Lazy-loaded content, video players
✅ **SaaS Platforms**: Dashboard, real-time data

The framework handles these scenarios automatically, requiring minimal configuration while providing maximum reliability.