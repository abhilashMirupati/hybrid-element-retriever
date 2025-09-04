#!/usr/bin/env bash
set -euo pipefail
CACHE_DIR="${HER_CACHE_DIR:-$(pwd)/.her_cache}"
DB_PATH="${1:-$CACHE_DIR/embeddings.db}"

mkdir -p "$CACHE_DIR"
: > "$DB_PATH"   # touch; schema is created lazily by the app

echo "CacheDir: $CACHE_DIR"
echo "DB: $DB_PATH"
echo "OK"

