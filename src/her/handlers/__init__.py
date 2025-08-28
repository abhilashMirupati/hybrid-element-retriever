"""Handlers for complex web scenarios."""

from .complex_scenarios import (
    ComplexScenarioHandler,
    StaleElementHandler,
    DynamicContentHandler,
    FrameHandler,
    ShadowDOMHandler,
    SPANavigationHandler,
    WaitStrategy
)

__all__ = [
    "ComplexScenarioHandler",
    "StaleElementHandler",
    "DynamicContentHandler",
    "FrameHandler",
    "ShadowDOMHandler",
    "SPANavigationHandler",
    "WaitStrategy"
]