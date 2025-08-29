#!/usr/bin/env python3
"""
Comprehensive testing of HER with properly mocked DOM elements.
Tests XPath generation, caching, and E2E flows.
"""

import json
import time
import os
import shutil
from typing import Dict, List, Any
from unittest.mock import Mock, MagicMock, patch
from dataclasses import dataclass

@dataclass
class MockElement:
    """Mock DOM element for testing."""
    tag: str
    text: str = ""
    attrs: Dict[str, str] = None
    children: List = None
    
    def to_descriptor(self) -> Dict[str, Any]:
        """Convert to HER descriptor format."""
        return {
            "tag": self.tag,
            "text": self.text or "",
            "attrs": self.attrs or {},
            "xpath": f"//{self.tag}",
            "css": f"{self.tag}",
            "visible": True,
            "clickable": self.tag in ["button", "a", "input"],
            "role": self.attrs.get("role", "") if self.attrs else "",
            "aria_label": self.attrs.get("aria-label", "") if self.attrs else ""
        }


def create_realistic_dom(scenario: str) -> List[Dict[str, Any]]:
    """Create realistic DOM descriptors for different scenarios."""
    
    scenarios = {
        "login_form": [
            MockElement("h1", "Login").to_descriptor(),
            MockElement("label", "Email", {"for": "email"}).to_descriptor(),
            MockElement("input", "", {"type": "email", "id": "email", "placeholder": "Enter email"}).to_descriptor(),
            MockElement("label", "Password", {"for": "password"}).to_descriptor(),
            MockElement("input", "", {"type": "password", "id": "password"}).to_descriptor(),
            MockElement("button", "Sign In", {"type": "submit", "class": "btn-primary"}).to_descriptor(),
            MockElement("a", "Forgot Password?", {"href": "#forgot"}).to_descriptor(),
        ],
        
        "popup_overlay": [
            # Main content (occluded)
            MockElement("button", "Open Account", {"id": "main-btn", "class": "btn"}).to_descriptor(),
            # Cookie banner (overlay)
            MockElement("div", "", {"class": "cookie-banner", "style": "z-index: 9999"}).to_descriptor(),
            MockElement("h2", "We use cookies").to_descriptor(),
            MockElement("button", "Accept All", {"id": "accept-cookies", "class": "cookie-btn"}).to_descriptor(),
            MockElement("button", "Reject", {"id": "reject-cookies"}).to_descriptor(),
            MockElement("button", "×", {"class": "close-modal", "aria-label": "Close"}).to_descriptor(),
        ],
        
        "nested_shadow": [
            # Regular DOM
            MockElement("div", "", {"class": "container"}).to_descriptor(),
            MockElement("h1", "Page Title").to_descriptor(),
            # Shadow DOM elements (marked with special attribute)
            MockElement("button", "Shadow Button", {"data-shadow": "true", "id": "shadow-btn"}).to_descriptor(),
            MockElement("input", "", {"data-shadow": "true", "placeholder": "Shadow input"}).to_descriptor(),
        ],
        
        "iframe_content": [
            # Main frame
            MockElement("h1", "Main Page").to_descriptor(),
            MockElement("iframe", "", {"id": "payment-frame", "src": "payment.html"}).to_descriptor(),
            # Frame content (marked)
            MockElement("input", "", {"data-frame": "payment-frame", "name": "card", "placeholder": "Card Number"}).to_descriptor(),
            MockElement("input", "", {"data-frame": "payment-frame", "name": "cvv", "placeholder": "CVV"}).to_descriptor(),
            MockElement("button", "Pay Now", {"data-frame": "payment-frame", "type": "submit"}).to_descriptor(),
        ],
        
        "dynamic_spa": [
            # Navigation
            MockElement("a", "Home", {"href": "#home", "class": "nav-link active"}).to_descriptor(),
            MockElement("a", "Profile", {"href": "#profile", "class": "nav-link"}).to_descriptor(),
            MockElement("a", "Settings", {"href": "#settings", "class": "nav-link"}).to_descriptor(),
            # Dynamic content
            MockElement("div", "", {"id": "content", "data-page": "home"}).to_descriptor(),
            MockElement("h1", "Welcome").to_descriptor(),
            MockElement("button", "Get Started", {"class": "cta", "data-dynamic": "true"}).to_descriptor(),
        ],
        
        "complex_form": [
            MockElement("form", "", {"id": "registration"}).to_descriptor(),
            MockElement("fieldset", "").to_descriptor(),
            MockElement("legend", "Personal Info").to_descriptor(),
            MockElement("input", "", {"name": "firstname", "placeholder": "First Name", "required": "true"}).to_descriptor(),
            MockElement("input", "", {"name": "lastname", "placeholder": "Last Name", "required": "true"}).to_descriptor(),
            MockElement("input", "", {"type": "email", "name": "email", "placeholder": "Email"}).to_descriptor(),
            MockElement("select", "", {"name": "country"}).to_descriptor(),
            MockElement("option", "United States", {"value": "us"}).to_descriptor(),
            MockElement("option", "United Kingdom", {"value": "uk", "selected": "true"}).to_descriptor(),
            MockElement("input", "", {"type": "radio", "name": "gender", "value": "male", "id": "male"}).to_descriptor(),
            MockElement("label", "Male", {"for": "male"}).to_descriptor(),
            MockElement("input", "", {"type": "radio", "name": "gender", "value": "female", "id": "female", "checked": "true"}).to_descriptor(),
            MockElement("label", "Female", {"for": "female"}).to_descriptor(),
            MockElement("button", "Register", {"type": "submit", "disabled": "true"}).to_descriptor(),
        ],
        
        "loading_state": [
            MockElement("div", "Loading...", {"class": "spinner", "style": "display: block"}).to_descriptor(),
            MockElement("div", "", {"class": "skeleton-loader"}).to_descriptor(),
            MockElement("button", "Submit", {"id": "submit", "disabled": "true", "style": "display: none"}).to_descriptor(),
        ],
    }
    
    return scenarios.get(scenario, [])


