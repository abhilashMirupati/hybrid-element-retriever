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
