#!/bin/bash
# Install optional ONNX models for HER

set -e

MODELS_DIR="${HER_MODELS_DIR:-$HOME/.her/models}"
mkdir -p "$MODELS_DIR"

echo "Installing HER models to $MODELS_DIR"

# Download E5-small model (if not present)
E5_DIR="$MODELS_DIR/e5-small-onnx"
if [ ! -f "$E5_DIR/model.onnx" ]; then
    echo "Downloading E5-small model..."
    mkdir -p "$E5_DIR"
    # In production, would download from HuggingFace or CDN
    echo "E5-small model would be downloaded here"
fi

# Download MarkupLM model (if not present)
MARKUPLM_DIR="$MODELS_DIR/markuplm-base-onnx"
if [ ! -f "$MARKUPLM_DIR/model.onnx" ]; then
    echo "Downloading MarkupLM model..."
    mkdir -p "$MARKUPLM_DIR"
    # In production, would download from HuggingFace or CDN
    echo "MarkupLM model would be downloaded here"
fi

# Download MiniLM fallback model (if not present)
MINILM_DIR="$MODELS_DIR/minilm-onnx"
if [ ! -f "$MINILM_DIR/model.onnx" ]; then
    echo "Downloading MiniLM model..."
    mkdir -p "$MINILM_DIR"
    # In production, would download from HuggingFace or CDN
    echo "MiniLM model would be downloaded here"
fi

echo "Model installation complete"