def test_xpath_generation():
    """Test how HER generates XPaths for different elements."""
    print("\n" + "="*60)
    print("Testing XPath Generation")
    print("="*60)
    
    from src.her.cli_api import HybridClient
    from src.her.locator.simple_synthesize import LocatorSynthesizer
    
    # Test elements
    test_elements = [
        {
            "tag": "button",
            "text": "Submit Form",
            "attrs": {"id": "submit-btn", "class": "btn btn-primary", "type": "submit"}
        },
        {
            "tag": "input",
            "text": "",
            "attrs": {"name": "email", "type": "email", "placeholder": "Enter your email"}
        },
        {
            "tag": "a",
            "text": "Click here",
            "attrs": {"href": "/page", "class": "link", "data-test": "link-1"}
        },
        {
            "tag": "div",
            "text": "Important message",
            "attrs": {"role": "alert", "aria-live": "polite", "class": "alert-box"}
        }
    ]
    
    synthesizer = LocatorSynthesizer()
    
    for elem in test_elements:
        print(f"\n📌 Element: <{elem['tag']}> '{elem.get('text', '')[:20]}...'")
        print(f"   Attributes: {elem['attrs']}")
        
        locators = synthesizer.synthesize(elem)
        print(f"   Generated {len(locators)} locators:")
        
        for loc in locators[:5]:  # Show first 5
            if isinstance(loc, dict):
                strategy = loc.get("strategy", "unknown")
                selector = loc.get("selector", "")
                print(f"      [{strategy}] {selector[:60]}...")
            else:
                print(f"      {str(loc)[:70]}...")


def test_cold_start_and_caching():
    """Test cold start behavior and caching effectiveness."""
    print("\n" + "="*60)
    print("Testing Cold Start & Caching")
    print("="*60)
    
    from src.her.cli_api import HybridClient
    
    # Clear cache
    cache_dir = ".cache"
    if os.path.exists(cache_dir):
        shutil.rmtree(cache_dir)
        print("✅ Cleared existing cache")
    
    # Create mock page with complex form
    mock_page = Mock()
    mock_page.url = "https://test.example.com/form"
    
    def mock_evaluate(*args, **kwargs):
        return []
    
    mock_page.evaluate = Mock(side_effect=mock_evaluate)
    mock_page.query_selector = Mock(return_value=None)
    mock_page.frames = []
    
    # Mock capture_snapshot to return our test DOM
    test_dom = create_realistic_dom("complex_form")
    
    with patch('src.her.bridge.snapshot.capture_snapshot') as mock_capture:
        mock_capture.return_value = (test_dom, "test_hash_12345")
        
        # Cold start
        print("\n🧊 Cold Start:")
        client1 = HybridClient(enable_cache=True)
        
        start = time.time()
        result1 = client1.query("first name input", url=mock_page.url)
        cold_time = time.time() - start
        
        print(f"   Time: {cold_time:.3f}s")
        print(f"   Results: {len(result1) if isinstance(result1, list) else 0} elements")
        
        if isinstance(result1, list) and result1:
            for i, elem in enumerate(result1[:3]):
                if isinstance(elem, dict):
                    print(f"   {i+1}. {elem.get('selector', 'N/A')[:50]}...")
        
        client1.close()
        
        # Warm cache
        print("\n🔥 Warm Cache:")
        client2 = HybridClient(enable_cache=True)
        
        start = time.time()
        result2 = client2.query("first name input", url=mock_page.url)
        warm_time = time.time() - start
        
        print(f"   Time: {warm_time:.3f}s")
        print(f"   Results: {len(result2) if isinstance(result2, list) else 0} elements")
        
        if cold_time > 0 and warm_time > 0:
            speedup = cold_time / warm_time
            print(f"\n⚡ Speedup: {speedup:.1f}x faster with cache")
        
        # Check what's cached
        if os.path.exists(cache_dir):
            files = os.listdir(cache_dir)
            print(f"\n📁 Cache contents: {len(files)} files")
            total_size = sum(os.path.getsize(os.path.join(cache_dir, f)) for f in files)
            print(f"   Total size: {total_size / 1024:.1f} KB")
        
        client2.close()


