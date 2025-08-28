# scripts/install_models.ps1
# Installs and exports required ONNX models for HER on Windows, then writes MODEL_INFO.json.
# Models:
#   - intfloat/e5-small        (query embeddings; task: feature-extraction)
#   - microsoft/markuplm-base  (element embeddings; task: feature-extraction)
#
# Output directory:
#   repo_root/src/her/models/
#
# Requires Python. The script will install needed Python packages if missing:
#   transformers, tokenizers, huggingface_hub, onnxruntime, optimum[onnxruntime]
# Falls back to python module exporter if optimum-cli is not on PATH.

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# -------- locate repo root & models dir --------
$ScriptDir = Split-Path -LiteralPath $PSCommandPath -Parent
$RepoRoot  = Resolve-Path -LiteralPath (Join-Path $ScriptDir "..")
$ModelsDir = Join-Path $RepoRoot "src/her/models"
$CacheDir  = $env:HER_HF_CACHE_DIR
if (-not $CacheDir) { $CacheDir = Join-Path $RepoRoot ".cache/hf" }

New-Item -ItemType Directory -Force -Path $ModelsDir | Out-Null
New-Item -ItemType Directory -Force -Path $CacheDir  | Out-Null

# -------- config --------
$E5Id        = "intfloat/e5-small"
$E5Task      = "feature-extraction"
$E5Out       = Join-Path $ModelsDir "e5-small-onnx"

$MarkupId    = "microsoft/markuplm-base"
$MarkupTask  = "feature-extraction"
$MarkupOut   = Join-Path $ModelsDir "markuplm-base-onnx"

$ModelInfoPath = Join-Path $ModelsDir "MODEL_INFO.json"

# Respect offline if set
if (-not $env:HF_HUB_OFFLINE) { $env:HF_HUB_OFFLINE = "0" }
$env:TRANSFORMERS_CACHE = $CacheDir
$env:HF_HOME            = $CacheDir
$env:HF_HUB_ENABLE_HF_TRANSFER = "1"

# -------- helpers --------
function Get-PythonCmd {
    if (Get-Command py -ErrorAction SilentlyContinue) { return "py" }
    elseif (Get-Command python -ErrorAction SilentlyContinue) { return "python" }
    elseif (Get-Command python3 -ErrorAction SilentlyContinue) { return "python3" }
    throw "Python not found. Please install Python 3."
}

$Py = Get-PythonCmd

function Test-PythonImport($module) {
    $code = @"
import importlib, sys
sys.exit(0 if importlib.util.find_spec('$module') is not None else 1)
"@
    $tmp = [System.IO.Path]::GetTempFileName() + ".py"
    Set-Content -LiteralPath $tmp -Value $code -Encoding UTF8
    try {
        & $Py $tmp | Out-Null
        return $LASTEXITCODE -eq 0
    } finally {
        Remove-Item -LiteralPath $tmp -ErrorAction SilentlyContinue
    }
}

function Pip-InstallIfMissing($module, $package=$null) {
    if (-not (Test-PythonImport $module)) {
        if (-not $package) { $package = $module }
        Write-Host "Installing $package ..."
        & $Py -m pip install --upgrade $package
        if ($LASTEXITCODE -ne 0) { throw "pip install failed for $package" }
    }
}

function Has-Command($name) {
    return $null -ne (Get-Command $name -ErrorAction SilentlyContinue)
}

# -------- preflight --------
# ensure pip is usable
& $Py -m pip --version | Out-Null
if ($LASTEXITCODE -ne 0) { throw "pip not available for Python." }

# install optimum + runtime + transformers stack if missing
Pip-InstallIfMissing "transformers" "transformers>=4.40.0"
Pip-InstallIfMissing "tokenizers" "tokenizers>=0.15.0"
Pip-InstallIfMissing "huggingface_hub" "huggingface_hub>=0.22.0"
Pip-InstallIfMissing "onnxruntime" "onnxruntime>=1.16.0"
Pip-InstallIfMissing "optimum" "optimum[onnxruntime]>=1.17.0"

$UseCli = $true
if (-not (Has-Command "optimum-cli")) {
    $UseCli = $false
}

