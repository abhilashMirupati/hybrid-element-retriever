# Hybrid Element Retriever - Model Installer
# - MiniLM (ONNX)  -> src\her\models\e5-small-onnx\model.onnx (+tokenizer files)
# - MarkupLM (PT)  -> src\her\models\markuplm-base\  (flat, not nested cache)
# Fails loudly (no stub files). PowerShell-safe (no heredocs).

param(
  [string]$BaseDir = "$PSScriptRoot\..\src\her\models"
)

$ErrorActionPreference = "Stop"
Write-Host "[HER] Installing models into $BaseDir"

# ---------- helpers ----------
function Ensure-Python {
  if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "[HER] Python not found. Install Python 3.10+ and ensure 'python' is on PATH."
  }
}
function Ensure-PipPkg($name) {
  $ok = python -m pip show $name 2>$null
  if (-not $ok) { throw "[HER] Missing Python package: $name. Run: pip install huggingface_hub transformers onnxruntime optimum" }
}
function Run-Py($code) {
  $tmp = [System.IO.Path]::GetTempFileName() + ".py"
  $code | Out-File -FilePath $tmp -Encoding utf8
  try { python $tmp } finally { Remove-Item $tmp -Force -ErrorAction SilentlyContinue }
}
function Require-File($path, $name, $minBytes=1024) {
  if (-not (Test-Path $path)) { throw "[HER] Missing $name at $path" }
  $len = (Get-Item $path).Length
  if ($len -lt $minBytes) { throw "[HER] $name too small ($len bytes): $path" }
  Write-Host "[HER] OK: $name ($([math]::Round($len/1MB,1)) MB)"
}

# ---------- prechecks ----------
Ensure-Python
@("huggingface_hub","transformers","onnxruntime","optimum") | ForEach-Object { Ensure-PipPkg $_ }

# Make base dir
New-Item -ItemType Directory -Force -Path $BaseDir | Out-Null

# =========================
# 1) MiniLM (ONNX) install
# =========================
$MiniDir = Join-Path $BaseDir "e5-small-onnx"
New-Item -ItemType Directory -Force -Path $MiniDir | Out-Null
Write-Host "[HER] Downloading MiniLM (Xenova/all-MiniLM-L6-v2) ..."

Run-Py @"
from huggingface_hub import snapshot_download
import os, shutil

local_dir = r'''$MiniDir'''
os.makedirs(local_dir, exist_ok=True)

# Pull the whole snapshot so tokenizer files come too
snapshot_download(repo_id='Xenova/all-MiniLM-L6-v2', local_dir=local_dir)

# Move the main ONNX up (if placed under onnx/)
onnx_dir = os.path.join(local_dir, 'onnx')
src = os.path.join(onnx_dir, 'model.onnx')
dst = os.path.join(local_dir, 'model.onnx')
if os.path.isdir(onnx_dir) and os.path.exists(src):
    shutil.move(src, dst)
    # best-effort cleanup of remaining files under onnx/
    for f in list(os.listdir(onnx_dir)):
        try: os.remove(os.path.join(onnx_dir, f))
        except Exception: pass
    try: os.rmdir(onnx_dir)
    except Exception: pass

if not os.path.exists(dst):
    # some snapshots already place model.onnx at root; ensure it exists
    if not os.path.exists(os.path.join(local_dir, 'model.onnx')):
        raise RuntimeError('MiniLM model.onnx not found after download.')
"@

# Validate MiniLM
Require-File (Join-Path $MiniDir "model.onnx") "MiniLM model.onnx" 5MB
$tokJson = Join-Path $MiniDir "tokenizer.json"
$vocabTxt = Join-Path $MiniDir "vocab.txt"
if (Test-Path $tokJson) { Require-File $tokJson "MiniLM tokenizer.json" 4096 }
elseif (Test-Path $vocabTxt) { Require-File $vocabTxt "MiniLM vocab.txt" 4096 }
else { throw "[HER] MiniLM tokenizer not found (tokenizer.json or vocab.txt) in $MiniDir" }

# ==========================================
# 2) MarkupLM (Transformers, flat to models)
# ==========================================
$MarkupDir = Join-Path $BaseDir "markuplm-base"
New-Item -ItemType Directory -Force -Path $MarkupDir | Out-Null
Write-Host "[HER] Downloading MarkupLM-base (flat files) ..."

# Use snapshot_download to place files FLAT under models/markuplm-base
Run-Py @"
from huggingface_hub import snapshot_download
import os
dst = r'''$MarkupDir'''
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
"@

# Validate MarkupLM essentials are flat in markuplm-base/
Require-File (Join-Path $MarkupDir "config.json") "MarkupLM config.json" 256
# one of tokenizer.json OR vocab.txt must exist
$mlTokJson = Join-Path $MarkupDir "tokenizer.json"
$mlVocab   = Join-Path $MarkupDir "vocab.txt"
if (Test-Path $mlTokJson) { Require-File $mlTokJson "MarkupLM tokenizer.json" 4096 }
elseif (Test-Path $mlVocab) { Require-File $mlVocab "MarkupLM vocab.txt" 4096 }
else { throw "[HER] MarkupLM tokenizer not found (tokenizer.json or vocab.txt) in $MarkupDir" }
Require-File (Join-Path $MarkupDir "pytorch_model.bin") "MarkupLM weights (pytorch_model.bin)" 100MB

Write-Host "[HER] ✅ All models installed successfully."
