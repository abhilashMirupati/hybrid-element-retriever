#!/usr/bin/env python3
"""
Universal test framework for HER - demonstrates universal capabilities
"""

import pytest
import os

try:
    from playwright.sync_api import sync_playwright  # noqa: F401
    PLAYWRIGHT_AVAILABLE = True
except Exception:
    PLAYWRIGHT_AVAILABLE = False


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not available")
@pytest.mark.skipif(os.getenv("HER_E2E") != "1", reason="Set HER_E2E=1 to run live e2e test")
@pytest.mark.timeout(180)
def test_verizon_ecommerce_flow():
    """Test Verizon e-commerce flow - demonstrates e-commerce automation"""
    from her.runner import run_steps

    steps = [
        "Open https://www.verizon.com/",
        "Click on Phones btn in top",
        "Select Apple filter", 
        "Select Apple iPhone 16 Pro",
        "Validate it landed on https://www.verizon.com/smartphones/apple-iphone-16-pro/",
    ]

    run_steps(steps, headless=True)


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not available")
@pytest.mark.skipif(os.getenv("HER_E2E") != "1", reason="Set HER_E2E=1 to run live e2e test")
@pytest.mark.timeout(180)
def test_google_search_flow():
    """Test Google search flow - demonstrates search automation"""
    from her.runner import run_steps

    steps = [
        "Open https://www.google.com/",
        "Type 'playwright automation' in search box",
        "Click on Search button",
        "Validate page contains 'playwright' text",
    ]

    run_steps(steps, headless=True)


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not available")
@pytest.mark.skipif(os.getenv("HER_E2E") != "1", reason="Set HER_E2E=1 to run live e2e test")
@pytest.mark.timeout(180)
def test_github_navigation_flow():
    """Test GitHub navigation flow - demonstrates navigation automation"""
    from her.runner import run_steps

    steps = [
        "Open https://github.com/",
        "Click on Sign in button",
        "Validate page contains 'Sign in to GitHub' text",
    ]

    run_steps(steps, headless=True)


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not available")
@pytest.mark.skipif(os.getenv("HER_E2E") != "1", reason="Set HER_E2E=1 to run live e2e test")
@pytest.mark.timeout(180)
def test_amazon_search_flow():
    """Test Amazon search flow - demonstrates e-commerce search automation"""
    from her.runner import run_steps

    steps = [
        "Open https://www.amazon.com/",
        "Type 'laptop' in search box",
        "Click on Search button",
        "Validate page contains 'laptop' text",
    ]

    run_steps(steps, headless=True)


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not available")
@pytest.mark.skipif(os.getenv("HER_E2E") != "1", reason="Set HER_E2E=1 to run live e2e test")
@pytest.mark.timeout(180)
def test_universal_form_filling():
    """Test universal form filling - demonstrates form automation"""
    from her.runner import run_steps

    steps = [
        "Open https://httpbin.org/forms/post",
        "Type 'John Doe' in name field",
        "Type 'john@example.com' in email field",
        "Type '123 Main St' in address field",
        "Click on Submit button",
        "Validate page contains 'John Doe' text",
    ]

    run_steps(steps, headless=True)


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not available")
@pytest.mark.skipif(os.getenv("HER_E2E") != "1", reason="Set HER_E2E=1 to run live e2e test")
@pytest.mark.timeout(180)
def test_universal_button_clicking():
    """Test universal button clicking - demonstrates button automation"""
    from her.runner import run_steps

    steps = [
        "Open https://example.com/",
        "Click on More information link",
        "Validate page contains 'Example Domain' text",
    ]

    run_steps(steps, headless=True)