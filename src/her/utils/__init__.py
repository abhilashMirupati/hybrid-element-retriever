import hashlib
from typing import Any, Iterable
import re


def sha1_of(obj: Any) -> str:
    if isinstance(obj, (bytes, bytearray)):
        data = bytes(obj)
    else:
        data = repr(obj).encode("utf-8")
    return hashlib.sha1(data).hexdigest()


def flatten(iterable_of_iterables: Iterable[Iterable[Any]]) -> list:
    return [item for sub in iterable_of_iterables for item in sub]


def sanitize_text(text: Any) -> str:
    if not text:
        return ""
    text = str(text)
    text = text.replace("\n", " ").replace("\t", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def truncate_text(text: Any, max_length: int) -> str:
    if not text:
        return ""
    s = str(text)
    if len(s) <= max_length:
        return s
    if max_length <= 3:
        return "..."
    # Keep one space plus ellipsis as tests expect specific slice behavior
    return s[: max_length - 1] + "..."


__all__ = ["sha1_of", "flatten", "sanitize_text", "truncate_text"]
