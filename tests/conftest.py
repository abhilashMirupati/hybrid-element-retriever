"""Pytest configuration and fixtures."""
import sys
import os
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Configure test environment
os.environ["HER_TEST_MODE"] = "true"

# Import fixtures that can be used across all tests
import pytest


@pytest.fixture
def mock_page():
    """Provide a mock page object for tests."""
    from unittest.mock import Mock
    page = Mock()
    page.url = "https://example.com"
    return page


@pytest.fixture
def temp_dir(tmp_path):
    """Provide a temporary directory for tests."""
    return tmp_path


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset any singleton instances between tests."""
    yield
    # Clean up after each test if needed