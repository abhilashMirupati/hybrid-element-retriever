import json
import os
import sys
import subprocess
import pytest


def _run_cli(args: list[str]) -> dict:
    proc = subprocess.run(
        [sys.executable, "-m", "her.cli", *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        text=True,
        env={**os.environ, "HER_DRY_RUN": "1"},  # ensure pure-Python path
    )
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert isinstance(data, dict)
    return data


def test_query_contract_strict_json_shape():
    out = _run_cli(["query", "click login"])
    for k in ("xpath", "strategy", "metadata", "confidence"):
        assert k in out, f"missing key: {k}"
    # element is often present for debug
    assert "element" in out


def test_act_contract_strict_json_shape_without_browser():
    out = _run_cli(["act", "click login"])
    # Accept either {'ok': true, ...} or {'status': 'ok', ...}
    assert ("ok" in out and isinstance(out["ok"], bool)) or ("status" in out), "Missing ok/status"
    assert "method" in out
    # Confidence may be present for action routing; allow optional but prefer present
    assert "confidence" in out or "strategy" in out
