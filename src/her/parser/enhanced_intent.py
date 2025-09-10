"""
Enhanced Intent Parser - Integrates structured parsing with existing runner
Maintains backward compatibility while adding structured format support
"""

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

@dataclass
class EnhancedIntent:
    """Enhanced intent with structured parsing support."""
    
    action: str
    target_phrase: str
    args: Optional[str] = None
    constraints: Optional[Dict[str, Any]] = None
    confidence: float = 1.0
    value: Optional[str] = None  # Extracted value for input actions
    
    # Backward compatibility with original Intent
    def __getitem__(self, key: str):
        mapping = {
            'action': self.action,
            'target': self.target_phrase,
            'args': self.args,
            'confidence': self.confidence,
        }
        return mapping.get(key)
    
    def __setitem__(self, key: str, value: Any):
        if key == 'action':
            self.action = value
        elif key == 'target':
            self.target_phrase = value
        elif key == 'args':
            self.args = value
        elif key == 'confidence':
            self.confidence = value
    
    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

class EnhancedIntentParser:
    """Enhanced intent parser with structured format support."""
    
    def __init__(self):
        # Import original patterns for fallback
        from .intent import IntentParser
        self.original_parser = IntentParser()
        
        # Structured patterns for high accuracy
        self.structured_patterns = [
            # Click actions: Click on "target" or Click "target" (allow words between "on" and quotes)
            (re.compile(r'^(click|press|tap|push|hit|select)\s+(?:on\s+)?(?:the\s+)?["\']([^"\']+)["\']', re.I), "click", None),
            
            # Type actions: Enter $value in "target" field
            (re.compile(r'^(type|enter|input|write|fill)\s+\$([^\s]+)\s+(?:in|into|to)\s+["\']([^"\']+)["\']', re.I), "type", "value"),
            
            # Validate actions: Validate "target"
            (re.compile(r'^(validate|verify|check|assert|ensure)\s+["\']([^"\']+)["\']', re.I), "assert", None),
            
            # Hover actions: Hover over "target"
            (re.compile(r'^(hover|mouse\s+over)\s+(?:over\s+)?["\']([^"\']+)["\']', re.I), "hover", None),
            
            # Wait actions: Wait for "target"
            (re.compile(r'^(wait|pause|delay)\s+(?:for\s+)?["\']?([^"\']+)["\']?', re.I), "wait", None),
            
            # Navigate actions: Navigate to "target"
            (re.compile(r'^(navigate|go|open|visit)\s+(?:to\s+)?["\']([^"\']+)["\']', re.I), "navigate", None),
            
            # Submit actions: Submit "target"
            (re.compile(r'^(submit|send|post|confirm)\s+["\']([^"\']+)["\']', re.I), "submit", None),
            
            # Clear actions: Clear "target"
            (re.compile(r'^(clear|empty|reset)\s+["\']([^"\']+)["\']', re.I), "clear", None),
        ]
    
    def parse(self, step: str) -> EnhancedIntent:
        """Parse step with structured format support and fallback to original parser."""
        step = step.strip()
        
        if not step:
            return EnhancedIntent(action="click", target_phrase="", confidence=0.0)
        
        # Try structured patterns first
        for pattern, action, arg_type in self.structured_patterns:
            match = pattern.match(step)
            if match:
                groups = match.groups()
                
                if arg_type == "value":
                    # Type action with value: Enter $value in "target"
                    return EnhancedIntent(
                        action=action,
                        target_phrase=groups[2],  # target
                        args=groups[1],  # value
                        value=groups[1],  # extracted value for sendKeys
                        confidence=1.0
                    )
                else:
                    # Other actions: Click "target", Validate "target", etc.
                    return EnhancedIntent(
                        action=action,
                        target_phrase=groups[1],  # target
                        confidence=1.0
                    )
        
        # Fallback to original parser for unstructured steps
        original_intent = self.original_parser.parse(step)
        return EnhancedIntent(
            action=original_intent.action,
            target_phrase=original_intent.target_phrase,
            args=original_intent.args,
            constraints=original_intent.constraints,
            confidence=original_intent.confidence
        )
    
    def validate_structured_format(self, step: str) -> Tuple[bool, str]:
        """Validate if step follows structured format."""
        if not step.strip():
            return False, "Empty step"
        
        # Check for quotes (mandatory for targets)
        if '"' not in step and "'" not in step:
            return False, f'Missing quotes around target. Use: {step.split()[0]} "target"'
        
        # Check for $ for input values
        if any(word in step.lower() for word in ["type", "enter", "input", "fill"]) and "$" not in step:
            return False, f'Missing $ for value. Use: {step.split()[0]} $value in "target"'
        
        return True, "Valid structured format"
    
    def get_format_examples(self) -> List[str]:
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
        ]

# Backward compatibility
def parse_intent(step: str) -> EnhancedIntent:
    """Parse intent with enhanced support (backward compatibility)."""
    parser = EnhancedIntentParser()
    return parser.parse(step)