#!/usr/bin/env bash
# install_models.sh
# Hybrid Element Retriever - Model Installer (Linux/macOS)
# - MiniLM (ONNX)  -> src/her/models/e5-small-onnx/
# - MarkupLM (PT)  -> src/her/models/markuplm-base/
set -euo pipefail

BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)/src/her/models"
echo "[HER] Installing models into $BASE_DIR"

# ---------- helpers ----------
require_cmd() {
  command -v "$1" >/dev/null 2>&1 || { echo "[HER] ERROR: '$1' not found"; exit 1; }
}
require_python_pkg() {
  python3 -c "import $1" 2>/dev/null || { echo "[HER] ERROR: Missing Python package '$1'. Run: pip install huggingface_hub transformers onnxruntime optimum"; exit 1; }
}
file_size() {
  # cross-platform stat (GNU vs BSD)
  if stat -c %s "$1" >/dev/null 2>&1; then stat -c %s "$1"; else stat -f %z "$1"; fi
}
require_file_min() {
  local path="$1"; local name="$2"; local minbytes="$3"
  [ -f "$path" ] || { echo "[HER] ERROR: Missing $name at $path"; exit 1; }
  local sz; sz=$(file_size "$path")
  if [ "$sz" -lt "$minbytes" ]; then
    echo "[HER] ERROR: $name too small (${sz} bytes): $path"; exit 1;
  fi
  # print size in MB to 1 decimal
  awk -v s="$sz" -v n="$name" 'BEGIN{printf("[HER] OK: %s (%.1f MB)\n", n, s/1048576)}'
}

# ---------- prechecks ----------
require_cmd python3
require_python_pkg huggingface_hub
require_python_pkg transformers
require_python_pkg onnxruntime
require_python_pkg optimum

mkdir -p "$BASE_DIR"

# =========================
# 1) MiniLM (ONNX) install
# =========================
MINI_DIR="$BASE_DIR/e5-small-onnx"
mkdir -p "$MINI_DIR"
echo "[HER] Downloading MiniLM (Xenova/all-MiniLM-L6-v2) ..."

python3 - <<PY
from huggingface_hub import snapshot_download
import os, shutil
local_dir = r"$MINI_DIR"
os.makedirs(local_dir, exist_ok=True)

# Pull snapshot (brings tokenizer + multiple onnx variants)
snapshot_download(repo_id='Xenova/all-MiniLM-L6-v2', local_dir=local_dir)

# Move main ONNX to root if under onnx/
onnx_dir = os.path.join(local_dir, 'onnx')
src = os.path.join(onnx_dir, 'model.onnx')
dst = os.path.join(local_dir, 'model.onnx')
if os.path.isdir(onnx_dir) and os.path.exists(src):
    shutil.move(src, dst)
    # best-effort cleanup of remaining onnx/ files
    for f in list(os.listdir(onnx_dir)):
        try: os.remove(os.path.join(onnx_dir, f))
        except Exception: pass
    try: os.rmdir(onnx_dir)
    except Exception: pass

# Final check
if not os.path.exists(dst) and not os.path.exists(os.path.join(local_dir, 'model.onnx')):
    raise RuntimeError('MiniLM model.onnx not found after download.')
PY

require_file_min "$MINI_DIR/model.onnx" "MiniLM model.onnx" $((5*1024*1024))
if [ -f "$MINI_DIR/tokenizer.json" ]; then
  require_file_min "$MINI_DIR/tokenizer.json" "MiniLM tokenizer.json" $((4*1024))
elif [ -f "$MINI_DIR/vocab.txt" ]; then
  require_file_min "$MINI_DIR/vocab.txt" "MiniLM vocab.txt" $((4*1024))
else
  echo "[HER] ERROR: MiniLM tokenizer not found (tokenizer.json or vocab.txt) in $MINI_DIR"; exit 1
fi

# ==========================================
# 2) MarkupLM (Transformers, flat to models)
# ==========================================
MARKUP_DIR="$BASE_DIR/markuplm-base"
mkdir -p "$MARKUP_DIR"
echo "[HER] Downloading MarkupLM-base (flat files) ..."

python3 - <<PY
from huggingface_hub import snapshot_download
import os
dst = r"$MARKUP_DIR"
os.makedirs(dst, exist_ok=True)
snapshot_download(
    repo_id='microsoft/markuplm-base',
    local_dir=dst,
    allow_patterns=[
        'config.json',
        'pytorch_model.bin',
        'tokenizer.json','tokenizer_config.json',
        'vocab.txt','special_tokens_map.json','added_tokens.json'
    ],
)
PY

require_file_min "$MARKUP_DIR/config.json" "MarkupLM config.json" 256
if [ -f "$MARKUP_DIR/tokenizer.json" ]; then
  require_file_min "$MARKUP_DIR/tokenizer.json" "MarkupLM tokenizer.json" $((4*1024))
elif [ -f "$MARKUP_DIR/vocab.txt" ]; then
  require_file_min "$MARKUP_DIR/vocab.txt" "MarkupLM vocab.txt" $((4*1024))
else
  echo "[HER] ERROR: MarkupLM tokenizer not found (tokenizer.json or vocab.txt) in $MARKUP_DIR"; exit 1
fi
require_file_min "$MARKUP_DIR/pytorch_model.bin" "MarkupLM weights (pytorch_model.bin)" $((100*1024*1024))

echo "[HER] ✅ All models installed successfully."
