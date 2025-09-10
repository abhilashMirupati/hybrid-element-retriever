# HER package init

# Load environment variables from .env file if available
from . import env_loader  # noqa: F401

def __getattr__(name):
    if name == "gateway_server":
        import importlib
        mod = importlib.import_module('.gateway_server', __name__)
        return mod
    # Provide direct access to the high-level runtime orchestrator.
    if name == "HerAgent":
        try:
            from .runtime.agent import HerAgent as _HA
            return _HA
        except Exception:
            # If runtime dependencies (e.g. Playwright) are missing, return None
            return None
    raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = [
    "HybridClient",
    "HybridElementRetriever",
    "HybridElementRetrieverClient",
    "HybridPipeline",
    "HERPipeline",
    "resolve_model_paths",
    "PipelineConfig",
    "ResilienceManager",
    "WaitStrategy",
    "InputValidator",
    "DOMValidator",
    "FormValidator",
    "AccessibilityValidator",
    "gateway_server",
    "HerAgent",
    "__version__"
]
