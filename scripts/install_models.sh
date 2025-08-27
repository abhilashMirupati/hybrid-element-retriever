#!/usr/bin/env bash
#
# Install and export the ONNX models required by Hybrid Element Retriever.
#
# This script downloads the MiniLM/E5‑small and MarkupLM‑base models
# from Hugging Face and exports them to ONNX format using the Optimum
# CLI.  The exported models are stored under ``src/her/models`` within
# the repository.  The resulting directory structure can be discovered
# by the HER model resolver at runtime.  If the models are already
# present, they will simply be reused.

set -euo pipefail

# Determine the repository root relative to this script.  ``${BASH_SOURCE[0]}``
# resolves to the current script path.  We ascend one directory to
# reach the ``repo`` root.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODELS_DIR="$ROOT/src/her/models"

# Allow callers to override the Python interpreter via the
# ``PYTHON_BIN`` environment variable.  Default to ``python``.
PYTHON_BIN="${PYTHON_BIN:-python}"

echo "[HER] Installing export tools…"
"$PYTHON_BIN" -m pip install -q --upgrade pip
"$PYTHON_BIN" -m pip install -q onnx onnxruntime "optimum[onnxruntime]" transformers tokenizers huggingface_hub

# Create directories for each model if they do not already exist.  The
# ONNX export and tokenizer files will be written into these
# directories.  The ``-p`` flag ensures nested directories are
# created.
mkdir -p "$MODELS_DIR/e5-small" "$MODELS_DIR/markuplm-base"

echo "[HER] Exporting intfloat/e5-small → ONNX (feature‑extraction)…"
optimum-cli export onnx --task feature-extraction --model intfloat/e5-small "$MODELS_DIR/e5-small"

echo "[HER] Exporting microsoft/markuplm-base → ONNX (feature‑extraction)…"
optimum-cli export onnx --task feature-extraction --model microsoft/markuplm-base "$MODELS_DIR/markuplm-base"

# Write a small metadata file so that the resolver knows which models
# are available locally.  This file is purely informational and is
# consumed by tooling outside of the runtime.
cat > "$MODELS_DIR/MODEL_INFO.json" <<'JSON'
{
  "e5_small": { "hf_id": "intfloat/e5-small", "task": "feature-extraction" },
  "markuplm_base": { "hf_id": "microsoft/markuplm-base", "task": "feature-extraction" }
}
JSON

echo "[HER] Models ready in $MODELS_DIR"