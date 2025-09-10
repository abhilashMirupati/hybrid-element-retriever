param(
  [string]$CacheDir = $env:HER_CACHE_DIR,
  [string]$DbPath = ""
)

if (-not $CacheDir -or $CacheDir.Trim() -eq "") { $CacheDir = ".her_cache" }
if (-not (Test-Path $CacheDir)) { New-Item -ItemType Directory -Path $CacheDir | Out-Null }

if (-not $DbPath -or $DbPath.Trim() -eq "") { $DbPath = Join-Path $CacheDir "embeddings.db" }

"CacheDir: $CacheDir"
"DB: $DbPath"

# Touch the DB file; the app will create schema lazily
if (-not (Test-Path $DbPath)) { New-Item -ItemType File -Path $DbPath | Out-Null }
"OK"

