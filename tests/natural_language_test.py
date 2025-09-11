"""
Natural Language Test Examples
Users can modify these tests by simply changing the English step descriptions.
No technical knowledge required!
"""

import pytest
from src.her.testing.natural_test_runner import run_natural_test


def test_verizon_phone_shopping():
    """Test shopping for phones on Verizon website using natural language."""
    
    # Define the test steps in plain English
    steps = [
        "Go to Verizon website",
        "Click on Phones",
        "Click on Apple filter",
        "Click on iPhone",
        "Verify we are on iPhone product page"
    ]
    
    # Run the test
    result = run_natural_test(
        test_name="Verizon Phone Shopping",
        steps=steps,
        start_url="https://www.verizon.com/",
        headless=True
    )
    
    # Assertions
    assert result['success'], f"Test failed: {result['message']}"
    assert result['successful_steps'] == len(steps), f"Only {result['successful_steps']}/{len(steps)} steps succeeded"
    assert "iphone" in result['final_url'].lower(), f"Expected iPhone page, got: {result['final_url']}"


def test_verizon_search():
    """Test search functionality on Verizon website."""
    
    steps = [
        "Go to Verizon website",
        "Click on search box",
        "Type iPhone 16",
        "Press Enter",
        "Verify search results page loaded"
    ]
    
    result = run_natural_test(
        test_name="Verizon Search",
        steps=steps,
        start_url="https://www.verizon.com/",
        headless=True
    )
    
    assert result['success'], f"Test failed: {result['message']}"
    assert result['successful_steps'] == len(steps), f"Only {result['successful_steps']}/{len(steps)} steps succeeded"


def test_verizon_navigation():
    """Test navigation through Verizon menu."""
    
    steps = [
        "Go to Verizon website",
        "Click on menu button",
        "Click on plans",
        "Verify plans page loaded"
    ]
    
    result = run_natural_test(
        test_name="Verizon Navigation",
        steps=steps,
        start_url="https://www.verizon.com/",
        headless=True
    )
    
    assert result['success'], f"Test failed: {result['message']}"
    assert result['successful_steps'] == len(steps), f"Only {result['successful_steps']}/{len(steps)} steps succeeded"


def test_amazon_product_search():
    """Test searching for products on Amazon."""
    
    steps = [
        "Go to Amazon website",
        "Click on search box",
        "Type laptop",
        "Press Enter",
        "Click on first product",
        "Verify product page loaded"
    ]
    
    result = run_natural_test(
        test_name="Amazon Product Search",
        steps=steps,
        start_url="https://www.amazon.com/",
        headless=True
    )
    
    assert result['success'], f"Test failed: {result['message']}"
    assert result['successful_steps'] == len(steps), f"Only {result['successful_steps']}/{len(steps)} steps succeeded"


def test_google_search():
    """Test Google search functionality."""
    
    steps = [
        "Go to Google",
        "Click on search box",
        "Type Python programming",
        "Press Enter",
        "Verify search results loaded"
    ]
    
    result = run_natural_test(
        test_name="Google Search",
        steps=steps,
        start_url="https://www.google.com/",
        headless=True
    )
    
    assert result['success'], f"Test failed: {result['message']}"
    assert result['successful_steps'] == len(steps), f"Only {result['successful_steps']}/{len(steps)} steps succeeded"


# Example of how users can create their own tests
def test_custom_business_flow():
    """Example: Users can create their own business flow tests."""
    
    # Users just need to describe what they want to do in English
    steps = [
        "Go to your website",
        "Click on login button",
        "Type your username",
        "Type your password", 
        "Click on submit button",
        "Verify dashboard loaded"
    ]
    
    result = run_natural_test(
        test_name="Custom Business Flow",
        steps=steps,
        start_url="https://your-website.com/",  # Users change this
        headless=True
    )
    
    assert result['success'], f"Test failed: {result['message']}"