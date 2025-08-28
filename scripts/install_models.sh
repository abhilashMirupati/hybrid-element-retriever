#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
REPO_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
MODELS_DIR="$REPO_ROOT/src/her/models"
CACHE_DIR="${HER_HF_CACHE_DIR:-$REPO_ROOT/.cache/hf}"
mkdir -p "$MODELS_DIR" "$CACHE_DIR"
E5_ID="intfloat/e5-small"; E5_TASK="feature-extraction"; E5_OUT="$MODELS_DIR/e5-small-onnx"
MARKUPLM_ID="microsoft/markuplm-base"; MARKUPLM_TASK="feature-extraction"; MARKUPLM_OUT="$MODELS_DIR/markuplm-base-onnx"
MODEL_INFO_PATH="$MODELS_DIR/MODEL_INFO.json"
export TRANSFORMERS_CACHE="$CACHE_DIR"; export HF_HOME="$CACHE_DIR"; export HF_HUB_ENABLE_HF_TRANSFER=1
py(){ if command -v python3 >/dev/null; then python3 "$@"; else python "$@"; fi; }
pip_install(){ local mod="$1"; local pkg="${2:-$1}"; if ! py - <<PY >/dev/null 2>&1
import importlib,sys; sys.exit(0 if importlib.util.find_spec("$mod") else 1)
PY
 then py -m pip install --upgrade "$pkg"; fi; }
pip_install transformers "transformers>=4.40.0"
pip_install tokenizers "tokenizers>=0.15.0"
pip_install huggingface_hub "huggingface_hub>=0.22.0"
pip_install onnxruntime "onnxruntime>=1.16.0"
pip_install optimum "optimum[onnxruntime]>=1.17.0"
if ! command -v optimum-cli >/dev/null; then export OPTIMUM_NO_CLI=1; fi
export_model(){ local HF_ID="$1" TASK="$2" OUT_DIR="$3"
  if [ -f "$OUT_DIR/model.onnx" ]; then echo "✓ $HF_ID already exported"; return 0; fi
  rm -rf "$OUT_DIR"; mkdir -p "$OUT_DIR"
  if [ "${OPTIMUM_NO_CLI:-0}" = "0" ] && command -v optimum-cli >/dev/null; then
    optimum-cli export onnx --model "$HF_ID" --task "$TASK" --cache_dir "$CACHE_DIR" "$OUT_DIR"
  else
    py - "$HF_ID" "$TASK" "$OUT_DIR" "$CACHE_DIR" <<'PY'
import sys
from optimum.exporters.onnx import main as onnx_export_main
onnx_export_main(["export","onnx","--model",sys.argv[1],"--task",sys.argv[2],"--cache_dir",sys.argv[4],sys.argv[3]])
PY
  fi
  if [ ! -f "$OUT_DIR/model.onnx" ]; then
    CAND="$(find "$OUT_DIR" -maxdepth 1 -type f -name '*.onnx' | head -n1 || true)"
    if [ -n "$CAND" ]; then mv "$CAND" "$OUT_DIR/model.onnx"; else echo "ERROR: ONNX missing"; exit 2; fi
  fi
}
export_model "$E5_ID" "$E5_TASK" "$E5_OUT"
export_model "$MARKUPLM_ID" "$MARKUPLM_TASK" "$MARKUPLM_OUT"
py - "$E5_ID" "$E5_OUT" <<'PY'
import sys, os
from transformers import AutoTokenizer, AutoConfig, AutoProcessor
hid, out = sys.argv[1:3]; os.makedirs(out, exist_ok=True)
for loader in (AutoTokenizer, AutoConfig, AutoProcessor):
    try:
        loader.from_pretrained(hid).save_pretrained(out)
    except Exception:
        continue
PY
py - "$MARKUPLM_ID" "$MARKUPLM_OUT" <<'PY'
import sys, os
from transformers import AutoTokenizer, AutoConfig, AutoProcessor
hid, out = sys.argv[1:3]; os.makedirs(out, exist_ok=True)
for loader in (AutoTokenizer, AutoConfig, AutoProcessor):
    try:
        loader.from_pretrained(hid).save_pretrained(out)
    except Exception:
        continue
PY
cat > "$MODEL_INFO_PATH" <<JSON
{
  "generated_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "models": [
    { "name": "e5-small", "hf_id": "$E5_ID", "task": "$E5_TASK", "path": "src/her/models/$(basename "$E5_OUT")" },
    { "name": "markuplm-base", "hf_id": "$MARKUPLM_ID", "task": "$MARKUPLM_TASK", "path": "src/her/models/$(basename "$MARKUPLM_OUT")" }
  ]
}
JSON
echo "✅ Models installed at $MODELS_DIR"
