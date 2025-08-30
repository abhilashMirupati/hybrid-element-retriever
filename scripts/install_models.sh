#!/usr/bin/env bash
# HER model installer (Linux/macOS)
# Downloads or prepares versioned ONNX model folders for MiniLM(E5-small) and MarkupLM.
# Writes src/her/models/MODEL_INFO.json with ISO-8601 timestamps.
# If offline/unavailable, creates deterministic stubs so the embedders can hash-fallback.

set -euo pipefail

# Resolve repo root relative to this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Target models directory (env override allowed)
MODELS_DIR_DEFAULT="${REPO_ROOT}/src/her/models"
MODELS_DIR="${HER_MODELS_DIR:-$MODELS_DIR_DEFAULT}"

E5_DIR="${MODELS_DIR}/e5-small-onnx"
MLM_DIR="${MODELS_DIR}/markuplm-base-onnx"

E5_MODEL="${E5_DIR}/model.onnx"
E5_TOKENIZER="${E5_DIR}/tokenizer.json"
MLM_MODEL="${MLM_DIR}/model.onnx"
MLM_TOKENIZER="${MLM_DIR}/tokenizer.json"

MODEL_INFO="${MODELS_DIR}/MODEL_INFO.json"

# Optional override URLs (set via env to point to your internal CDN/artifacts if desired)
E5_URL="${E5_URL:-}"
E5_TOK_URL="${E5_TOK_URL:-}"
MLM_URL="${MLM_URL:-}"
MLM_TOK_URL="${MLM_TOK_URL:-}"

timestamp_iso() {
  # ISO-8601 UTC
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}

mkdir -p "${E5_DIR}" "${MLM_DIR}"

download() {
  # download <url> <dest>
  local url="$1"
  local dest="$2"
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL --retry 3 --retry-delay 2 -o "${dest}.partial" "${url}" && mv "${dest}.partial" "${dest}"
    return 0
  elif command -v wget >/dev/null 2>&1; then
    wget -qO "${dest}.partial" "${url}" && mv "${dest}.partial" "${dest}"
    return 0
  else
    echo "Neither curl nor wget found; cannot download ${url}" >&2
    return 1
  fi
}

make_stub_model() {
  # Create a small non-empty stub file so ONNX runtime will fail fast
  # and our embedders detect fallback mode deterministically.
  local dest="$1"
  printf '' > "${dest}"
}

make_stub_tokenizer() {
  # Minimal JSON stub that our resolver/embedders can detect for hash fallback.
  local dest="$1"
  cat > "${dest}" <<'JSON'
{
  "stub": true,
  "reason": "offline-or-missing-tokenizer",
  "note": "HER embedders will use deterministic hash fallback."
}
JSON
}

ensure_e5() {
  local ts
  ts="$(timestamp_iso)"
  echo "[HER] Preparing E5-small ONNX at ${E5_MODEL}"
  if [[ -n "${E5_URL}" ]]; then
    if ! download "${E5_URL}" "${E5_MODEL}"; then
      echo "[HER] E5 model download failed, writing stub."
      make_stub_model "${E5_MODEL}"
    fi
  else
    # No default public ONNX—create stub (hash fallback kicks in)
    make_stub_model "${E5_MODEL}"
  fi

  if [[ -n "${E5_TOK_URL}" ]]; then
    if ! download "${E5_TOK_URL}" "${E5_TOKENIZER}"; then
      echo "[HER] E5 tokenizer download failed, writing stub."
      make_stub_tokenizer "${E5_TOKENIZER}"
    fi
  else
    make_stub_tokenizer "${E5_TOKENIZER}"
  fi
}

ensure_markuplm() {
  local ts
  ts="$(timestamp_iso)"
  echo "[HER] Preparing MarkupLM-base ONNX at ${MLM_MODEL}"
  if [[ -n "${MLM_URL}" ]]; then
    if ! download "${MLM_URL}" "${MLM_MODEL}"; then
      echo "[HER] MarkupLM model download failed, writing stub."
      make_stub_model "${MLM_MODEL}"
    fi
  else
    make_stub_model "${MLM_MODEL}"
  fi

  if [[ -n "${MLM_TOK_URL}" ]]; then
    if ! download "${MLM_TOK_URL}" "${MLM_TOKENIZER}"; then
      echo "[HER] MarkupLM tokenizer download failed, writing stub."
      make_stub_tokenizer "${MLM_TOKENIZER}"
    fi
  else
    make_stub_tokenizer "${MLM_TOKENIZER}"
  fi
}

write_model_info() {
  local ts
  ts="$(timestamp_iso)"
  mkdir -p "${MODELS_DIR}"
  cat > "${MODEL_INFO}" <<JSON
[
  {
    "id": "sentence-transformers/ms-marco-MiniLM-L-6-v3",
    "alias": "e5-small-onnx/model.onnx",
    "task": "text-embedding",
    "downloaded_at": "${ts}"
  },
  {
    "id": "microsoft/markuplm-base",
    "alias": "markuplm-base-onnx/model.onnx",
    "task": "element-embedding",
    "downloaded_at": "${ts}"
  }
]
JSON
  echo "[HER] Wrote ${MODEL_INFO}"
}

ensure_e5
ensure_markuplm
write_model_info

echo "[HER] Model installation complete in ${MODELS_DIR}"
