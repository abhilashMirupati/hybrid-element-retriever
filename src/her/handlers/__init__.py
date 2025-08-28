"""Handlers for complex web scenarios."""

try:
    from .complex_scenarios import (
        ComplexScenarioHandler,
        StaleElementHandler,
        DynamicContentHandler,
        FrameHandler,
        ShadowDOMHandler,
        SPANavigationHandler,
        WaitStrategy
    )
except Exception:  # allow import when Playwright not installed
    ComplexScenarioHandler = object  # type: ignore
    StaleElementHandler = object  # type: ignore
    DynamicContentHandler = object  # type: ignore
    FrameHandler = object  # type: ignore
    ShadowDOMHandler = object  # type: ignore
    SPANavigationHandler = object  # type: ignore
    WaitStrategy = object  # type: ignore

__all__ = [
    "ComplexScenarioHandler",
    "StaleElementHandler",
    "DynamicContentHandler",
    "FrameHandler",
    "ShadowDOMHandler",
    "SPANavigationHandler",
    "WaitStrategy"
]