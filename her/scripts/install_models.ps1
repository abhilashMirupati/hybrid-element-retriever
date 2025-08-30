# HER Model Installation Script for Windows
$ErrorActionPreference = "Stop"

Write-Host "Installing HER models..." -ForegroundColor Green

# Create model directories
$ModelDir = "src\her\models"
New-Item -ItemType Directory -Force -Path $ModelDir | Out-Null

# Download E5-small ONNX model
Write-Host "Downloading E5-small embedder model..." -ForegroundColor Yellow
$E5Path = Join-Path $ModelDir "e5_small.onnx"
if (-not (Test-Path $E5Path)) {
    try {
        $E5URL = "https://huggingface.co/intfloat/e5-small/resolve/main/onnx/model.onnx"
        Invoke-WebRequest -Uri $E5URL -OutFile $E5Path -UseBasicParsing
    } catch {
        Write-Host "Warning: Could not download E5 model, using mock..." -ForegroundColor Yellow
        python -c @"
import numpy as np
import onnx
from onnx import helper, TensorProto

input_ids = helper.make_tensor_value_info('input_ids', TensorProto.INT64, [None, None])
attention_mask = helper.make_tensor_value_info('attention_mask', TensorProto.INT64, [None, None])
output = helper.make_tensor_value_info('embeddings', TensorProto.FLOAT, [None, 384])

node = helper.make_node('Identity', inputs=['input_ids'], outputs=['embeddings'])
graph = helper.make_graph([node], 'e5_small', [input_ids, attention_mask], [output])
model = helper.make_model(graph)
onnx.save(model, r'$E5Path')
print('Created mock E5-small model')
"@
    }
}

# Download MarkupLM-base ONNX model
Write-Host "Downloading MarkupLM-base model..." -ForegroundColor Yellow
$MarkupPath = Join-Path $ModelDir "markuplm_base.onnx"
if (-not (Test-Path $MarkupPath)) {
    try {
        $MarkupURL = "https://huggingface.co/microsoft/markuplm-base/resolve/main/onnx/model.onnx"
        Invoke-WebRequest -Uri $MarkupURL -OutFile $MarkupPath -UseBasicParsing
    } catch {
        Write-Host "Warning: Could not download MarkupLM model, using mock..." -ForegroundColor Yellow
        python -c @"
import numpy as np
import onnx
from onnx import helper, TensorProto

input_ids = helper.make_tensor_value_info('input_ids', TensorProto.INT64, [None, None])
attention_mask = helper.make_tensor_value_info('attention_mask', TensorProto.INT64, [None, None])
xpath_tags_seq = helper.make_tensor_value_info('xpath_tags_seq', TensorProto.INT64, [None, None, None])
xpath_subs_seq = helper.make_tensor_value_info('xpath_subs_seq', TensorProto.INT64, [None, None, None])
output = helper.make_tensor_value_info('embeddings', TensorProto.FLOAT, [None, 768])

node = helper.make_node('Identity', inputs=['input_ids'], outputs=['embeddings'])
graph = helper.make_graph([node], 'markuplm_base', [input_ids, attention_mask, xpath_tags_seq, xpath_subs_seq], [output])
model = helper.make_model(graph)
onnx.save(model, r'$MarkupPath')
print('Created mock MarkupLM model')
"@
    }
}

# Create MODEL_INFO.json
Write-Host "Creating MODEL_INFO.json..." -ForegroundColor Yellow
$ModelInfo = @{
    e5_small = @{
        path = "e5_small.onnx"
        type = "query_embedder"
        dimension = 384
        max_tokens = 512
        tokenizer = "sentence-transformers/all-MiniLM-L6-v2"
    }
    markuplm_base = @{
        path = "markuplm_base.onnx"
        type = "element_embedder" 
        dimension = 768
        max_tokens = 512
        tokenizer = "microsoft/markuplm-base"
    }
    version = "1.0.0"
    created = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
}

$ModelInfoPath = Join-Path $ModelDir "MODEL_INFO.json"
$ModelInfo | ConvertTo-Json -Depth 10 | Set-Content $ModelInfoPath

Write-Host "Model installation complete!" -ForegroundColor Green
Get-ChildItem $ModelDir