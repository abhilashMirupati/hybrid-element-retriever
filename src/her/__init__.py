# HER package init

# Load environment variables from .env file if available
from . import env_loader  # noqa: F401

def __getattr__(name):
    # These modules are not available in this version
    if name in ["gateway_server", "HerAgent"]:
        return None
    raise AttributeError(f"module {__name__} has no attribute {name}")


# Import core classes that exist
try:
    from .core.pipeline import HybridPipeline
    from .core.compat import HERPipeline
except ImportError as e:
    # Handle missing dependencies gracefully
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Core pipeline dependencies not available: {e}")
    HybridPipeline = None
    HERPipeline = None

from .core.config import PipelineConfig

# Import CLI classes that exist
try:
    from .cli.cli_api import (
        ResilienceManager,
        WaitStrategy,
        InputValidator,
        DOMValidator,
        FormValidator,
        HybridElementRetrieverClient
    )
except ImportError:
    # CLI classes not available
    ResilienceManager = None
    WaitStrategy = None
    InputValidator = None
    DOMValidator = None
    FormValidator = None
    HybridElementRetrieverClient = None

# Version information
__version__ = "0.1.0"

__all__ = [
    "HybridPipeline",
    "HERPipeline", 
    "PipelineConfig",
    "ResilienceManager",
    "WaitStrategy",
    "InputValidator",
    "DOMValidator",
    "FormValidator",
    "HybridElementRetrieverClient",
    "__version__"
]
