"""
HER Framework Exceptions

Custom exceptions for the HER framework.
"""

from __future__ import annotations

from typing import List, Optional


class ElementNotFoundError(Exception):
    """Raised when no elements match the target text."""
    
    def __init__(self, message: str, target_text: str = "", suggestions: List[str] = None):
        super().__init__(message)
        self.target_text = target_text
        self.suggestions = suggestions or []
    
    def __str__(self) -> str:
        msg = super().__str__()
        if self.suggestions:
            msg += f"\nSuggestions: {', '.join(self.suggestions[:5])}"
        return msg


class InvalidIntentError(Exception):
    """Raised when intent parsing fails."""
    
    def __init__(self, message: str, step: str = "", issues: List[str] = None):
        super().__init__(message)
        self.step = step
        self.issues = issues or []
    
    def __str__(self) -> str:
        msg = super().__init__()
        if self.issues:
            msg += f"\nIssues: {', '.join(self.issues)}"
        return msg


class XPathGenerationError(Exception):
    """Raised when XPath generation fails."""
    
    def __init__(self, message: str, element: dict = None):
        super().__init__(message)
        self.element = element or {}
    
    def __str__(self) -> str:
        msg = super().__str__()
        if self.element:
            msg += f"\nElement: {self.element.get('tag', 'unknown')}"
        return msg


class ExecutionError(Exception):
    """Raised when action execution fails."""
    
    def __init__(self, message: str, action: str = "", selector: str = ""):
        super().__init__(message)
        self.action = action
        self.selector = selector
    
    def __str__(self) -> str:
        msg = super().__str__()
        if self.action:
            msg += f"\nAction: {self.action}"
        if self.selector:
            msg += f"\nSelector: {self.selector}"
        return msg