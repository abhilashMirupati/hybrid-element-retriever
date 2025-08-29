"""Hybrid Element Retriever (HER) - Production-ready element location for web automation."""

__version__ = "1.0.0"

# Lazy imports to avoid dependency issues
def __getattr__(name):
    if name == "HybridClient":
        from .cli_api import HybridElementRetrieverClient
        return HybridElementRetrieverClient
    if name == "HybridElementRetriever":
        from .cli_api import HybridElementRetrieverClient
        return HybridElementRetrieverClient
    if name == "HybridElementRetrieverClient":
        from .cli_api import HybridElementRetrieverClient
        return HybridElementRetrieverClient
    if name == "HERPipeline":
        from .pipeline import HERPipeline
        return HERPipeline
    if name == "PipelineConfig":
        from .pipeline import PipelineConfig
        return PipelineConfig
    if name == "ResilienceManager":
        from .resilience import ResilienceManager
        return ResilienceManager
    if name == "WaitStrategy":
        from .resilience import WaitStrategy
        return WaitStrategy
    if name == "InputValidator":
        from .validators import InputValidator
        return InputValidator
    if name == "DOMValidator":
        from .validators import DOMValidator
        return DOMValidator
    if name == "FormValidator":
        from .validators import FormValidator
        return FormValidator
    if name == "AccessibilityValidator":
        from .validators import AccessibilityValidator
        return AccessibilityValidator
    if name == "gateway_server":
        import importlib
        mod = importlib.import_module('.gateway_server', __name__)
        return mod
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "HybridClient",
    "HybridElementRetriever", 
    "HybridElementRetrieverClient",
    "HERPipeline",
    "PipelineConfig",
    "ResilienceManager",
    "WaitStrategy",
    "InputValidator",
    "DOMValidator",
    "FormValidator",
    "AccessibilityValidator",
    "gateway_server",
    "__version__"
]