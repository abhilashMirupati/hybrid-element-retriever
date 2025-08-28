"""Hybrid Element Retriever (HER) - Natural language web automation."""

__version__ = "0.1.0"

# Lazy import to avoid dependency issues
def __getattr__(name):
    if name == "HybridClient":
        from .cli_api import HybridClient
        return HybridClient
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = ["HybridClient", "__version__"]