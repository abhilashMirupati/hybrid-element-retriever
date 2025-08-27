#!/usr/bin/env bash
set -euo pipefail

# This script installs Playwright and its dependencies for local development.
# It should be run after creating your virtual environment and installing
# package requirements via `pip install .[dev]`.

echo "Installing Playwright browsers…"
npx playwright install chromium --with-deps

echo "Playwright installation complete."