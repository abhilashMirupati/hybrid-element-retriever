#!/usr/bin/env python3
"""
HER Preflight (fail-fast)

Checks that:
  - Playwright is installed AND Chromium can launch
  - Models dir exists (HER_MODELS_DIR) with at least one known model folder
  - Cache dir (HER_CACHE_DIR) exists and SQLite DB is openable

Exit codes:
  0 = OK
  1 = Failure with a clear message

Usage:
  python scripts/preflight.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from her.strict import (
    require_env,
    require_path_exists,
    require_sqlite_open,
    require_playwright,
)

def main() -> None:
    # Playwright (and Chromium) must be present and launchable
    require_playwright(require_browser_launch=True)

    # Models
    models_dir = os.getenv("HER_MODELS_DIR", "").strip()
    if not models_dir:
        # Not all element embedders need heavy models, but we ENFORCE presence to avoid silent fallback
        raise SystemExit(
            "Missing HER_MODELS_DIR. Set it to your models directory, e.g.\n"
            "  Windows PowerShell:\n"
            "    $env:HER_MODELS_DIR = (Resolve-Path 'src/her/models').Path\n"
            "  macOS/Linux:\n"
            "    export HER_MODELS_DIR=\"$(pwd)/src/her/models\"\n"
            "Run the installers first: scripts/install_models.ps1 or scripts/install_models.sh"
        )
    require_path_exists(models_dir, kind="models dir")

    # Check for at least one known model directory
    known = [
        Path(models_dir) / "markuplm-base",      # heavy element embedder (optional but enforced by preflight)
        Path(models_dir) / "minilm-e5-small.onnx"  # example ONNX file (depending on your installer)
    ]
    if not any(p.exists() for p in known):
        raise SystemExit(
            f"Models not found in {models_dir}. Expected one of: "
            f"'markuplm-base' dir or 'minilm-e5-small.onnx' file. "
            f"Run scripts/install_models.*"
        )

    # Cache DB
    cache_dir = os.getenv("HER_CACHE_DIR", "").strip()
    if not cache_dir:
        raise SystemExit(
            "Missing HER_CACHE_DIR. Set it to a writable cache directory, e.g.\n"
            "  Windows PowerShell:\n"
            "    $env:HER_CACHE_DIR = (Resolve-Path '.\\.her_cache').Path\n"
            "  macOS/Linux:\n"
            "    export HER_CACHE_DIR=\"$(pwd)/.her_cache\" && mkdir -p \"$HER_CACHE_DIR\"\n"
            "Then run: scripts/init_dbs.ps1 or scripts/init_dbs.sh"
        )
    require_path_exists(cache_dir, kind="cache dir")

    db_path = str(Path(cache_dir) / "embeddings.db")
    if not Path(db_path).exists():
        raise SystemExit(
            f"SQLite DB not found at {db_path}. Run scripts/init_dbs.ps1 or scripts/init_dbs.sh."
        )
    require_sqlite_open(db_path)

    print("PREFLIGHT_OK: Playwright & Chromium launchable, models present, SQLite DB accessible ✅")

if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        # Print message and exit with code 1 if message provided
        msg = str(e) or "Preflight failed."
        if msg:
            print(msg)
        sys.exit(1)
    except Exception as e:
        print(f"Preflight error: {e}")
        sys.exit(1)
