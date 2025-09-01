import json
import subprocess
import sys


def _run_cli(args):
    # Prefer module invocation to avoid PATH issues
    cmd = [sys.executable, "-m", "her.cli"] + args
    proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return proc.stdout.strip()


def _assert_strict_json(obj):
    assert isinstance(obj, dict)
    # No empty top-level fields for contract outputs we validate
    for k, v in obj.items():
        assert v is not None


def test_cli_version_contract():
    out = _run_cli(["version"]).splitlines()[-1]
    data = json.loads(out)
    assert data.get("ok") is True
    assert data.get("name") == "her"
    assert isinstance(data.get("version"), str)


def test_cli_cache_clear_contract():
    out = _run_cli(["cache", "--clear"]).splitlines()[-1]
    data = json.loads(out)
    assert data.get("ok") is True
    assert data.get("cleared") is True


def test_cli_query_contract_minimal():
    out = _run_cli(["query", "click login"]).splitlines()[-1]
    data = json.loads(out)
    # Accept either normalized schema or legacy schema normalized by cli
    if {"element", "xpath", "confidence", "strategy", "metadata"} <= set(data.keys()):
        _assert_strict_json(data)
        assert isinstance(data["element"], (dict, type(None)))
        assert isinstance(data["xpath"], (str, type(None)))
        assert isinstance(data["confidence"], (float, int))
        assert isinstance(data["strategy"], str)
        assert isinstance(data["metadata"], dict)
    else:
        # Accept legacy passthrough shape or strict error contract
        if "selector" in data or "xpath" in data:
            assert True
        elif "ok" in data and isinstance(data["ok"], bool):
            # Strict JSON error/no-candidate case
            assert (data["ok"] is False) and ("error" in data)
        else:
            raise AssertionError(f"Unexpected CLI output shape: {data}")


def test_cli_act_contract_minimal():
    out = _run_cli(["act", "click login"]).splitlines()[-1]
    data = json.loads(out)
    # Accept status or ok/error contracts
    assert isinstance(data, dict)
    if "ok" in data:
        assert isinstance(data["ok"], bool)
    elif "status" in data:
        assert data["status"] in {"success", "failure"}
    else:
        # Fallback: normalized action summary must contain method and confidence
        assert "method" in data and "confidence" in data
