# src/her/strict.py
from __future__ import annotations

"""
HER Strict Mode Guard (fail-fast, no silent fallbacks)

Use this to assert hard preconditions at runtime. If a requirement is not met,
we raise StrictViolation and exit with a clear message.

Enabled by default. Set HER_STRICT=0 only for local debugging.
"""

import os
import sqlite3
from dataclasses import dataclass
from typing import Optional


class StrictViolation(RuntimeError):
    """Raised when a strict rule is violated (no silent pass)."""


def _truthy(s: Optional[str]) -> bool:
    return str(s).strip() not in ("0", "false", "False", "", "none", "None")


@dataclass(frozen=True)
class StrictConfig:
    enabled: bool = True

    def ensure(self, condition: bool, message: str) -> None:
        if self.enabled and not condition:
            raise StrictViolation(message)

    def require_env(self, name: str, message: str = "") -> str:
        val = os.getenv(name, "")
        if self.enabled and not val:
            msg = message or f"Missing environment variable: {name}"
            raise StrictViolation(msg)
        return val

    def require_path_exists(self, path: str, kind: str = "path") -> None:
        if not self.enabled:
            return
        if not os.path.exists(path):
            raise StrictViolation(f"Required {kind} does not exist: {path}")

    def require_file_nonempty(self, path: str) -> None:
        if not self.enabled:
            return
        if not os.path.isfile(path) or os.path.getsize(path) <= 0:
            raise StrictViolation(f"Required file missing or empty: {path}")

    def require_sqlite_open(self, db_path: str) -> None:
        if not self.enabled:
            return
        try:
            con = sqlite3.connect(db_path, timeout=5.0)
            con.execute("PRAGMA user_version;").fetchone()
        except Exception as e:
            raise StrictViolation(f"Cannot open SQLite DB at {db_path}: {e}") from e
        finally:
            try:
                con.close()
            except Exception:
                pass

    def require_playwright(self, require_browser_launch: bool = True) -> None:
        if not self.enabled:
            return
        try:
            from playwright.sync_api import sync_playwright  # noqa: F401
        except Exception as e:  # pragma: no cover
            raise StrictViolation(
                "Playwright is required. Install with `pip install playwright` and run "
                "`python -m playwright install chromium`."
            ) from e

        if require_browser_launch:
            try:
                from playwright.sync_api import sync_playwright
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    browser.new_context().close()
                    browser.close()
            except Exception as e:
                raise StrictViolation(
                    "Chromium is not installed or cannot launch. Run: "
                    "`python -m playwright install chromium`."
                ) from e


STRICT = StrictConfig(enabled=_truthy(os.getenv("HER_STRICT", "1")))


# Convenience free functions (import-friendly)
def ensure(condition: bool, message: str) -> None:
    STRICT.ensure(condition, message)


def require_env(name: str, message: str = "") -> str:
    return STRICT.require_env(name, message)


def require_path_exists(path: str, kind: str = "path") -> None:
    STRICT.require_path_exists(path, kind)


def require_file_nonempty(path: str) -> None:
    STRICT.require_file_nonempty(path)


def require_sqlite_open(db_path: str) -> None:
    STRICT.require_sqlite_open(db_path)


def require_playwright(require_browser_launch: bool = True) -> None:
    STRICT.require_playwright(require_browser_launch=require_browser_launch)
