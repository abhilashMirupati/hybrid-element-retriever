# src/her/embeddings/_resolve.py
# Model resolver for HER.
# Load order priority:
#   1) HER_MODELS_DIR (env override)
#   2) Packaged models at src/her/models/
#   3) User models at ~/.her/models/
#
# Exposes:
#   - get_models_base_dirs() -> list[Path]
#   - load_model_info() -> dict
#   - resolve_model_dir(name: str) -> Path
#   - resolve_file(name: str, filename: str) -> Path
#   - ensure_model_available(name: str) -> Path
#
# Guarantees:
#   - No placeholders or partial implementations.
#   - Clear error messages guiding how to install models via scripts/install_models.*.

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple


_MODELS_INFO_NAME = "MODEL_INFO.json"
# Names we expect after export (directories under the selected base dir)
# Keep these stable; scripts/install_models.* write to these names.
_E5_DIR = "e5-small-onnx"
_MARKUPLM_DIR = "markuplm-base-onnx"


def _repo_root_from_this_file() -> Path:
    # __file__ = src/her/embeddings/_resolve.py
    return Path(__file__).resolve().parents[2]


def _packaged_models_dir() -> Path:
    return _repo_root_from_this_file() / "src" / "her" / "models"


def _user_models_dir() -> Path:
    return Path.home() / ".her" / "models"


def get_models_base_dirs() -> List[Path]:
    """
    Return candidate base directories in priority order:
      1) HER_MODELS_DIR (if set)
      2) Packaged models in the distribution
      3) User models in ~/.her/models
    """
    env_dir = os.environ.get("HER_MODELS_DIR")
    candidates: List[Path] = []
    if env_dir:
        candidates.append(Path(env_dir).expanduser().resolve())
    candidates.append(_packaged_models_dir())
    candidates.append(_user_models_dir())
    # Deduplicate while preserving order
    deduped: List[Path] = []
    seen = set()
    for p in candidates:
        rp = str(p)
        if rp not in seen:
            deduped.append(p)
            seen.add(rp)
    return deduped


def _read_json(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _find_model_info(base: Path) -> Optional[Dict]:
    info_path = base / _MODELS_INFO_NAME
    if info_path.is_file():
        try:
            data = _read_json(info_path)
            # minimal sanity
            if isinstance(data, dict) and "models" in data:
                return data
        except Exception:
            return None
    return None


def load_model_info() -> Dict[str, Dict]:
    """
    Load MODEL_INFO.json from the first base dir that contains it.
    Returns a dict keyed by logical model names (e.g., 'e5-small', 'markuplm-base')
    with metadata {hf_id, task, path}.
    """
    for base in get_models_base_dirs():
        info = _find_model_info(base)
        if info:
            by_name: Dict[str, Dict] = {}
            for m in info.get("models", []):
                name = m.get("name")
                if not name:
                    continue
                # Normalize path to an absolute directory
                rel = m.get("path")
                if rel:
                    ap = (base / Path(rel).name).resolve()
                else:
                    # Fall back to conventional name if not provided
                    ap = (base / _guess_dir_for_name(name)).resolve()
                by_name[name] = {
                    "hf_id": m.get("hf_id"),
                    "task": m.get("task"),
                    "path": str(ap),
                }
            return by_name
    # Not found anywhere: return empty dict (caller can decide)
    return {}


def _guess_dir_for_name(name: str) -> str:
    if name.lower().startswith("e5"):
        return _E5_DIR
    if "markuplm" in name.lower():
        return _MARKUPLM_DIR
    # Default: name as-is
    return name


def resolve_model_dir(name: str) -> Path:
    """
    Resolve the directory containing an exported ONNX model by logical name.
    Tries each base dir in priority order and returns the first existing path.
    Raises FileNotFoundError with an installation hint if not found.
    """
    # Try via MODEL_INFO.json first
    info = load_model_info()
    if name in info:
        p = Path(info[name]["path"])
        if p.is_dir():
            return p

    # Fallback: conventional directory name
    wanted = _guess_dir_for_name(name)
    for base in get_models_base_dirs():
        cand = (base / wanted).resolve()
        if cand.is_dir():
            return cand

    # Not found anywhere
    raise FileNotFoundError(
        f"HER model '{name}' not found in any models directory.\n"
        f"Checked: {', '.join(str(p) for p in get_models_base_dirs())}\n"
        f"Install models with:\n"
        f"  bash scripts/install_models.sh\n"
        f"or on Windows PowerShell:\n"
        f"  ./scripts/install_models.ps1"
    )


def resolve_file(name: str, filename: str) -> Path:
    """
    Resolve a specific file within a named model directory.
    Example: resolve_file('e5-small', 'model.onnx')
    """
    mdir = resolve_model_dir(name)
    f = (mdir / filename).resolve()
    if not f.is_file():
        raise FileNotFoundError(
            f"File '{filename}' not found in model '{name}' at '{mdir}'."
        )
    return f


def ensure_model_available(name: str) -> Path:
    """
    Ensure a model is available and contains an ONNX graph file.
    Returns the model directory if OK.
    """
    mdir = resolve_model_dir(name)
    onnx = mdir / "model.onnx"
    if not onnx.is_file():
        raise FileNotFoundError(
            f"Model '{name}' at '{mdir}' does not contain 'model.onnx'. "
            f"Re-run model export scripts."
        )
    return mdir


# Convenience constants for typical HER components
E5_SMALL_NAME = "e5-small"
MARKUPLM_BASE_NAME = "markuplm-base"


__all__ = [
    "get_models_base_dirs",
    "load_model_info",
    "resolve_model_dir",
    "resolve_file",
    "ensure_model_available",
    "E5_SMALL_NAME",
    "MARKUPLM_BASE_NAME",
]
