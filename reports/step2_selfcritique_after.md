- **Cross-platform safety:** PowerShell and Bash scripts both use safe primitives (`Test-Path`/`New-Item`, `mkdir -p`/shell redirection) and relative defaults. Re-running either script is idempotent: existing directories are reused and the DB file is only touched if missing (PS) or safely truncated to zero bytes (Bash) without schema involvement.

- **Env variability:** With `HER_CACHE_DIR` set, scripts honor the provided path. Without it, PowerShell defaults to `.her_cache` and Bash to `$(pwd)/.her_cache`. Optional parameters/args allow explicit overrides.

- **Permissions:** On a writable working directory, both scripts complete successfully, leaving an `embeddings.db` file that the app can open for schema creation. Failures surface clearly if the directory is not writable; no partial side effects beyond attempted directory creation and file touch.

- **Schema creation:** No schema manipulation is performed. The application remains responsible for creating and migrating tables lazily at runtime when it first opens the database.

- **Scope control:** Only Step-2 artifacts were added or edited: `scripts/init_dbs.ps1`, `scripts/init_dbs.sh`, `reports/step2_*` files, and the TODO list. No changes to CI, packaging, or application source.

