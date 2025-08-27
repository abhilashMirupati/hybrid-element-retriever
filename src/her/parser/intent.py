"""Natural language intent parsing.

This module contains a very lightweight parser that takes a plain English
instruction and attempts to extract an action (e.g. click, type), a target
phrase and any arguments such as values to type.  The implementation here
is deliberately simple: it splits the sentence into words and looks for
known verbs.  Real deployments should replace this with a proper
embedding‑based intent extractor and richer grammar rules.
"""

from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class Intent:
    action: str
    target_phrase: str
    args: Optional[str] = None
    constraints: Optional[Tuple[str, str]] = None


def parse_intent(step: str) -> Intent:
    """Parse a plain English step into an :class:`Intent`.

    The parser looks for simple verb patterns such as "click", "type" and
    extracts the remainder of the sentence as the target phrase.  Arguments
    for typing (e.g. the text to type) are detected using a "into" pattern.

    Examples::

        >>> parse_intent("Click the login button")
        Intent(action='click', target_phrase='the login button')
        >>> parse_intent("Type 'hello' into the message box")
        Intent(action='type', target_phrase='the message box', args="hello")

    Args:
        step: The raw English step.

    Returns:
        An :class:`Intent` instance.
    """
    text = step.strip().lower()
    # Default action
    action = "click"
    args = None
    target = text

    if text.startswith("click"):
        action = "click"
        target = text[len("click"):].strip()
    elif text.startswith("type"):
        action = "type"
        # naive extraction of quoted argument
        # e.g. "type 'hello' into the message box"
        if "into" in text:
            # split at into
            before, after = text.split("into", 1)
            before = before.strip()
            after = after.strip()
            # extract quoted string
            if "'" in before:
                arg = before.split("'", 2)[1]
                args = arg
            target = after
        else:
            target = text[len("type"):].strip()
    elif text.startswith("select"):
        action = "select"
        target = text[len("select"):].strip()
    else:
        # fallback: first word is verb, remainder is target
        parts = text.split(maxsplit=1)
        if len(parts) == 2:
            action, target = parts
        else:
            target = text
    return Intent(action=action, target_phrase=target.strip(), args=args)
