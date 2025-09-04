- **Cross-platform safety:** Scripts provided for PowerShell and Bash. They avoid absolute paths by defaulting to a relative `.her_cache` (PS) or `$(pwd)/.her_cache` (Bash) and are idempotent: directory creation uses safe checks (`Test-Path`/`mkdir -p`), and file creation is a no-op on subsequent runs.

- **Env variability:** If `HER_CACHE_DIR` is unset or empty, PowerShell falls back to `.her_cache` and Bash to `$(pwd)/.her_cache`. Both allow overriding via parameter (PS: `-CacheDir`, `-DbPath`) or positional arg (Bash: `DB_PATH` as `$1`).

- **Permissions:** Scripts only ensure a writable directory and touch a SQLite file. They fail fast if the location is not writable without altering system state. No elevated privileges are required.

- **Schema creation:** Explicitly deferred. Scripts only ensure the embeddings DB file exists; the application will lazily create/upgrade the schema at runtime.

- **Scope control:** Changes limited to adding initialization scripts, reports, and updating the TODO checklist and changes report. No CI, packaging, or runtime code modified in this step.

