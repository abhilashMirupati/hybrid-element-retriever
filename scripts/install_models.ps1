# Windows model exporter for HER
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -LiteralPath $PSCommandPath -Parent
$RepoRoot  = Resolve-Path -LiteralPath (Join-Path $ScriptDir "..")
$ModelsDir = Join-Path $RepoRoot "src/her/models"
$CacheDir  = $env:HER_HF_CACHE_DIR
if (-not $CacheDir) { $CacheDir = Join-Path $RepoRoot ".cache/hf" }
New-Item -ItemType Directory -Force -Path $ModelsDir | Out-Null
New-Item -ItemType Directory -Force -Path $CacheDir  | Out-Null
$E5Id="intfloat/e5-small"; $E5Task="feature-extraction"; $E5Out=Join-Path $ModelsDir "e5-small-onnx"
$MarkupId="microsoft/markuplm-base"; $MarkupTask="feature-extraction"; $MarkupOut=Join-Path $ModelsDir "markuplm-base-onnx"
$ModelInfoPath = Join-Path $ModelsDir "MODEL_INFO.json"
$env:TRANSFORMERS_CACHE=$CacheDir; $env:HF_HOME=$CacheDir; $env:HF_HUB_ENABLE_HF_TRANSFER="1"
function Py { if (Get-Command py -ErrorAction SilentlyContinue) { "py" } elseif (Get-Command python -ErrorAction SilentlyContinue) { "python" } else { "python3" } }
$Py = Py
& $Py -m pip install --upgrade "transformers>=4.40.0" "tokenizers>=0.15.0" "huggingface_hub>=0.22.0" "onnxruntime>=1.16.0" "optimum[onnxruntime]>=1.17.0"
$UseCli = (Get-Command optimum-cli -ErrorAction SilentlyContinue) -ne $null
function Export-Model($id,$task,$out){
  if (Test-Path (Join-Path $out "model.onnx")){ return }
  if (Test-Path $out){ Remove-Item -Recurse -Force $out }
  New-Item -ItemType Directory -Force -Path $out | Out-Null
  if ($UseCli){
    optimum-cli export onnx --model $id --task $task --cache_dir $CacheDir $out
  } else {
    $p=@"
import sys
from optimum.exporters.onnx import main as onnx_export_main
onnx_export_main([""export"",""onnx"",""--model"",sys.argv[1],""--task"",sys.argv[2],""--cache_dir"",sys.argv[4],sys.argv[3]])
"@
    $tmp=[IO.Path]::GetTempFileName()+".py"; Set-Content $tmp $p; & $Py $tmp $id $task $out $CacheDir; Remove-Item $tmp -ErrorAction SilentlyContinue
  }
  if (-not (Test-Path (Join-Path $out "model.onnx"))){
    $cand = Get-ChildItem $out -Filter *.onnx -File | Select-Object -First 1
    if ($null -eq $cand){ throw "ONNX missing" }
    Move-Item $cand.FullName (Join-Path $out "model.onnx") -Force
  }
}
Export-Model $E5Id $E5Task $E5Out
Export-Model $MarkupId $MarkupTask $MarkupOut
$p2=@"
import sys, os
from transformers import AutoTokenizer, AutoConfig, AutoProcessor
hid, out = sys.argv[1:3]; os.makedirs(out, exist_ok=True)
for loader in (AutoTokenizer, AutoConfig, AutoProcessor):
    try:
        loader.from_pretrained(hid).save_pretrained(out)
    except Exception:
        continue
"@
$tmp=[IO.Path]::GetTempFileName()+".py"; Set-Content $tmp $p2
& $Py $tmp $E5Id $E5Out; & $Py $tmp $MarkupId $MarkupOut
Remove-Item $tmp -ErrorAction SilentlyContinue
$info=@"
{
  ""generated_at"": ""$(Get-Date -AsUTC -Format s)Z"",
  ""models"": [
    { ""name"": ""e5-small"", ""hf_id"": ""$E5Id"", ""task"": ""$E5Task"", ""path"": ""src/her/models/$(Split-Path -Leaf $E5Out)"" },
    { ""name"": ""markuplm-base"", ""hf_id"": ""$MarkupId"", ""task"": ""$MarkupTask"", ""path"": ""src/her/models/$(Split-Path -Leaf $MarkupOut)"" }
  ]
}
"@
Set-Content $ModelInfoPath $info -Encoding UTF8
Write-Host "✅ Models installed at $ModelsDir"
