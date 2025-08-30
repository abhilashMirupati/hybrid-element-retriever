#!/usr/bin/env python3
"""
Comprehensive mock HTML testing for HER framework.
Tests complex edge cases without requiring a real browser.
"""

import json
import time
from typing import Dict, List, Any
from unittest.mock import Mock, MagicMock, patch

# Complex HTML scenarios for testing
MOCK_HTML_SCENARIOS = {
    "loading_state": {
        "html": """
        <html>
            <body>
                <div class="loading-spinner" style="display: block;">Loading...</div>
                <div class="content" style="display: none;">
                    <button id="submit" disabled>Submit</button>
                    <div class="skeleton-loader">████████</div>
                </div>
                <script>
                    setTimeout(() => {
                        document.querySelector('.loading-spinner').style.display = 'none';
                        document.querySelector('.content').style.display = 'block';
                        document.querySelector('#submit').disabled = false;
                    }, 2000);
                </script>
            </body>
        </html>
        """,
        "elements": [
            {"tag": "div", "class": "loading-spinner", "text": "Loading...", "visible": True},
            {"tag": "button", "id": "submit", "disabled": True, "visible": False}
        ]
    },
    
    "popup_overlay": {
        "html": """
        <html>
            <body>
                <div class="main-content">
                    <button id="login">Login</button>
                    <input type="email" id="email" />
                </div>
                <div class="modal-overlay" style="position: fixed; z-index: 9999;">
                    <div class="modal">
                        <button class="close-modal">×</button>
                        <h2>Cookie Notice</h2>
                        <button id="accept-cookies">Accept All</button>
                    </div>
                </div>
                <div class="toast-notification" style="position: absolute; z-index: 10000;">
                    <span>New message received</span>
                    <button class="dismiss">Dismiss</button>
                </div>
            </body>
        </html>
        """,
        "elements": [
            {"tag": "button", "id": "login", "text": "Login", "occluded": True},
            {"tag": "button", "class": "close-modal", "text": "×", "z_index": 9999},
            {"tag": "button", "class": "dismiss", "text": "Dismiss", "z_index": 10000}
        ]
    },
    
    "nested_shadow_dom": {
        "html": """
        <html>
            <body>
                <custom-element>
                    #shadow-root (open)
                        <div class="shadow-container">
                            <nested-component>
                                #shadow-root (open)
                                    <button id="deep-button">Click Me</button>
                                    <input type="text" placeholder="Shadow input" />
                                #shadow-root
                            </nested-component>
                        </div>
                    #shadow-root
                </custom-element>
                <regular-button>Normal Button</regular-button>
            </body>
        </html>
        """,
        "elements": [
            {"tag": "button", "id": "deep-button", "text": "Click Me", "shadow_path": ["custom-element", "nested-component"]},
            {"tag": "input", "placeholder": "Shadow input", "shadow_path": ["custom-element", "nested-component"]},
            {"tag": "regular-button", "text": "Normal Button", "shadow_path": []}
        ]
    },
    
    "iframe_nested": {
        "html": """
        <html>
            <body>
                <h1>Main Page</h1>
                <iframe id="frame1" src="page1.html">
                    <html>
                        <body>
                            <h2>Frame 1</h2>
                            <button id="frame1-btn">Frame 1 Button</button>
                            <iframe id="frame2" src="page2.html">
                                <html>
                                    <body>
                                        <h3>Nested Frame 2</h3>
                                        <input id="nested-input" type="text" />
                                        <button>Deeply Nested Button</button>
                                    </body>
                                </html>
                            </iframe>
                        </body>
                    </html>
                </iframe>
                <iframe id="frame3" src="page3.html">
                    <html>
                        <body>
                            <form id="payment-form">
                                <input type="text" name="card" placeholder="Card Number" />
                                <button type="submit">Pay Now</button>
                            </form>
                        </body>
                    </html>
                </iframe>
            </body>
        </html>
        """,
        "elements": [
            {"tag": "h1", "text": "Main Page", "frame_path": []},
            {"tag": "button", "id": "frame1-btn", "text": "Frame 1 Button", "frame_path": ["frame1"]},
            {"tag": "input", "id": "nested-input", "frame_path": ["frame1", "frame2"]},
            {"tag": "button", "text": "Pay Now", "frame_path": ["frame3"]}
        ]
    },
    
    "dynamic_spa": {
        "html": """
        <html>
            <body>
                <div id="app">
                    <nav>
                        <a href="#home" class="nav-link active">Home</a>
                        <a href="#profile" class="nav-link">Profile</a>
                        <a href="#settings" class="nav-link">Settings</a>
                    </nav>
                    <div id="content">
                        <!-- Content changes based on route -->
                        <div class="page" data-page="home">
                            <h1>Welcome</h1>
                            <button class="cta">Get Started</button>
                        </div>
                    </div>
                </div>
                <script>
                    window.addEventListener('hashchange', () => {
                        // SPA route change simulation
                        document.querySelector('#content').innerHTML = '<div>Loading...</div>';
                        setTimeout(() => {
                            // New content loaded
                        }, 100);
                    });
                </script>
            </body>
        </html>
        """,
        "elements": [
            {"tag": "a", "class": "nav-link active", "text": "Home", "href": "#home"},
            {"tag": "button", "class": "cta", "text": "Get Started", "dynamic": True}
        ]
    },
    
    "complex_form": {
        "html": """
        <html>
            <body>
                <form id="registration">
                    <fieldset>
                        <legend>Personal Info</legend>
                        <input type="text" name="firstname" placeholder="First Name" required />
                        <input type="text" name="lastname" placeholder="Last Name" required />
                    </fieldset>
                    <fieldset disabled>
                        <legend>Account Details</legend>
                        <input type="email" name="email" placeholder="Email" />
                        <input type="password" name="password" placeholder="Password" />
                    </fieldset>
                    <select name="country" multiple>
                        <option value="us">United States</option>
                        <option value="uk" selected>United Kingdom</option>
                        <option value="ca">Canada</option>
                    </select>
                    <div class="radio-group">
                        <input type="radio" id="male" name="gender" value="male" />
                        <label for="male">Male</label>
                        <input type="radio" id="female" name="gender" value="female" checked />
                        <label for="female">Female</label>
                    </div>
                    <button type="submit" disabled>Register</button>
                </form>
            </body>
        </html>
        """,
        "elements": [
            {"tag": "input", "name": "firstname", "placeholder": "First Name", "required": True},
            {"tag": "input", "name": "email", "disabled": True, "fieldset_disabled": True},
            {"tag": "option", "value": "uk", "selected": True, "text": "United Kingdom"},
            {"tag": "input", "type": "radio", "id": "female", "checked": True}
        ]
    },
    
    "lazy_loaded": {
        "html": """
        <html>
            <body>
                <div class="container">
                    <div class="visible-content">
                        <h1>Above the fold</h1>
                        <button id="visible-btn">Visible Button</button>
                    </div>
                    <div class="lazy-content" data-src="lazy.html" style="min-height: 2000px;">
                        <!-- Content loads when scrolled into view -->
                        <div class="placeholder">Scroll to load...</div>
                    </div>
                    <div class="infinite-scroll">
                        <div class="item">Item 1</div>
                        <div class="item">Item 2</div>
                        <!-- More items load on scroll -->
                        <div class="loader" style="display: none;">Loading more...</div>
                    </div>
                </div>
            </body>
        </html>
        """,
        "elements": [
            {"tag": "button", "id": "visible-btn", "text": "Visible Button", "in_viewport": True},
            {"tag": "div", "class": "placeholder", "text": "Scroll to load...", "in_viewport": False},
            {"tag": "div", "class": "loader", "visible": False, "lazy_load": True}
        ]
    },
    
    "accessibility_rich": {
        "html": """
        <html>
            <body>
                <nav role="navigation" aria-label="Main">
                    <ul>
                        <li><a href="#" aria-current="page">Home</a></li>
                        <li><a href="#">About</a></li>
                    </ul>
                </nav>
                <main role="main">
                    <h1 id="page-title">Welcome</h1>
                    <button aria-label="Close dialog" aria-pressed="false">
                        <span aria-hidden="true">×</span>
                    </button>
                    <div role="alert" aria-live="polite">
                        Important message
                    </div>
                    <input type="text" aria-describedby="help-text" aria-invalid="true" />
                    <span id="help-text">Enter valid email</span>
                </main>
            </body>
        </html>
        """,
        "elements": [
            {"tag": "a", "text": "Home", "aria_current": "page"},
            {"tag": "button", "aria_label": "Close dialog", "aria_pressed": "false"},
            {"tag": "div", "role": "alert", "aria_live": "polite", "text": "Important message"},
            {"tag": "input", "aria_invalid": "true", "aria_describedby": "help-text"}
        ]
    }
}