# -------- export function using optimum --------
function Invoke-PythonScript($code, $args) {
    $tmp = [System.IO.Path]::GetTempFileName() + ".py"
    Set-Content -LiteralPath $tmp -Value $code -Encoding UTF8
    try {
        & $Py $tmp @args
        if ($LASTEXITCODE -ne 0) { throw "Python script failed." }
    } finally {
        Remove-Item -LiteralPath $tmp -ErrorAction SilentlyContinue
    }
}

function Export-Model($hfId, $task, $outDir) {
    if (Test-Path -LiteralPath (Join-Path $outDir "model.onnx")) {
        Write-Host "✓ Skipping export for $hfId (already exists at $outDir)"
        return
    }
    if (Test-Path -LiteralPath $outDir) {
        Remove-Item -Recurse -Force -LiteralPath $outDir
    }
    New-Item -ItemType Directory -Force -Path $outDir | Out-Null

    Write-Host "→ Exporting $hfId to ONNX ($task) → $outDir"
    if ($UseCli) {
        optimum-cli export onnx --model "$hfId" --task "$task" --cache_dir "$CacheDir" "$outDir"
        if ($LASTEXITCODE -ne 0) { throw "optimum-cli export failed for $hfId" }
    } else {
        $exportPy = @"
import sys
from optimum.exporters.onnx import main as onnx_export_main
hf_id, task, out_dir, cache_dir = sys.argv[1:5]
args = ["export", "onnx", "--model", hf_id, "--task", task, "--cache_dir", cache_dir, out_dir]
onnx_export_main(args)
"@
        Invoke-PythonScript $exportPy @($hfId, $task, $outDir, $CacheDir)
    }

    $primary = Join-Path $outDir "model.onnx"
    if (-not (Test-Path -LiteralPath $primary)) {
        $cand = Get-ChildItem -LiteralPath $outDir -Filter *.onnx -File | Select-Object -First 1
        if ($null -eq $cand) { throw "No ONNX graph produced for $hfId in $outDir" }
        Move-Item -LiteralPath $cand.FullName -Destination $primary -Force
        Write-Host "✓ Normalized primary ONNX to $primary"
    } else {
        Write-Host "✓ Exported model.onnx at $outDir"
    }
}

# -------- tokenizer/config/processor copy --------
$copyAssetsPy = @"
import sys, os, shutil
from transformers import AutoTokenizer, AutoConfig, AutoProcessor
hf_id, out_dir = sys.argv[1:3]
os.makedirs(out_dir, exist_ok=True)
try:
    tok = AutoTokenizer.from_pretrained(hf_id, use_fast=True)
    tok.save_pretrained(out_dir)
except Exception:
    pass
try:
    cfg = AutoConfig.from_pretrained(hf_id)
    cfg.save_pretrained(out_dir)
except Exception:
    pass
try:
    proc = AutoProcessor.from_pretrained(hf_id)
    proc.save_pretrained(out_dir)
except Exception:
    pass
"@

function Copy-Assets($hfId, $outDir) {
    Invoke-PythonScript $copyAssetsPy @($hfId, $outDir)
}

# -------- exports --------
Export-Model -hfId $E5Id     -task $E5Task     -outDir $E5Out
Export-Model -hfId $MarkupId -task $MarkupTask -outDir $MarkupOut

Copy-Assets -hfId $E5Id     -outDir $E5Out
Copy-Assets -hfId $MarkupId -outDir $MarkupOut

# -------- MODEL_INFO.json --------
$info = @"
{
  "generated_at": "$(Get-Date -AsUTC -Format s)Z",
  "models": [
    { "name": "e5-small",      "hf_id": "$E5Id",     "task": "$E5Task",     "path": "src/her/models/$(Split-Path -Leaf $E5Out)" },
    { "name": "markuplm-base", "hf_id": "$MarkupId", "task": "$MarkupTask", "path": "src/her/models/$(Split-Path -Leaf $MarkupOut)" }
  ]
}
"@
Set-Content -LiteralPath $ModelInfoPath -Value $info -Encoding UTF8
Write-Host "Wrote $ModelInfoPath"

Write-Host "✅ Models installed to: $ModelsDir"
