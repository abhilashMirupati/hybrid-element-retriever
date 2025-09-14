"""
Intent Parser for No-Semantic Mode

This module parses test steps to extract intent, target_text (quoted), and value
for more explicit and deterministic element matching.
"""

from __future__ import annotations

import re
import logging
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
from enum import Enum

log = logging.getLogger("her.intent_parser")


class IntentType(Enum):
    """Types of user intents."""
    CLICK = "click"
    ENTER = "enter"
    TYPE = "type"
    SEARCH = "search"
    SELECT = "select"
    VALIDATE = "validate"
    NAVIGATE = "navigate"
    SCROLL = "scroll"
    HOVER = "hover"
    WAIT = "wait"


@dataclass
class ParsedIntent:
    """Parsed intent information."""
    intent: IntentType
    target_text: str
    value: Optional[str] = None
    original_step: str = ""
    confidence: float = 1.0


class IntentParser:
    """Parser for extracting intent and target information from test steps."""
    
    # Intent patterns with priority order
    INTENT_PATTERNS = [
        (r'\b(click|press|tap|select|choose|pick)\b', IntentType.CLICK),
        (r'\b(enter|type|input|fill)\b', IntentType.ENTER),
        (r'\b(search|find|look for|query)\b', IntentType.SEARCH),
        (r'\b(select|choose|pick from|dropdown)\b', IntentType.SELECT),
        (r'\b(validate|check|verify|assert)\b', IntentType.VALIDATE),
        (r'\b(navigate|go to|visit|open)\b', IntentType.NAVIGATE),
        (r'\b(scroll|move|swipe)\b', IntentType.SCROLL),
        (r'\b(hover|mouse over|focus)\b', IntentType.HOVER),
        (r'\b(wait|pause|delay)\b', IntentType.WAIT),
    ]
    
    def __init__(self):
        """Initialize intent parser."""
        self.compiled_patterns = [(re.compile(pattern, re.IGNORECASE), intent) 
                                 for pattern, intent in self.INTENT_PATTERNS]
    
    def parse_step(self, step: str) -> ParsedIntent:
        """Parse a test step to extract intent, target_text, and value.
        
        Args:
            step: Test step string (e.g., "click 'Submit' button", "enter 'John' in name field")
            
        Returns:
            ParsedIntent with extracted information
        """
        step = step.strip()
        if not step:
            return ParsedIntent(IntentType.CLICK, "", step)
        
        # Extract quoted target text
        target_text = self._extract_quoted_text(step)
        
        # Extract intent
        intent = self._extract_intent(step)
        
        # Extract value (for enter/type operations)
        value = self._extract_value(step, intent)
        
        # If no quoted text found, try to extract from context
        if not target_text:
            target_text = self._extract_contextual_target(step, intent)
        
        return ParsedIntent(
            intent=intent,
            target_text=target_text,
            value=value,
            original_step=step,
            confidence=self._calculate_confidence(step, target_text, intent)
        )
    
    def _extract_quoted_text(self, step: str) -> str:
        """Extract quoted text from step.
        
        Args:
            step: Test step string
            
        Returns:
            Extracted quoted text or empty string
        """
        # Look for quoted text in various formats
        patterns = [
            r'"([^"]+)"',  # "text"
            r"'([^']+)'",  # 'text'
            r'`([^`]+)`',  # `text`
        ]
        
        for pattern in patterns:
            match = re.search(pattern, step)
            if match:
                return match.group(1).strip()
        
        return ""
    
    def _extract_intent(self, step: str) -> IntentType:
        """Extract intent from step.
        
        Args:
            step: Test step string
            
        Returns:
            Detected intent type
        """
        step_lower = step.lower()
        
        # Check patterns in priority order
        for pattern, intent in self.compiled_patterns:
            if pattern.search(step_lower):
                return intent
        
        # Default to click if no intent detected
        return IntentType.CLICK
    
    def _extract_value(self, step: str, intent: IntentType) -> Optional[str]:
        """Extract value for enter/type operations.
        
        Args:
            step: Test step string
            intent: Detected intent type
            
        Returns:
            Extracted value or None
        """
        if intent not in [IntentType.ENTER, IntentType.TYPE, IntentType.SEARCH]:
            return None
        
        # Look for value patterns
        value_patterns = [
            r'(?:enter|type|input|fill)\s+[\'"]([^\'"]+)[\'"]',  # enter "value"
            r'(?:enter|type|input|fill)\s+([^\s]+)',  # enter value
            r'[\'"]([^\'"]+)[\'"]\s+(?:in|into|to)\s+',  # "value" in field
        ]
        
        for pattern in value_patterns:
            match = re.search(pattern, step, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_contextual_target(self, step: str, intent: IntentType) -> str:
        """Extract target from context when no quotes are present.
        
        Args:
            step: Test step string
            intent: Detected intent type
            
        Returns:
            Contextual target text
        """
        # Remove intent words and common prepositions
        step_clean = step.lower()
        intent_words = [intent.value, 'button', 'field', 'input', 'link', 'element']
        
        for word in intent_words:
            step_clean = step_clean.replace(word, '')
        
        # Remove common prepositions
        prepositions = ['in', 'on', 'at', 'to', 'for', 'with', 'by']
        for prep in prepositions:
            step_clean = step_clean.replace(f' {prep} ', ' ')
        
        # Clean up and return
        step_clean = re.sub(r'\s+', ' ', step_clean).strip()
        return step_clean
    
    def _calculate_confidence(self, step: str, target_text: str, intent: IntentType) -> float:
        """Calculate confidence score for parsed intent.
        
        Args:
            step: Original step
            target_text: Extracted target text
            intent: Detected intent
            
        Returns:
            Confidence score (0.0-1.0)
        """
        confidence = 1.0
        
        # Reduce confidence if no target text found
        if not target_text:
            confidence -= 0.3
        
        # Reduce confidence if intent is ambiguous
        if intent == IntentType.CLICK and not any(word in step.lower() for word in ['click', 'press', 'tap']):
            confidence -= 0.2
        
        # Increase confidence if quoted text is present
        if '"' in step or "'" in step:
            confidence += 0.1
        
        return max(0.0, min(1.0, confidence))
    
    def get_intent_specific_heuristics(self, intent: IntentType) -> Dict[str, Any]:
        """Get intent-specific heuristics for element matching.
        
        Args:
            intent: Intent type
            
        Returns:
            Dictionary of heuristics to apply
        """
        heuristics = {
            IntentType.CLICK: {
                'prefer_tags': ['button', 'a', 'input[type="button"]', 'input[type="submit"]'],
                'prefer_attributes': ['onclick', 'data-click', 'role="button"'],
                'avoid_tags': ['div', 'span', 'p'],
                'min_interactive_score': 0.7
            },
            IntentType.ENTER: {
                'prefer_tags': ['input[type="text"]', 'input[type="email"]', 'input[type="password"]', 'textarea'],
                'prefer_attributes': ['name', 'id', 'placeholder'],
                'avoid_tags': ['button', 'a', 'div'],
                'min_interactive_score': 0.8
            },
            IntentType.SEARCH: {
                'prefer_tags': ['input[type="text"]', 'input[type="search"]', 'input'],
                'prefer_attributes': ['name*search', 'placeholder*search', 'id*search'],
                'avoid_tags': ['button', 'a'],
                'min_interactive_score': 0.8
            },
            IntentType.SELECT: {
                'prefer_tags': ['select', 'option', 'input[type="radio"]', 'input[type="checkbox"]'],
                'prefer_attributes': ['name', 'id'],
                'avoid_tags': ['div', 'span'],
                'min_interactive_score': 0.7
            },
            IntentType.VALIDATE: {
                'prefer_tags': ['label', 'span', 'div', 'p'],
                'prefer_attributes': ['id', 'class', 'data-testid'],
                'avoid_tags': ['input', 'button'],
                'min_interactive_score': 0.5
            }
        }
        
        return heuristics.get(intent, {
            'prefer_tags': [],
            'prefer_attributes': [],
            'avoid_tags': [],
            'min_interactive_score': 0.5
        })