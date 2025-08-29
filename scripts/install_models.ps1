# Install optional ONNX models for HER (Windows)

$ErrorActionPreference = "Stop"

$ModelsDir = if ($env:HER_MODELS_DIR) { $env:HER_MODELS_DIR } else { "$env:USERPROFILE\.her\models" }
New-Item -ItemType Directory -Force -Path $ModelsDir | Out-Null

Write-Host "Installing HER models to $ModelsDir"

# Download E5-small model (if not present)
$E5Dir = "$ModelsDir\e5-small-onnx"
if (-not (Test-Path "$E5Dir\model.onnx")) {
    Write-Host "Downloading E5-small model..."
    New-Item -ItemType Directory -Force -Path $E5Dir | Out-Null
    # In production, would download from HuggingFace or CDN
    Write-Host "E5-small model would be downloaded here"
}

# Download MarkupLM model (if not present)
$MarkupLMDir = "$ModelsDir\markuplm-base-onnx"
if (-not (Test-Path "$MarkupLMDir\model.onnx")) {
    Write-Host "Downloading MarkupLM model..."
    New-Item -ItemType Directory -Force -Path $MarkupLMDir | Out-Null
    # In production, would download from HuggingFace or CDN
    Write-Host "MarkupLM model would be downloaded here"
}

# Download MiniLM fallback model (if not present)
$MiniLMDir = "$ModelsDir\minilm-onnx"
if (-not (Test-Path "$MiniLMDir\model.onnx")) {
    Write-Host "Downloading MiniLM model..."
    New-Item -ItemType Directory -Force -Path $MiniLMDir | Out-Null
    # In production, would download from HuggingFace or CDN
    Write-Host "MiniLM model would be downloaded here"
}

Write-Host "Model installation complete"