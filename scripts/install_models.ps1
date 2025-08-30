<#
.SYNOPSIS
  HER model installer for Windows (PowerShell).

.DESCRIPTION
  Downloads or prepares versioned ONNX model folders for:
   - sentence-transformers/ms-marco-MiniLM-L-6-v3 (→ e5-small-onnx/)
   - microsoft/markuplm-base (→ markuplm-base-onnx/)

  Writes src/her/models/MODEL_INFO.json with ISO-8601 timestamps.
  If offline/unavailable, creates deterministic stubs so the embedders can hash-fallback.
#>

param (
  [string]$RepoRoot = (Resolve-Path "$PSScriptRoot\.."),
  [string]$ModelsDir = $null
)

if (-not $ModelsDir) {
  $ModelsDir = Join-Path $RepoRoot "src\her\models"
}
$env:HER_MODELS_DIR = $ModelsDir

$E5Dir = Join-Path $ModelsDir "e5-small-onnx"
$MLMDir = Join-Path $ModelsDir "markuplm-base-onnx"

$E5Model = Join-Path $E5Dir "model.onnx"
$E5Tokenizer = Join-Path $E5Dir "tokenizer.json"
$MLMModel = Join-Path $MLMDir "model.onnx"
$MLMTokenizer = Join-Path $MLMDir "tokenizer.json"

$ModelInfo = Join-Path $ModelsDir "MODEL_INFO.json"

# Optional override URLs (env override if needed)
$E5Url = $env:E5_URL
$E5TokUrl = $env:E5_TOK_URL
$MLMUrl = $env:MLM_URL
$MLMTokUrl = $env:MLM_TOK_URL

function TimestampISO {
  return (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
}

function Ensure-Dir($path) {
  if (-not (Test-Path $path)) {
    New-Item -ItemType Directory -Path $path | Out-Null
  }
}

function Download-File($url, $dest) {
  try {
    Invoke-WebRequest -Uri $url -OutFile $dest -UseBasicParsing -ErrorAction Stop
    return $true
  } catch {
    Write-Host "[HER] Download failed for $url, error: $_"
    return $false
  }
}

function Make-StubModel($dest) {
  Set-Content -Path $dest -Value ""
}

function Make-StubTokenizer($dest) {
  @"
{
  "stub": true,
  "reason": "offline-or-missing-tokenizer",
  "note": "HER embedders will use deterministic hash fallback."
}
"@ | Set-Content -Path $dest -Encoding UTF8
}

function Ensure-E5 {
  Ensure-Dir $E5Dir
  Write-Host "[HER] Preparing E5-small ONNX at $E5Model"

  if ($E5Url) {
    if (-not (Download-File $E5Url $E5Model)) { Make-StubModel $E5Model }
  } else {
    Make-StubModel $E5Model
  }

  if ($E5TokUrl) {
    if (-not (Download-File $E5TokUrl $E5Tokenizer)) { Make-StubTokenizer $E5Tokenizer }
  } else {
    Make-StubTokenizer $E5Tokenizer
  }
}

function Ensure-MarkupLM {
  Ensure-Dir $MLMDir
  Write-Host "[HER] Preparing MarkupLM-base ONNX at $MLMModel"

  if ($MLMUrl) {
    if (-not (Download-File $MLMUrl $MLMModel)) { Make-StubModel $MLMModel }
  } else {
    Make-StubModel $MLMModel
  }

  if ($MLMTokUrl) {
    if (-not (Download-File $MLMTokUrl $MLMTokenizer)) { Make-StubTokenizer $MLMTokenizer }
  } else {
    Make-StubTokenizer $MLMTokenizer
  }
}

function Write-ModelInfo {
  $ts = TimestampISO
  Ensure-Dir $ModelsDir
  @"
[
  {
    "id": "sentence-transformers/ms-marco-MiniLM-L-6-v3",
    "alias": "e5-small-onnx/model.onnx",
    "task": "text-embedding",
    "downloaded_at": "$ts"
  },
  {
    "id": "microsoft/markuplm-base",
    "alias": "markuplm-base-onnx/model.onnx",
    "task": "element-embedding",
    "downloaded_at": "$ts"
  }
]
"@ | Set-Content -Path $ModelInfo -Encoding UTF8
  Write-Host "[HER] Wrote $ModelInfo"
}

# === Main ===
Ensure-E5
Ensure-MarkupLM
Write-ModelInfo

Write-Host "[HER] Model installation complete in $ModelsDir"
