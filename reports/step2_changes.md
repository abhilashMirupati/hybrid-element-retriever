- Added initialization scripts for cache and embeddings database:
  - `scripts/init_dbs.ps1` (PowerShell)
  - `scripts/init_dbs.sh` (Bash)

- Behavior and rationale:
  - Validate and create cache directory (`HER_CACHE_DIR` respected; defaults used if unset)
  - Compute DB path (`embeddings.db`) and touch file only; schema remains lazy in app code
  - Idempotent on re-runs; no destructive actions

- Minimal validation commands:

  Windows (PowerShell):
  ```powershell
  $env:HER_CACHE_DIR = (Resolve-Path ".her_cache").Path
  .\scripts\init_dbs.ps1
  Test-Path "$env:HER_CACHE_DIR\embeddings.db"
  ```

  macOS/Linux:
  ```bash
  export HER_CACHE_DIR="$(pwd)/.her_cache"
  bash scripts/init_dbs.sh
  test -f "$HER_CACHE_DIR/embeddings.db" && echo "DB touched"
  ```

