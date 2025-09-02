import json
import subprocess
import sys


def run_cli(args):
  p = subprocess.run([sys.executable, "-m", "her.cli", *args], capture_output=True, text=True)
  assert p.returncode in (0,1)
  return p.stdout.strip() or p.stderr.strip()


def test_version_json():
  out = run_cli(["version"])
  data = json.loads(out)
  assert data.get("ok") is True or "version" in data


def test_cache_json():
  out = run_cli(["cache", "--clear"]) 
  data = json.loads(out)
  assert data.get("ok") is True
