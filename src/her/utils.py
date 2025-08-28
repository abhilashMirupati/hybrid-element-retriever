"""Miscellaneous utilities used throughout the HER framework.

This module contains small helper functions that don't fit neatly into a
specific submodule.  You should avoid adding external dependencies here to
keep the core lightweight.

"""

import hashlib
from typing import Any, Iterable


def sha1_of(obj: Any) -> str:
    """Compute a SHA‑1 hex digest for the given object.

    The object is converted to its UTF‑8 representation if possible, or
    repr() is used as a fallback.  This function is used to generate
    deterministic keys for the embedding cache.

    """
    if isinstance(obj, (bytes, bytearray)):
        data = bytes(obj)
    else:
        data = repr(obj).encode("utf-8")
    return hashlib.sha1(data).hexdigest()


def flatten(iterable_of_iterables: Iterable[Iterable[Any]]) -> list:
    """Flatten a nested iterable into a single list."""
    return [item for sub in iterable_of_iterables for item in sub]


def sanitize_text(text: Any) -> str:
    """Sanitize text by removing extra whitespace.

    Args:
        text: Text to sanitize

    Returns:
        Sanitized text
    """
    if not text:
        return ""

    text = str(text)
    # Replace newlines and tabs with spaces
    text = text.replace("\n", " ").replace("\t", " ")
    # Replace multiple spaces with single space
    import re

    text = re.sub(r"\s+", " ", text)
    return text.strip()


def truncate_text(text: Any, max_length: int) -> str:
    """Truncate text to maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length

    Returns:
        Truncated text with ellipsis if needed
    """
    if not text:
        return ""

    text = str(text)
    if len(text) <= max_length:
        return text

    if max_length <= 3:
        return "..."

    return text[: max_length - 1] + "..."