def create_mock_page(scenario_name: str) -> Mock:
    """Create a mock page object with the specified scenario."""
    scenario = MOCK_HTML_SCENARIOS[scenario_name]
    
    mock_page = Mock()
    mock_page.url = f"https://test.example.com/{scenario_name}"
    mock_page.content = scenario["html"]
    
    # Mock evaluate for DOM snapshot
    def mock_evaluate(script, *args, **kwargs):
        if "document.documentElement.outerHTML" in str(script):
            return scenario["html"]
        elif "getComputedStyle" in str(script):
            return {"display": "block", "visibility": "visible"}
        return scenario.get("elements", [])
    
    mock_page.evaluate = Mock(side_effect=mock_evaluate)
    
    # Mock query_selector methods
    mock_page.query_selector = Mock(return_value=Mock())
    mock_page.query_selector_all = Mock(return_value=[Mock() for _ in scenario.get("elements", [])])
    
    # Mock frame handling
    mock_frame = Mock()
    mock_frame.query_selector = Mock(return_value=Mock())
    mock_page.frames = [mock_frame]
    mock_page.main_frame = mock_frame
    
    return mock_page


def test_her_with_scenario(scenario_name: str):
    """Test HER with a specific scenario."""
    print(f"\n{'='*60}")
    print(f"Testing Scenario: {scenario_name}")
    print('='*60)
    
    from her.cli_api import HybridClient
    from her.bridge.snapshot import capture_snapshot
    
    # Create mock page
    mock_page = create_mock_page(scenario_name)
    scenario = MOCK_HTML_SCENARIOS[scenario_name]
    
    # Initialize HER client
    client = HybridClient(headless=True)
    
    # Mock the executor's page
    with patch.object(client.executor, 'page', mock_page):
        # Test different queries for this scenario
        test_queries = get_test_queries_for_scenario(scenario_name)
        
        for query in test_queries:
            print(f"\n🔍 Query: '{query}'")
            
            try:
                # Capture what HER would see
                descriptors, dom_hash = capture_snapshot(mock_page)
                print(f"   📊 Captured {len(descriptors)} elements")
                print(f"   🔑 DOM Hash: {dom_hash[:16]}...")
                
                # Test query
                result = client.query(query, url=mock_page.url)
                
                if isinstance(result, list):
                    print(f"   ✅ Found {len(result)} matches")
                    for i, elem in enumerate(result[:3]):  # Show first 3
                        if isinstance(elem, dict):
                            selector = elem.get('selector', 'N/A')
                            score = elem.get('score', 0)
                            print(f"      {i+1}. {selector[:50]}... (score: {score:.2f})")
                else:
                    print(f"   ℹ️ Result: {result}")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
    
    client.close()
    print(f"\n✅ Scenario '{scenario_name}' completed")