def test_e2e_flows():
    """Test complete E2E flows."""
    print("\n" + "="*60)
    print("Testing E2E Flows")
    print("="*60)
    
    from src.her.cli_api import HybridClient
    
    scenarios = [
        ("Login Flow", "login_form", [
            ("query", "email input field"),
            ("act", "type user@example.com in email field"),
            ("query", "password input"),
            ("act", "type password123 in password field"),
            ("query", "sign in button"),
            ("act", "click sign in button")
        ]),
        ("Popup Handling", "popup_overlay", [
            ("query", "accept cookies button"),
            ("act", "click accept all"),
            ("query", "close modal button"),
            ("act", "click close button")
        ]),
        ("Form Submission", "complex_form", [
            ("query", "first name input"),
            ("act", "type John in first name"),
            ("query", "email field"),
            ("act", "select United Kingdom from country"),
            ("query", "register button"),
            ("act", "click register")
        ])
    ]
    
    client = HybridClient(enable_self_heal=True)
    
    for scenario_name, dom_type, actions in scenarios:
        print(f"\n📋 {scenario_name}:")
        
        # Mock page with scenario DOM
        mock_page = Mock()
        mock_page.url = f"https://test.example.com/{dom_type}"
        test_dom = create_realistic_dom(dom_type)
        
        with patch('src.her.bridge.snapshot.capture_snapshot') as mock_capture:
            mock_capture.return_value = (test_dom, f"hash_{dom_type}")
            
            for action_type, command in actions:
                print(f"   → {command}")
                
                try:
                    if action_type == "query":
                        result = client.query(command, url=mock_page.url)
                        count = len(result) if isinstance(result, list) else 0
                        print(f"     ✅ Found {count} elements")
                    else:  # act
                        with patch.object(client.executor, 'page', mock_page):
                            result = client.act(command, url=mock_page.url)
                            status = result.get("status", "unknown") if isinstance(result, dict) else "error"
                            print(f"     ✅ Action: {status}")
                except Exception as e:
                    print(f"     ❌ Error: {str(e)[:50]}...")
    
    client.close()


def test_self_healing():
    """Test self-healing capabilities."""
    print("\n" + "="*60)
    print("Testing Self-Healing")
    print("="*60)
    
    from src.her.cli_api import HybridClient
    from src.her.recovery.enhanced_self_heal import EnhancedSelfHeal
    
    # Test locators that need healing
    test_cases = [
        ("//button[text()='Submitt']", "Typo in text"),  # Typo
        ("//input[@id='emial']", "Typo in ID"),  # Wrong ID
        ("//div[@class='btnn']", "Wrong class"),  # Wrong class
        ("//button[contains(text(),'Sgn')]", "Partial text typo"),  # Partial typo
    ]
    
    healer = EnhancedSelfHeal()
    
    for locator, description in test_cases:
        print(f"\n🔧 {description}")
        print(f"   Original: {locator}")
        
        # Get healing suggestions
        alternatives = healer.heal(locator, max_alternatives=3)
        
        if alternatives:
            print(f"   Healed ({len(alternatives)} alternatives):")
            for alt in alternatives[:3]:
                print(f"      - {alt}")
        else:
            print("   No healing suggestions")


def main():
    """Run all comprehensive tests."""
    print("🚀 HER Framework - Comprehensive Testing")
    print("=" * 60)
    
    # Run all test suites
    test_xpath_generation()
    test_cold_start_and_caching()
    test_e2e_flows()
    test_self_healing()
    
    print("\n" + "="*60)
    print("✅ All Comprehensive Tests Completed")
    print("="*60)


if __name__ == "__main__":
    main()