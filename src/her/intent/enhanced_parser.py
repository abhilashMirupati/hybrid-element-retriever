"""
Enhanced Intent Parser for HER Framework

Extracts {action, target, value} from user steps following the format:
- Click "Login"
- Type $"John123" into "Username"  
- Validate "Welcome back"

Supports:
- Action = {click, type, validate}
- Target = quoted string ("" required)
- Value = quoted string prefixed with $ (for type actions)
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


@dataclass
class ParsedIntent:
    """Enhanced parsed intent with action, target, and value."""
    
    # Core components
    action: str
    target: str
    value: Optional[str]
    
    # Original input
    raw_step: str
    
    # Confidence and metadata
    confidence: float
    label_tokens: List[str]
    
    # Additional context
    constraints: Dict[str, Any]
    args: Optional[str]


class EnhancedIntentParser:
    """Enhanced intent parser for precise {action, target, value} extraction."""
    
    def __init__(self):
        # Action patterns with aliases
        self.action_patterns = {
            'click': {
                'keywords': {'click', 'tap', 'press', 'hit', 'open', 'choose', 'select', 'pick'},
                'pattern': r'(?:click|tap|press|hit|open|choose|select|pick)\s+"([^"]+)"',
                'priority': 1
            },
            'type': {
                'keywords': {'type', 'enter', 'fill', 'input', 'write', 'set'},
                'pattern': r'(?:type|enter|fill|input|write|set)\s+\$?"([^"]+)"\s+into\s+"([^"]+)"',
                'priority': 1
            },
            'validate': {
                'keywords': {'validate', 'check', 'verify', 'confirm', 'assert'},
                'pattern': r'(?:validate|check|verify|confirm|assert)\s+"([^"]+)"',
                'priority': 1
            },
            'navigate': {
                'keywords': {'open', 'go', 'navigate', 'visit'},
                'pattern': r'(?:open|go|navigate|visit)\s+(https?://[^\s]+)',
                'priority': 2
            },
            'wait': {
                'keywords': {'wait', 'pause', 'sleep'},
                'pattern': r'(?:wait|pause|sleep)\s+(?:for\s+)?(\d+(?:\.\d+)?)\s*(?:seconds?|s|ms)?',
                'priority': 2
            }
        }
        
        # Value extraction patterns
        self.value_patterns = [
            r'\$"([^"]+)"',  # $"value"
            r'\$([^\s"]+)',  # $value
            r'"([^"]+)"\s+into',  # "value" into
        ]
        
        # Target extraction patterns
        self.target_patterns = [
            r'"([^"]+)"',  # "target"
            r'into\s+"([^"]+)"',  # into "target"
            r'(?:click|tap|press|hit|open|choose|select|pick)\s+"([^"]+)"',  # action "target"
        ]
    
    def parse(self, step: str) -> ParsedIntent:
        """
        Parse a user step into structured intent.
        
        Args:
            step: User step string (e.g., 'Click "Login"', 'Type $"John123" into "Username"')
            
        Returns:
            ParsedIntent with action, target, value, and metadata
        """
        step = step.strip()
        if not step:
            return self._create_empty_intent(step)
        
        # Try to match against action patterns
        for action, config in self.action_patterns.items():
            match = re.search(config['pattern'], step, re.IGNORECASE)
            if match:
                return self._parse_action_match(action, match, step)
        
        # Fallback to keyword-based parsing
        return self._parse_by_keywords(step)
    
    def _parse_action_match(self, action: str, match: re.Match, step: str) -> ParsedIntent:
        """Parse intent from a successful action pattern match."""
        groups = match.groups()
        
        if action == 'click':
            target = groups[0] if groups else ''
            return ParsedIntent(
                action='click',
                target=target,
                value=None,
                raw_step=step,
                confidence=0.9,
                label_tokens=self._extract_label_tokens(target),
                constraints={},
                args=None
            )
        
        elif action == 'type':
            if len(groups) >= 2:
                value = groups[0]
                target = groups[1]
                return ParsedIntent(
                    action='type',
                    target=target,
                    value=value,
                    raw_step=step,
                    confidence=0.9,
                    label_tokens=self._extract_label_tokens(target),
                    constraints={},
                    args=value
                )
            else:
                # Fallback for type without "into"
                value = groups[0] if groups else ''
                return ParsedIntent(
                    action='type',
                    target='',
                    value=value,
                    raw_step=step,
                    confidence=0.7,
                    label_tokens=self._extract_label_tokens(value),
                    constraints={},
                    args=value
                )
        
        elif action == 'validate':
            target = groups[0] if groups else ''
            return ParsedIntent(
                action='validate',
                target=target,
                value=None,
                raw_step=step,
                confidence=0.9,
                label_tokens=self._extract_label_tokens(target),
                constraints={},
                args=None
            )
        
        elif action == 'navigate':
            url = groups[0] if groups else ''
            return ParsedIntent(
                action='navigate',
                target=url,
                value=None,
                raw_step=step,
                confidence=0.9,
                label_tokens=self._extract_label_tokens(url),
                constraints={},
                args=url
            )
        
        elif action == 'wait':
            duration = groups[0] if groups else '1'
            return ParsedIntent(
                action='wait',
                target='',
                value=duration,
                raw_step=step,
                confidence=0.8,
                label_tokens=[],
                constraints={'duration': float(duration)},
                args=duration
            )
        
        # Fallback
        return self._create_empty_intent(step)
    
    def _parse_by_keywords(self, step: str) -> ParsedIntent:
        """Fallback parsing using keyword detection."""
        step_lower = step.lower()
        
        # Detect action
        action = 'click'  # default
        for action_name, config in self.action_patterns.items():
            if any(keyword in step_lower for keyword in config['keywords']):
                action = action_name
                break
        
        # Extract value and target
        value = self._extract_value(step)
        target = self._extract_target(step)
        
        # If we have a value but no target, try to extract target from context
        if value and not target:
            target = self._extract_target_from_context(step, value)
        
        return ParsedIntent(
            action=action,
            target=target,
            value=value,
            raw_step=step,
            confidence=0.6,
            label_tokens=self._extract_label_tokens(target or step),
            constraints={},
            args=value
        )
    
    def _extract_value(self, step: str) -> Optional[str]:
        """Extract value from step using various patterns."""
        for pattern in self.value_patterns:
            match = re.search(pattern, step)
            if match:
                return match.group(1)
        return None
    
    def _extract_target(self, step: str) -> str:
        """Extract target from step using various patterns."""
        for pattern in self.target_patterns:
            match = re.search(pattern, step)
            if match:
                return match.group(1)
        return ''
    
    def _extract_target_from_context(self, step: str, value: str) -> str:
        """Extract target from context when value is present."""
        # Look for patterns like "Type value into target"
        pattern = rf'type[^"]*{re.escape(value)}[^"]*into\s+"([^"]+)"'
        match = re.search(pattern, step, re.IGNORECASE)
        if match:
            return match.group(1)
        
        # Look for patterns like "Type value target"
        pattern = rf'type[^"]*{re.escape(value)}[^"]*"([^"]+)"'
        match = re.search(pattern, step, re.IGNORECASE)
        if match:
            return match.group(1)
        
        return ''
    
    def _extract_label_tokens(self, text: str) -> List[str]:
        """Extract label tokens for promotion lookup."""
        if not text:
            return []
        
        # Clean and tokenize text
        cleaned = re.sub(r'[^\w\s]', ' ', text.lower())
        tokens = [token for token in cleaned.split() if token and len(token) > 1]
        
        return tokens
    
    def _create_empty_intent(self, step: str) -> ParsedIntent:
        """Create empty intent for invalid steps."""
        return ParsedIntent(
            action='',
            target='',
            value=None,
            raw_step=step,
            confidence=0.0,
            label_tokens=[],
            constraints={},
            args=None
        )
    
    def validate_intent(self, intent: ParsedIntent) -> Tuple[bool, List[str]]:
        """
        Validate parsed intent and return issues.
        
        Args:
            intent: Parsed intent to validate
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        # Check required fields
        if not intent.action:
            issues.append("No action detected")
        
        if intent.action in ['click', 'type', 'validate'] and not intent.target:
            issues.append(f"Action '{intent.action}' requires a target")
        
        if intent.action == 'type' and not intent.value:
            issues.append("Type action requires a value")
        
        # Check confidence
        if intent.confidence < 0.5:
            issues.append(f"Low confidence: {intent.confidence:.2f}")
        
        # Check for quoted strings where required
        if intent.action in ['click', 'validate'] and intent.target and not self._is_quoted(intent.target, intent.raw_step):
            issues.append(f"Target should be quoted: '{intent.target}'")
        
        if intent.action == 'type' and intent.value and not self._is_quoted(intent.value, intent.raw_step):
            issues.append(f"Value should be quoted: '{intent.value}'")
        
        return len(issues) == 0, issues
    
    def _is_quoted(self, text: str, raw_step: str) -> bool:
        """Check if text appears to be quoted in the original step."""
        return text in raw_step and (
            f'"{text}"' in raw_step or 
            f"'{text}'" in raw_step
        )
    
    def get_action_aliases(self, action: str) -> Set[str]:
        """Get all aliases for an action."""
        if action in self.action_patterns:
            return self.action_patterns[action]['keywords']
        return set()
    
    def is_valid_action(self, action: str) -> bool:
        """Check if action is valid."""
        return action in self.action_patterns
    
    def get_supported_actions(self) -> List[str]:
        """Get list of supported actions."""
        return list(self.action_patterns.keys())


# Convenience function for backward compatibility
def parse_intent(step: str) -> ParsedIntent:
    """Parse a single step into structured intent."""
    parser = EnhancedIntentParser()
    return parser.parse(step)