def get_test_queries_for_scenario(scenario_name: str) -> List[str]:
    """Get relevant test queries for each scenario."""
    queries = {
        "loading_state": [
            "submit button",
            "loading spinner",
            "disabled button"
        ],
        "popup_overlay": [
            "login button",
            "close modal button",
            "accept cookies",
            "dismiss notification"
        ],
        "nested_shadow_dom": [
            "deep button in shadow",
            "shadow input field",
            "click me button"
        ],
        "iframe_nested": [
            "frame 1 button",
            "nested input",
            "pay now button",
            "card number input"
        ],
        "dynamic_spa": [
            "home navigation link",
            "get started button",
            "active nav link"
        ],
        "complex_form": [
            "first name input",
            "email field",
            "register button",
            "female radio button"
        ],
        "lazy_loaded": [
            "visible button",
            "scroll to load",
            "loading more"
        ],
        "accessibility_rich": [
            "close dialog button",
            "home link with current page",
            "alert message",
            "invalid input field"
        ]
    }
    return queries.get(scenario_name, ["button", "input", "link"])


def test_cold_start_flow():
    """Test cold start behavior and caching."""
    print("\n" + "="*60)
    print("Testing Cold Start Flow")
    print("="*60)
    
    from her.cli_api import HybridClient
# import os
    import shutil
    
    # Clear any existing cache
    cache_dir = ".cache"
    if os.path.exists(cache_dir):
        shutil.rmtree(cache_dir)
        print("✅ Cleared existing cache")
    
    # First run - cold start
    print("\n📦 Cold Start Run:")
    client1 = HybridClient(enable_cache=True)
    
    mock_page = create_mock_page("complex_form")
    with patch.object(client1.executor, 'page', mock_page):
        start_time = time.time()
        result1 = client1.query("first name input", url=mock_page.url)
        cold_time = time.time() - start_time
        print(f"   ⏱️ Cold start time: {cold_time:.3f}s")
        print(f"   📊 Results: {len(result1) if isinstance(result1, list) else 0} elements")
    
    client1.close()
    
    # Second run - warm cache
    print("\n🔥 Warm Cache Run:")
    client2 = HybridClient(enable_cache=True)
    
    with patch.object(client2.executor, 'page', mock_page):
        start_time = time.time()
        result2 = client2.query("first name input", url=mock_page.url)
        warm_time = time.time() - start_time
        print(f"   ⏱️ Warm cache time: {warm_time:.3f}s")
        print(f"   📊 Results: {len(result2) if isinstance(result2, list) else 0} elements")
    
    # Check cache statistics
    if os.path.exists(cache_dir):
        cache_files = os.listdir(cache_dir)
        print(f"\n📁 Cache Status:")
        print(f"   Files created: {len(cache_files)}")
        for f in cache_files[:5]:  # Show first 5
            size = os.path.getsize('ignored'
            print(f"   - {f}: {size} bytes")
    
    # Performance comparison
    if cold_time > 0 and warm_time > 0:
        speedup = cold_time / warm_time
        print(f"\n⚡ Performance: {speedup:.1f}x faster with cache")
    
    client2.close()


def test_all_e2e_flows():
    """Test all E2E functionalities."""
    print("\n" + "="*60)
    print("Testing All E2E Flows")
    print("="*60)
    
    from her.cli_api import HybridClient
    
    flows = [
        ("Query Flow", "click submit button"),
        ("Action Flow", "type hello in input field"),
        ("Complex Query", "button with aria-label close"),
        ("XPath Generation", "first input in form"),
        ("Self-Healing", "submit btn")  # Intentional typo to test healing
    ]
    
    client = HybridClient(enable_self_heal=True)
    mock_page = create_mock_page("complex_form")
    
    with patch.object(client.executor, 'page', mock_page):
        for flow_name, command in flows:
            print(f"\n🔄 {flow_name}: '{command}'")
            try:
                if "type" in command or "click" in command:
                    # Test action flow
                    result = client.act(command, url=mock_page.url)
                    print(f"   ✅ Action result: {result.get('status', 'unknown')}")
                else:
                    # Test query flow
                    result = client.query(command, url=mock_page.url)
                    print(f"   ✅ Query found: {len(result) if isinstance(result, list) else 0} elements")
            except Exception as e:
                print(f"   ❌ Error: {e}")
    
    client.close()


def main():
    """Run all tests."""
    print("🚀 HER Framework - Comprehensive Mock Testing")
    print("=" * 60)
    
    # Test all scenarios
    for scenario_name in MOCK_HTML_SCENARIOS.keys():
        test_her_with_scenario(scenario_name)
    
    # Test cold start
    test_cold_start_flow()
    
    # Test E2E flows
    test_all_e2e_flows()
    
    print("\n" + "="*60)
    print("✅ All Mock Tests Completed")
    print("="*60)


if __name__ == "__main__":
    main()