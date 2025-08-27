#!/usr/bin/env bash
set -euo pipefail

echo "Running formatting checks (black)…"
black --check src/her tests

echo "Running flake8…"
flake8 src/her tests

echo "Running mypy…"
mypy src/her

# Fail the build if any placeholder markers are present.  We treat a literal
# three‑dot sequence and the typical task marker string as indicators of
# incomplete implementation.  The grep pattern searches recursively
# through source, test, script and CI files and returns non‑zero
# status if a match is found.  If matches are present we abort
# verification.
# Build the grep pattern without embedding the forbidden triple dot directly in
# the source.  We assemble "\\.\\.\\." from separate pieces to avoid
# triggering the placeholder detection on this very script.  The pattern
# matches three literal dots or the assembled task marker.
dot="\\."
# Assemble the task marker string from parts to avoid having the literal word in
# this script, which would otherwise trigger our own placeholder checker.  We
# concatenate "TO" and "DO" into a single variable.
todo="TO"
todo="${todo}DO"
pattern="${dot}${dot}${dot}|${todo}"
if grep -R -n -E "$pattern" src/her scripts ci java >/dev/null; then
  echo "Error: placeholder ellipsis or 'TO DO' detected in codebase."
  grep -R -n -E "$pattern" src/her scripts ci java
  exit 1
fi

echo "Running pytest…"
pytest --cov=src/her --cov-report=term

echo "All checks passed."