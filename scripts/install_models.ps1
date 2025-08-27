Param(
  [string]$PythonBin = "python"
)

#
# Install and export the ONNX models required by Hybrid Element Retriever on
# Windows.  This PowerShell script mirrors the behaviour of the
# accompanying Bash script.  It downloads the MiniLM/E5‑small and
# MarkupLM‑base models and exports them to ONNX format using the
# Optimum CLI.  The models are placed under ``src/her/models`` in the
# repository.

$ErrorActionPreference = "Stop"

# Compute the repository root relative to this script.  In PowerShell
# ``$MyInvocation.MyCommand.Path`` resolves to the script's full path.
$ROOT = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$MODELS_DIR = Join-Path $ROOT "src/her/models"

Write-Host "[HER] Installing export tools…"
& $PythonBin -m pip install -q --upgrade pip
& $PythonBin -m pip install -q onnx onnxruntime "optimum[onnxruntime]" transformers tokenizers huggingface_hub

# Ensure the model directories exist
New-Item -Force -ItemType Directory -Path (Join-Path $MODELS_DIR "e5-small") | Out-Null
New-Item -Force -ItemType Directory -Path (Join-Path $MODELS_DIR "markuplm-base") | Out-Null

Write-Host "[HER] Exporting intfloat/e5-small → ONNX (feature‑extraction)…"
optimum-cli export onnx --task feature-extraction --model intfloat/e5-small (Join-Path $MODELS_DIR "e5-small")

Write-Host "[HER] Exporting microsoft/markuplm-base → ONNX (feature‑extraction)…"
optimum-cli export onnx --task feature-extraction --model microsoft/markuplm-base (Join-Path $MODELS_DIR "markuplm-base")

# Write model metadata file
@'
{
  "e5_small": { "hf_id": "intfloat/e5-small", "task": "feature-extraction" },
  "markuplm_base": { "hf_id": "microsoft/markuplm-base", "task": "feature-extraction" }
}
'@ | Out-File -Encoding ascii (Join-Path $MODELS_DIR "MODEL_INFO.json")

Write-Host "[HER] Models ready in $MODELS_DIR"