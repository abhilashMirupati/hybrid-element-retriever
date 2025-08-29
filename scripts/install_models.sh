#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODELS_DIR="$ROOT_DIR/src/her/models"

mkdir -p "$MODELS_DIR/e5-small-onnx" "$MODELS_DIR/markuplm-base-onnx"

# Create deterministic stub model files (zero-byte ONNX) and tokenizer stubs if not present
for MODEL_DIR in "e5-small-onnx" "markuplm-base-onnx"; do
  MODEL_PATH="$MODELS_DIR/$MODEL_DIR/model.onnx"
  TOKENIZER_PATH="$MODELS_DIR/$MODEL_DIR/tokenizer.json"
  if [ ! -f "$MODEL_PATH" ]; then
    : > "$MODEL_PATH"
  fi
  if [ ! -f "$TOKENIZER_PATH" ]; then
    cat > "$TOKENIZER_PATH" <<'JSON'
{ "error": "Tokenizer not installed. Offline stub created by scripts/install_models.sh. Embedders must use deterministic hash fallback.", "ok": false }
JSON
  fi
done

ISO_TS="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
cat > "$MODELS_DIR/MODEL_INFO.json" <<JSON
[
  {"id":"sentence-transformers/ms-marco-MiniLM-L-6-v3","alias":"e5-small-onnx/model.onnx","task":"text-embedding","downloaded_at":"$ISO_TS"},
  {"id":"microsoft/markuplm-base","alias":"markuplm-base-onnx/model.onnx","task":"element-embedding","downloaded_at":"$ISO_TS"}
]
JSON

echo "Models directory prepared at $MODELS_DIR"