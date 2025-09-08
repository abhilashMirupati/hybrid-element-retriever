import pytest

try:
    from playwright.sync_api import sync_playwright  # noqa: F401
    PLAYWRIGHT_AVAILABLE = True
except Exception:
    PLAYWRIGHT_AVAILABLE = False


import os


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not available")
@pytest.mark.skipif(os.getenv("HER_E2E") != "1", reason="Set HER_E2E=1 to run live e2e test")
@pytest.mark.timeout(180)
def test_verizon_flow():
    from her.runner import run_steps

    steps = [
        "Open https://www.verizon.com/",
        "Click on featured smartphones menu list in top",
        "Select Apple filter",
        "Select iPhone 16 Pro on us: Buy now",
        "Validate it landed on https://www.verizon.com/smartphones/apple-iphone-16-pro/",
        "Select Desert Titanium",
        "Select 512 GB",
        "Click Add to Cart",
        "Validate 'Added to your cart'",
    ]

    run_steps(steps, headless=True)