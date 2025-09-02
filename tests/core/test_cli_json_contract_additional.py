# tests/core/test_cli_json_contract_additional.py
"""
CLI contract tests (additional):
- Ensures 'query' and 'act' subcommands emit strict JSON with required keys.
- Must succeed without browsers; uses HER_DRY_RUN=1 if supported.
- Safe for -n auto (pure subprocess calls).
"""

import json
import os
import sys
import subprocess


def _run_cli(args):
    env = {**os.environ, "HER_DRY_RUN": "1"}  # enforce pure-Python path if supported
    proc = subprocess.run(
        [sys.executable, "-m", "her.cli", *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
        env=env,
    )
    assert proc.returncode == 0, f"CLI failed: {proc.stderr}"
    out = json.loads(proc.stdout)
    assert isinstance(out, dict), "CLI must return a JSON object"
    return out


def test_cli_query_contract_shape():
    out = _run_cli(["query", "click login"])
    # Required keys
    for k in ("xpath", "strategy", "metadata", "confidence"):
        assert k in out, f"missing key: {k}"
    assert isinstance(out["xpath"], str)
    assert isinstance(out["strategy"], str)
    assert isinstance(out["metadata"], dict)
    # confidence must be a plain number
    assert isinstance(out["confidence"], (int, float))


def test_cli_act_contract_shape():
    out = _run_cli(["act", "click login"])
    # Must include success indicator and method
    ok = out.get("ok")
    status = out.get("status")
    assert (isinstance(ok, bool) and ok in (True, False)) or isinstance(status, str), "missing ok/status"
    assert "method" in out, "missing method"
    # Prefer confidence/strategy if available but don't fail if only one is present
    assert ("confidence" in out) or ("strategy" in out), "missing confidence/strategy"
