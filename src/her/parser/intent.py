"""Natural language intent parsing with support for all action types."""

from dataclasses import dataclass
from typing import Optional, Tuple, List, Dict, Any
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class Intent:
    """Parsed intent from natural language."""

    action: str
    target_phrase: str
    args: Optional[str] = None
    constraints: Optional[Dict[str, Any]] = None
    confidence: float = 1.0

    # Test convenience: subscriptable like a dict
    def __getitem__(self, key: str):
        mapping = {
            'action': self.action,
            'target': self.target_phrase,
            'args': self.args,
            'confidence': self.confidence,
        }
        return mapping[key]


class IntentParser:
    """Parse natural language steps into structured intents."""

    def __init__(self):
        self.action_patterns = self._init_action_patterns()

    def _init_action_patterns(self) -> List[Tuple[re.Pattern, str, str]]:
        """Initialize regex patterns for action detection.

        Returns:
            List of (pattern, action, arg_type) tuples
        """
        return [
            # Click actions
            (re.compile(r"^click\s+(?:on\s+)?(.+)$", re.I), "click", None),
            (re.compile(r"^press\s+(?:on\s+)?(.+)$", re.I), "click", None),
            (re.compile(r"^tap\s+(?:on\s+)?(.+)$", re.I), "click", None),
            (re.compile(r"^select\s+(.+?)\s+button$", re.I), "click", None),
            # Type/Fill actions
            (
                re.compile(r'^type\s+["\'](.+?)["\']\s+(?:in|into)\s+(.+)$', re.I),
                "type",
                "text",
            ),
            (
                re.compile(r'^enter\s+["\'](.+?)["\']\s+(?:in|into)\s+(.+)$', re.I),
                "type",
                "text",
            ),
            (
                re.compile(r'^fill\s+(.+?)\s+with\s+["\'](.+?)["\']$', re.I),
                "type",
                "text_reversed",
            ),
            (
                re.compile(r'^input\s+["\'](.+?)["\']\s+(?:in|into)\s+(.+)$', re.I),
                "type",
                "text",
            ),
            (re.compile(r"^type\s+(.+)$", re.I), "type", "infer"),
            # Select actions
            (
                re.compile(r'^select\s+["\'](.+?)["\']\s+from\s+(.+)$', re.I),
                "select",
                "option",
            ),
            (
                re.compile(r'^choose\s+["\'](.+?)["\']\s+(?:from|in)\s+(.+)$', re.I),
                "select",
                "option",
            ),
            (
                re.compile(r'^pick\s+["\'](.+?)["\']\s+(?:from|in)\s+(.+)$', re.I),
                "select",
                "option",
            ),
            (re.compile(r"^select\s+(.+?)\s+option$", re.I), "select", None),
            # Checkbox/Radio actions
            (re.compile(r"^check\s+(.+?)\s*(?:checkbox|box)$", re.I), "check", None),
            (re.compile(r"^uncheck\s+(.+?)\s*(?:checkbox|box)?$", re.I), "uncheck", None),
            (re.compile(r"^tick\s+(.+?)\s*(?:checkbox|box)?$", re.I), "check", None),
            (re.compile(r"^toggle\s+(.+?)\s*(?:checkbox)?$", re.I), "toggle", None),
            (re.compile(r"^select\s+(.+?)\s+radio\s*(?:button)?$", re.I), "radio", None),
            # Hover actions
            (re.compile(r"^hover\s+(?:over\s+)?(.+)$", re.I), "hover", None),
            (re.compile(r"^mouse\s+over\s+(.+)$", re.I), "hover", None),
            (re.compile(r"^move\s+to\s+(.+)$", re.I), "hover", None),
            # Wait actions
            (re.compile(r"^wait\s+for\s+(.+)$", re.I), "wait", None),
            (
                re.compile(r"^wait\s+until\s+(.+?)\s+(?:is\s+)?visible$", re.I),
                "wait",
                "visible",
            ),
            (
                re.compile(r"^wait\s+(\d+)\s*(?:seconds?|secs?|s)$", re.I),
                "wait",
                "time",
            ),
            (
                re.compile(r"^pause\s+(?:for\s+)?(\d+)\s*(?:seconds?|secs?|s)?$", re.I),
                "wait",
                "time",
            ),
            # Navigation actions
            (
                re.compile(r"^(?:go\s+to|navigate\s+to|open)\s+(.+)$", re.I),
                "navigate",
                None,
            ),
            (re.compile(r"^refresh(?:\s+the\s+page)?$", re.I), "refresh", None),
            (re.compile(r"^go\s+back$", re.I), "back", None),
            # Assertion actions
            (
                re.compile(r"^verify\s+(.+?)\s+(?:is\s+)?visible$", re.I),
                "assert",
                "visible",
            ),
            (
                re.compile(r"^check\s+(?:that\s+)?(.+?)\s+exists$", re.I),
                "assert",
                "exists",
            ),
            (re.compile(r"^verify\s+(.+)$", re.I), "assert", None),
            (re.compile(r"^assert\s+(.+)$", re.I), "assert", None),
            (re.compile(r"^check\s+(.+)$", re.I), "assert", None),
            # Clear action
            (re.compile(r"^clear\s+(.+)$", re.I), "clear", None),
            # Submit action
            (re.compile(r"^submit\s+(.+)$", re.I), "submit", None),
        ]

    def parse(self, step: str) -> Intent:
        """Parse a natural language step into an Intent.

        Args:
            step: Natural language instruction

        Returns:
            Parsed Intent object
        """
        step = step.strip()

        # Try each pattern
        for pattern, action, arg_type in self.action_patterns:
            match = pattern.match(step)
            if match:
                return self._build_intent(match, action, arg_type, step)

        # Fallback: try to infer from keywords
        return self._infer_intent(step)

    def _build_intent(
        self, match: re.Match, action: str, arg_type: Optional[str], original: str
    ) -> Intent:
        """Build Intent from regex match.

        Args:
            match: Regex match object
            action: Action type
            arg_type: Argument type hint
            original: Original step text

        Returns:
            Intent object
        """
        groups = match.groups()

        if action == "type":
            if arg_type == "text":
                # Pattern: type "text" into field
                return Intent(
                    action=action,
                    target_phrase=groups[1],
                    args=groups[0],
                    confidence=0.9,
                )
            elif arg_type == "text_reversed":
                # Pattern: fill field with "text"
                return Intent(
                    action=action,
                    target_phrase=groups[0],
                    args=groups[1],
                    confidence=0.9,
                )
            elif arg_type == "infer":
                # Pattern: type something (need to extract text)
                text = groups[0]
                # Try to extract quoted text
                quoted = re.search(r'["\'](.+?)["\']', text)
                if quoted:
                    return Intent(
                        action=action,
                        target_phrase=text.replace(quoted.group(0), "").strip(),
                        args=quoted.group(1),
                        confidence=0.8,
                    )
                else:
                    return Intent(action=action, target_phrase=text, confidence=0.7)

        elif action == "select":
            if arg_type == "option":
                # Pattern: select "option" from dropdown
                return Intent(
                    action=action,
                    target_phrase=groups[1],
                    args=groups[0],
                    confidence=0.9,
                )
            else:
                return Intent(action=action, target_phrase=groups[0], confidence=0.8)

        elif action == "wait":
            if arg_type == "time":
                # Pattern: wait X seconds
                return Intent(
                    action=action,
                    target_phrase="",
                    args=groups[0],
                    constraints={"type": "time", "unit": "seconds"},
                    confidence=0.95,
                )
            elif arg_type == "visible":
                # Pattern: wait until X is visible
                return Intent(
                    action=action,
                    target_phrase=groups[0],
                    constraints={"type": "visible"},
                    confidence=0.9,
                )
            else:
                return Intent(action=action, target_phrase=groups[0], confidence=0.8)

        elif action == "assert":
            if arg_type:
                return Intent(
                    action=action,
                    target_phrase=groups[0],
                    constraints={"type": arg_type},
                    confidence=0.9,
                )
            else:
                return Intent(
                    action=action,
                    target_phrase=groups[0] if groups else original,
                    confidence=0.8,
                )

        else:
            # Default: single capture group is target
            target = groups[0] if groups else original
            return Intent(action=action, target_phrase=target, confidence=0.85)

    def _infer_intent(self, step: str) -> Intent:
        """Infer intent when no pattern matches.

        Args:
            step: Natural language step

        Returns:
            Best guess Intent
        """
        step_lower = step.lower()

        # Check for action keywords
        if any(word in step_lower for word in ["click", "press", "tap", "push"]):
            action = "click"
        elif any(word in step_lower for word in ["type", "enter", "input", "fill"]):
            action = "type"
        elif any(word in step_lower for word in ["select", "choose", "pick"]):
            action = "select"
        elif any(word in step_lower for word in ["hover", "mouse over"]):
            action = "hover"
        elif any(word in step_lower for word in ["wait", "pause"]):
            action = "wait"
        elif any(word in step_lower for word in ["verify", "check", "assert"]):
            action = "assert"
        else:
            # Default to click
            action = "click"

        # Extract target phrase (remove action word)
        action_words = [
            "click",
            "press",
            "tap",
            "type",
            "enter",
            "select",
            "hover",
            "wait",
        ]
        target = step
        for word in action_words:
            if step_lower.startswith(word):
                target = step[len(word) :].strip()
                break

        # Remove common prepositions
        for prep in ["on", "the", "a", "an"]:
            if target.lower().startswith(prep + " "):
                target = target[len(prep) + 1 :].strip()

        return Intent(action=action, target_phrase=target, confidence=0.6)

    def parse_batch(self, steps: List[str]) -> List[Intent]:
        """Parse multiple steps.

        Args:
            steps: List of natural language steps

        Returns:
            List of Intent objects
        """
        return [self.parse(step) for step in steps]

    def explain_intent(self, intent: Intent) -> str:
        """Generate human-readable explanation of intent.

        Args:
            intent: Intent object

        Returns:
            Explanation string
        """
        explanations = {
            "click": f"Click on '{intent.target_phrase}'",
            "type": (
                f"Type '{intent.args}' into '{intent.target_phrase}'"
                if intent.args
                else f"Type into '{intent.target_phrase}'"
            ),
            "select": (
                f"Select '{intent.args}' from '{intent.target_phrase}'"
                if intent.args
                else f"Select '{intent.target_phrase}'"
            ),
            "hover": f"Hover over '{intent.target_phrase}'",
            "wait": self._explain_wait(intent),
            "assert": (
                f"Verify that '{intent.target_phrase}' {intent.constraints.get('type', 'exists')}"
                if intent.constraints
                else f"Assert '{intent.target_phrase}'"
            ),
            "navigate": f"Navigate to '{intent.target_phrase}'",
            "clear": f"Clear '{intent.target_phrase}'",
            "submit": f"Submit '{intent.target_phrase}'",
            "refresh": "Refresh the page",
            "back": "Go back",
        }

        explanation = explanations.get(
            intent.action, f"{intent.action} '{intent.target_phrase}'"
        )

        if intent.confidence < 0.7:
            explanation += " (low confidence)"

        return explanation

    def _explain_wait(self, intent: Intent) -> str:
        """Generate explanation for wait intent.

        Args:
            intent: Wait intent

        Returns:
            Explanation string
        """
        if intent.constraints:
            if intent.constraints.get("type") == "time":
                return f"Wait for {intent.args} seconds"
            elif intent.constraints.get("type") == "visible":
                return f"Wait until '{intent.target_phrase}' is visible"

        if intent.target_phrase:
            return f"Wait for '{intent.target_phrase}'"

        return "Wait"


# Keep the original function for backwards compatibility
def parse_intent(step: str) -> Intent:
    """Parse a plain English step into an Intent.

    This function maintains backwards compatibility with the original API.

    Args:
        step: The raw English step

    Returns:
        An Intent instance
    """
    parser = IntentParser()
    return parser.parse(step)
