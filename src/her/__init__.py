"""
Hybrid Element Retriever (HER) - Natural Language Web Automation

Convert natural language descriptions into precise XPath/CSS selectors.

Example:
    >>> from her.cli_api import HybridClient
    >>> client = HybridClient()
    >>> result = client.act("Click the login button", url="https://example.com")
    >>> print(result['used_locator'])  # Shows the XPath that was used

For more information, see:
- SETUP_GUIDE.md for comprehensive documentation
- QUICK_REFERENCE.md for quick start guide
- examples/demo.py for interactive examples
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

# Main public API
from .cli_api import HybridClient

__all__ = [
    "HybridClient",
    "__version__",
]

# Optional: Log that HER is imported successfully
import logging
logger = logging.getLogger(__name__)
logger.info(f"HER {__version__} initialized")