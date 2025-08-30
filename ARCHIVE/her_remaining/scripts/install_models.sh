#!/bin/bash

# HER Model Installation Script
set -e

echo "Installing HER models..."

# Create model directories
MODEL_DIR="src/her/models"
mkdir -p "$MODEL_DIR"

# Download E5-small ONNX model
echo "Downloading E5-small embedder model..."
E5_URL="https://huggingface.co/intfloat/e5-small/resolve/main/onnx/model.onnx"
if [ ! -f "$MODEL_DIR/e5_small.onnx" ]; then
    curl -L -o "$MODEL_DIR/e5_small.onnx" "$E5_URL" 2>/dev/null || {
        echo "Warning: Could not download E5 model, using mock..."
        python -c "
import numpy as np
import onnx
from onnx import helper, TensorProto

# Create minimal mock ONNX model for E5-small
input_ids = helper.make_tensor_value_info('input_ids', TensorProto.INT64, [None, None])
attention_mask = helper.make_tensor_value_info('attention_mask', TensorProto.INT64, [None, None])
output = helper.make_tensor_value_info('embeddings', TensorProto.FLOAT, [None, 384])

# Create a simple identity-like operation
node = helper.make_node(
    'Identity',
    inputs=['input_ids'],
    outputs=['embeddings']
)

graph = helper.make_graph(
    [node],
    'e5_small',
    [input_ids, attention_mask],
    [output]
)

model = helper.make_model(graph)
onnx.save(model, '$MODEL_DIR/e5_small.onnx')
print('Created mock E5-small model')
"
    }
fi

# Download MarkupLM-base ONNX model  
echo "Downloading MarkupLM-base model..."
MARKUP_URL="https://huggingface.co/microsoft/markuplm-base/resolve/main/onnx/model.onnx"
if [ ! -f "$MODEL_DIR/markuplm_base.onnx" ]; then
    curl -L -o "$MODEL_DIR/markuplm_base.onnx" "$MARKUP_URL" 2>/dev/null || {
        echo "Warning: Could not download MarkupLM model, using mock..."
        python -c "
import numpy as np
import onnx
from onnx import helper, TensorProto

# Create minimal mock ONNX model for MarkupLM
input_ids = helper.make_tensor_value_info('input_ids', TensorProto.INT64, [None, None])
attention_mask = helper.make_tensor_value_info('attention_mask', TensorProto.INT64, [None, None])
xpath_tags_seq = helper.make_tensor_value_info('xpath_tags_seq', TensorProto.INT64, [None, None, None])
xpath_subs_seq = helper.make_tensor_value_info('xpath_subs_seq', TensorProto.INT64, [None, None, None])
output = helper.make_tensor_value_info('embeddings', TensorProto.FLOAT, [None, 768])

node = helper.make_node(
    'Identity', 
    inputs=['input_ids'],
    outputs=['embeddings']
)

graph = helper.make_graph(
    [node],
    'markuplm_base',
    [input_ids, attention_mask, xpath_tags_seq, xpath_subs_seq],
    [output]
)

model = helper.make_model(graph)
onnx.save(model, '$MODEL_DIR/markuplm_base.onnx')
print('Created mock MarkupLM model')
"
    }
fi

# Create MODEL_INFO.json
echo "Creating MODEL_INFO.json..."
cat > "$MODEL_DIR/MODEL_INFO.json" << EOF
{
    "e5_small": {
        "path": "e5_small.onnx",
        "type": "query_embedder",
        "dimension": 384,
        "max_tokens": 512,
        "tokenizer": "sentence-transformers/all-MiniLM-L6-v2"
    },
    "markuplm_base": {
        "path": "markuplm_base.onnx",
        "type": "element_embedder",
        "dimension": 768,
        "max_tokens": 512,
        "tokenizer": "microsoft/markuplm-base"
    },
    "version": "1.0.0",
    "created": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
}
EOF

echo "Model installation complete!"
ls -la "$MODEL_DIR"/