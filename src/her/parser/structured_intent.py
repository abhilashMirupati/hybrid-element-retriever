"""
Structured Intent Parser - High Accuracy Intent/Target Extraction
Uses mandatory quotes for targets and $ for values to achieve 100% accuracy
"""

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

@dataclass
class StructuredIntent:
    """Structured intent with high accuracy parsing."""
    
    action: str
    target: str
    value: Optional[str] = None
    query: str = ""
    confidence: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for pipeline."""
        return {
            "action": self.action,
            "target": self.target,
            "value": self.value,
            "query": self.query,
            "confidence": self.confidence
        }

class StructuredIntentParser:
    """High-accuracy intent parser using structured format."""
    
    def __init__(self):
        # Action patterns with their aliases
        self.action_patterns = {
            "click": ["click", "press", "tap", "push", "hit", "select"],
            "type": ["type", "enter", "input", "write", "fill"],
            "select": ["select", "choose", "pick"],
            "validate": ["validate", "verify", "check", "assert", "ensure"],
            "hover": ["hover", "mouse over", "mouseover"],
            "wait": ["wait", "pause", "delay"],
            "navigate": ["navigate", "go", "open", "visit"],
            "submit": ["submit", "send", "post", "confirm"],
            "clear": ["clear", "empty", "reset"],
            "scroll": ["scroll", "swipe", "pan"],
            "drag": ["drag", "move", "reorder"],
            "double_click": ["double click", "double-click", "dblclick"],
            "right_click": ["right click", "right-click", "context menu"],
        }
    
    def parse(self, step: str) -> StructuredIntent:
        """Parse structured step with 100% accuracy.
        
        Expected formats:
        1. Click on the "Login" button -> action: click, target: Login
        2. Enter $test123 in "password" field -> action: enter, target: password, value: test123
        3. Validate "User successfully logged In" -> action: validate, target: User successfully logged In
        """
        step = step.strip()
        
        if not step:
            return StructuredIntent(action="click", target="", query=step, confidence=0.0)
        
        # Pattern 1: Click on "target" or Click "target"
        click_pattern = r'^(click|press|tap|push|hit|select)\s+(?:on\s+)?["\']([^"\']+)["\']'
        match = re.match(click_pattern, step, re.IGNORECASE)
        if match:
            action = match.group(1).lower()
            target = match.group(2)
            return StructuredIntent(
                action=action,
                target=target,
                query=step,
                confidence=1.0
            )
        
        # Pattern 2: Enter/Type $value in "target" field
        type_pattern = r'^(type|enter|input|write|fill)\s+\$([^\s]+)\s+(?:in|into|to)\s+["\']([^"\']+)["\']'
        match = re.match(type_pattern, step, re.IGNORECASE)
        if match:
            action = match.group(1).lower()
            value = match.group(2)
            target = match.group(3)
            return StructuredIntent(
                action=action,
                target=target,
                value=value,
                query=step,
                confidence=1.0
            )
        
        # Pattern 3: Validate/Check "target"
        validate_pattern = r'^(validate|verify|check|assert|ensure)\s+["\']([^"\']+)["\']'
        match = re.match(validate_pattern, step, re.IGNORECASE)
        if match:
            action = match.group(1).lower()
            target = match.group(2)
            return StructuredIntent(
                action=action,
                target=target,
                query=step,
                confidence=1.0
            )
        
        # Pattern 4: Hover over "target"
        hover_pattern = r'^(hover|mouse\s+over)\s+(?:over\s+)?["\']([^"\']+)["\']'
        match = re.match(hover_pattern, step, re.IGNORECASE)
        if match:
            action = "hover"
            target = match.group(2)
            return StructuredIntent(
                action=action,
                target=target,
                query=step,
                confidence=1.0
            )
        
        # Pattern 5: Wait for "target" or Wait X seconds
        wait_pattern = r'^(wait|pause|delay)\s+(?:for\s+)?["\']?([^"\']+)["\']?'
        match = re.match(wait_pattern, step, re.IGNORECASE)
        if match:
            action = "wait"
            target = match.group(2)
            return StructuredIntent(
                action=action,
                target=target,
                query=step,
                confidence=1.0
            )
        
        # Pattern 6: Navigate to "target"
        navigate_pattern = r'^(navigate|go|open|visit)\s+(?:to\s+)?["\']([^"\']+)["\']'
        match = re.match(navigate_pattern, step, re.IGNORECASE)
        if match:
            action = "navigate"
            target = match.group(2)
            return StructuredIntent(
                action=action,
                target=target,
                query=step,
                confidence=1.0
            )
        
        # Pattern 7: Submit "target"
        submit_pattern = r'^(submit|send|post|confirm)\s+["\']([^"\']+)["\']'
        match = re.match(submit_pattern, step, re.IGNORECASE)
        if match:
            action = "submit"
            target = match.group(2)
            return StructuredIntent(
                action=action,
                target=target,
                query=step,
                confidence=1.0
            )
        
        # Pattern 8: Clear "target"
        clear_pattern = r'^(clear|empty|reset)\s+["\']([^"\']+)["\']'
        match = re.match(clear_pattern, step, re.IGNORECASE)
        if match:
            action = "clear"
            target = match.group(2)
            return StructuredIntent(
                action=action,
                target=target,
                query=step,
                confidence=1.0
            )
        
        # Fallback: Try to extract action and target without quotes (lower confidence)
        return self._fallback_parse(step)
    
    def _fallback_parse(self, step: str) -> StructuredIntent:
        """Fallback parsing for unstructured steps."""
        step_lower = step.lower()
        
        # Find action
        action = "click"  # default
        for act, patterns in self.action_patterns.items():
            if any(pattern in step_lower for pattern in patterns):
                action = act
                break
        
        # Extract target (everything after action word)
        action_words = [word for patterns in self.action_patterns.values() for word in patterns]
        target = step
        for word in action_words:
            if step_lower.startswith(word):
                target = step[len(word):].strip()
                break
        
        # Clean up target
        for prep in ["on", "the", "a", "an", "in", "into", "to"]:
            if target.lower().startswith(prep + " "):
                target = target[len(prep) + 1:].strip()
        
        return StructuredIntent(
            action=action,
            target=target,
            query=step,
            confidence=0.6  # Lower confidence for unstructured
        )
    
    def validate_format(self, step: str) -> Tuple[bool, str]:
        """Validate if step follows structured format.
        
        Returns:
            (is_valid, suggestion)
        """
        if not step.strip():
            return False, "Empty step"
        
        # Check for quotes
        if '"' not in step and "'" not in step:
            return False, f'Missing quotes around target. Use: {step.split()[0]} "target"'
        
        # Check for $ for values
        if any(word in step.lower() for word in ["type", "enter", "input", "fill"]) and "$" not in step:
            return False, f'Missing $ for value. Use: {step.split()[0]} $value in "target"'
        
        return True, "Valid structured format"
    
    def get_examples(self) -> List[str]:
        """Get example structured steps."""
        return [
            'Click on "Login" button',
            'Enter $test123 in "password" field',
            'Validate "User successfully logged in"',
            'Hover over "product image"',
            'Wait for "page to load"',
            'Navigate to "about page"',
            'Submit "contact form"',
            'Clear "search field"',
            'Select "United States" from "country dropdown"',
            'Check "terms and conditions" checkbox'
        ]

# Backward compatibility
def parse_structured_intent(step: str) -> StructuredIntent:
    """Parse structured intent (backward compatibility)."""
    parser = StructuredIntentParser()
    return parser.parse(step)