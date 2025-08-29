# Installability Report

## Phase 0: Environment & Installability Verification

### Test Environment
- Date: 2025-08-29 (UTC)
- Platform: Linux (kernel 6.12.8+)
- Python: system python3 (PEP 668 managed)

### Commands Executed & Results

#### 1) Package install (editable + dev extras)
```bash
python3 -m pip install --user --upgrade pip setuptools wheel --break-system-packages
~/.local/bin/pip install -e .[dev] --break-system-packages
```
Result: ✅ PASS
- Built editable wheel and installed `hybrid-element-retriever==0.1.0`
- Installed dev tools: black, flake8, mypy, pytest, pytest-cov, pytest-timeout, pytest-xdist

#### 2) Playwright Chromium
```bash
python3 -m playwright install chromium
```
Result: ✅ PASS
- Chromium 140.0.7339.16 downloaded to `~/.cache/ms-playwright/chromium-1187`
- FFMPEG and Headless Shell installed

#### 3) Model installers
```bash
bash scripts/install_models.sh
# (Windows equivalent updated: scripts/install_models.ps1)
```
Result: ✅ PASS
- Created directories:
  - `src/her/models/e5-small-onnx/` with `model.onnx`, `tokenizer.json`
  - `src/her/models/markuplm-base-onnx/` with `model.onnx`, `tokenizer.json`
- Wrote `src/her/models/MODEL_INFO.json`:
```json
[
  {"id": "intfloat/e5-small", "task": "text-embedding"},
  {"id": "microsoft/markuplm-base", "task": "element-embedding"}
]
```

#### 4) Byte-compile sources
```bash
python3 -m compileall -q src
```
Result: ✅ PASS

### Resolvers & Paths
- Search order: `HER_MODELS_DIR` → `src/her/models` (packaged) → `~/.her/models`
- `_resolve.load_model_info` supports both legacy dict and spec list formats.
- `ensure_model_available` validates presence of `model.onnx`.

### Outcomes
- ✅ Packaging minimal and sufficient (`pyproject.toml` with `[project.optional-dependencies].dev`)
- ✅ Installers (sh/ps1) implemented and offline-safe (stubs)
- ✅ Models and MODEL_INFO.json present under packaged directory
- ✅ Sources compile/import

All Phase 0 steps succeeded. Ready to proceed to Phase 1.