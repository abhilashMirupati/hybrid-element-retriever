# Thin wrapper around the production Executor
from ..executor import Executor  # your real executor

def click(selector: str, *, strict: bool = True) -> dict:
    return Executor().click(selector, strict=strict)

def type(selector: str, value: str, *, strict: bool = True) -> dict:
    return Executor().type(selector, value, strict=strict)

def verify(selector: str, expected: str) -> dict:
    return Executor().verify(selector, expected)
