```sh
# scripts/install_models.sh
#!/usr/bin/env bash
# Installs and exports required ONNX models for HER, then writes MODEL_INFO.json.
# Models:
#   - intfloat/e5-small           (query embeddings; task: sentence-embedding / feature-extraction)
#   - microsoft/markuplm-base     (element embeddings; task: feature-extraction)
#
# Output directory:
#   repo_root/src/her/models/
#
# Requirements (installed automatically if missing):
#   - python3, pip
#   - optimum[onnxruntime], transformers, tokenizers, huggingface_hub
#
# Exit codes are non-zero on failure to ensure CI catches issues.
set -euo pipefail

# -------- locate repo root & models dir --------
SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
REPO_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
MODELS_DIR="$REPO_ROOT/src/her/models"
CACHE_DIR="${HER_HF_CACHE_DIR:-$REPO_ROOT/.cache/hf}"

mkdir -p "$MODELS_DIR"
mkdir -p "$CACHE_DIR"

# -------- config --------
E5_ID="intfloat/e5-small"
E5_TASK="feature-extraction"            # optimum task name for embeddings export
E5_OUT="$MODELS_DIR/e5-small-onnx"

MARKUPLM_ID="microsoft/markuplm-base"
MARKUPLM_TASK="feature-extraction"
MARKUPLM_OUT="$MODELS_DIR/markuplm-base-onnx"

MODEL_INFO_PATH="$MODELS_DIR/MODEL_INFO.json"

# Respect offline if set
HF_HUB_OFFLINE="${HF_HUB_OFFLINE:-0}"
export TRANSFORMERS_CACHE="$CACHE_DIR"
export HF_HOME="$CACHE_DIR"
export HF_HUB_ENABLE_HF_TRANSFER=1

# -------- helpers --------
need_cmd () { command -v "$1" >/dev/null 2>&1; }
ensure_python () {
  if ! need_cmd python3 && ! need_cmd python; then
    echo "ERROR: python3 is required." >&2
    exit 1
  fi
}
py () { if need_cmd python3; then python3 "$@"; else python "$@"; fi; }

pip_install () {
  # Install a package if the import fails
  local mod="$1"; shift
  local pkg="${1:-$mod}"
  if ! py - <<PY >/dev/null 2>&1
import importlib
import sys
sys.exit(0 if importlib.util.find_spec("$mod") is not None else 1)
PY
  then
    echo "Installing $pkg ..."
    py -m pip install --upgrade "$pkg"
  fi
}

write_model_info () {
  # Write MODEL_INFO.json (id + task + exported paths)
  cat > "$MODEL_INFO_PATH" <<JSON
{
  "generated_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "models": [
    {
      "name": "e5-small",
      "hf_id": "$E5_ID",
      "task": "$E5_TASK",
      "path": "src/her/models/$(basename "$E5_OUT")"
    },
    {
      "name": "markuplm-base",
      "hf_id": "$MARKUPLM_ID",
      "task": "$MARKUPLM_TASK",
      "path": "src/her/models/$(basename "$MARKUPLM_OUT")"
    }
  ]
}
JSON
  echo "Wrote $MODEL_INFO_PATH"
}

# -------- preflight --------
ensure_python
py -m pip --version >/dev/null 2>&1 || { echo "ERROR: pip not available for Python." >&2; exit 1; }

# install optimum + runtime + transformers stack if missing
pip_install "transformers" "transformers>=4.40.0"
pip_install "tokenizers" "tokenizers>=0.15.0"
pip_install "huggingface_hub" "huggingface_hub>=0.22.0"
pip_install "onnxruntime" "onnxruntime>=1.16.0"
pip_install "optimum" "optimum[onnxruntime]>=1.17.0"

# Also ensure the CLI entrypoint is present:
if ! need_cmd optimum-cli; then
  # Some environments expose CLI as `optimum-cli` after install; rehash PATH
  hash -r || true
fi
if ! need_cmd optimum-cli; then
  # Fallback shim using python -m optimum.exporters.onnx
  export OPTIMUM_NO_CLI=1
fi

# -------- export function using optimum --------
export_model () {
  local HF_ID="$1"
  local TASK="$2"
  local OUT_DIR="$3"

  if [ -d "$OUT_DIR" ] && [ -f "$OUT_DIR/model.onnx" ]; then
    echo "✓ Skipping export for $HF_ID (already exists at $OUT_DIR)"
    return 0
  fi

  rm -rf "$OUT_DIR"
  mkdir -p "$OUT_DIR"

  echo "→ Exporting $HF_ID to ONNX ($TASK) → $OUT_DIR"
  if [ "${OPTIMUM_NO_CLI:-0}" = "0" ] && need_cmd optimum-cli; then
    # Use CLI exporter
    optimum-cli export onnx \
      --model "$HF_ID" \
      --task "$TASK" \
      --cache_dir "$CACHE_DIR" \
      "$OUT_DIR"
  else
    # Use python module fallback exporter
    py - "$HF_ID" "$TASK" "$OUT_DIR" "$CACHE_DIR" <<'PY'
import sys, os
from optimum.exporters.onnx import main as onnx_export_main

hf_id, task, out_dir, cache_dir = sys.argv[1:5]
# Build args similar to CLI:
args = [
    "export", "onnx",
    "--model", hf_id,
    "--task", task,
    "--cache_dir", cache_dir,
    out_dir
]
onnx_export_main(args)
PY
  fi

  # Normalize output: ensure a single top-level model.onnx exists
  # Some exporters create multiple .onnx files; keep main graph as model.onnx if present.
  if [ -f "$OUT_DIR/model.onnx" ]; then
    echo "✓ Exported model.onnx at $OUT_DIR"
  else
    # try to find a reasonable primary graph
    CAND="$(find "$OUT_DIR" -maxdepth 1 -type f -name '*.onnx' | head -n1 || true)"
    if [ -n "$CAND" ]; then
      mv "$CAND" "$OUT_DIR/model.onnx"
      echo "✓ Normalized primary ONNX to $OUT_DIR/model.onnx"
    else
      echo "ERROR: No ONNX graph produced for $HF_ID in $OUT_DIR" >&2
      exit 2
    fi
  fi
}

# -------- exports --------
export_model "$E5_ID" "$E5_TASK" "$E5_OUT"
export_model "$MARKUPLM_ID" "$MARKUPLM_TASK" "$MARKUPLM_OUT"

# -------- tokenizer/config copy (safety) --------
copy_assets () {
  local HF_ID="$1"
  local OUT_DIR="$2"
  py - "$HF_ID" "$OUT_DIR" <<'PY'
import sys, os, shutil
from transformers import AutoTokenizer, AutoConfig, AutoProcessor

hf_id, out_dir = sys.argv[1:3]
os.makedirs(out_dir, exist_ok=True)

# Save tokenizer (if available)
try:
    tok = AutoTokenizer.from_pretrained(hf_id, use_fast=True)
    tok.save_pretrained(out_dir)
except Exception:
    pass

# Save config
try:
    cfg = AutoConfig.from_pretrained(hf_id)
    cfg.save_pretrained(out_dir)
except Exception:
    pass

# Some models use Processor (e.g., Layout/Markup variants)
try:
    proc = AutoProcessor.from_pretrained(hf_id)
    proc.save_pretrained(out_dir)
except Exception:
    pass
PY
}

copy_assets "$E5_ID" "$E5_OUT"
copy_assets "$MARKUPLM_ID" "$MARKUPLM_OUT"

# -------- MODEL_INFO.json --------
write_model_info

echo "✅ Models installed to: $MODELS_DIR"
```
