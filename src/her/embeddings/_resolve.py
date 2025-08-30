from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class ResolveError(Exception):
    pass


_MODEL_INFO = 'MODEL_INFO.json'


def _base_dirs() -> List[Path]:
    dirs: List[Path] = []
    env = os.environ.get('HER_MODELS_DIR')
    if env:
        dirs.append(Path(env).expanduser().resolve())
    # Packaged models: src/her/models relative to this file
    pkg = Path(__file__).resolve().parents[1] / 'models'
    dirs.append(pkg)
    # User home fallback
    dirs.append(Path.home() / '.her' / 'models')
    out: List[Path] = []
    seen: set[str] = set()
    for p in dirs:
        s = str(p)
        if s not in seen:
            out.append(p)
            seen.add(s)
    return out


def _read_model_info(path: Path) -> List[dict]:
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except Exception as e:
        raise ResolveError(f"MODEL_INFO.json at {path} is not valid JSON: {e}")
    if not isinstance(data, list):
        raise ResolveError(f"MODEL_INFO.json at {path} must be a list of objects")
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            raise ResolveError(f"MODEL_INFO.json entry {i} at {path} is not an object")
        for req in ('id', 'alias', 'task', 'downloaded_at'):
            if req not in item:
                raise ResolveError(f"MODEL_INFO.json entry {i} missing '{req}' at {path}")
    return data


def _alias_dir(alias: str) -> str:
    # e.g., 'e5-small-onnx/model.onnx' -> 'e5-small-onnx'
    return alias.split('/', 1)[0]


def resolve_model_paths() -> Dict[str, Tuple[Optional[Path], Optional[Path]]]:
    """Resolve paths for required tasks with precedence: env -> packaged -> home.

    Returns mapping: task -> (onnx_path or None, tokenizer_path or None).
    """
    last_err: Optional[Exception] = None
    for base in _base_dirs():
        info_path = base / _MODEL_INFO
        if not info_path.exists():
            continue
        entries = _read_model_info(info_path)
        out: Dict[str, Tuple[Optional[Path], Optional[Path]]] = {}
        for it in entries:
            alias = str(it['alias'])
            task = str(it['task'])
            d = base / _alias_dir(alias)
            onnx = d / 'model.onnx'
            tok = d / 'tokenizer.json'
            out[task] = (
                onnx if onnx.exists() else None,
                tok if tok.exists() else None,
            )
        return out
    raise ResolveError(
        "MODEL_INFO.json not found in HER_MODELS_DIR, packaged src/her/models, or ~/.her/models"
    )


class ONNXResolver:
    def __init__(self, task: str, embedding_dim: int) -> None:
        self.task = task
        self.embedding_dim = int(embedding_dim)
        mp = resolve_model_paths()
        if task not in mp:
            raise ResolveError(f"Task '{task}' missing in MODEL_INFO.json")
        self.onnx_path, self.tokenizer_path = mp[task]
        # Lazy session/tokenizer initialization in embedders

    def files(self) -> Tuple[Optional[Path], Optional[Path]]:
        return self.onnx_path, self.tokenizer_path


def get_query_resolver() -> ONNXResolver:
    return ONNXResolver('text-embedding', embedding_dim=384)


def get_element_resolver() -> ONNXResolver:
    return ONNXResolver('element-embedding', embedding_dim=384)


# Back-compat alias expected by some tests
class ONNXModelResolver(ONNXResolver):
    pass


def _guess_dir_for_name(name: str) -> str:
    n = name.lower()
    if n.startswith('e5'):
        return 'e5-small-onnx'
    if 'markuplm' in n:
        return 'markuplm-base-onnx'
    return name


def resolve_model_dir(name: str) -> Path:
    # Choose first available base dir
    for base in _base_dirs():
        d = base / _guess_dir_for_name(name)
        if d.exists():
            return d
    raise ResolveError(f"Model directory for '{name}' not found")


def resolve_file(name: str, filename: str) -> Path:
    d = resolve_model_dir(name)
    f = d / filename
    if not f.exists():
        raise ResolveError(f"File '{filename}' not found in model '{name}' at {d}")
    return f


def ensure_model_available(name: str) -> Path:
    d = resolve_model_dir(name)
    f = d / 'model.onnx'
    if not f.exists():
        raise ResolveError(f"Model '{name}' missing model.onnx at {d}")
    return d


__all__ = [
    'ResolveError', 'resolve_model_paths', 'ONNXResolver', 'ONNXModelResolver',
    'get_query_resolver', 'get_element_resolver', 'resolve_model_dir', 'resolve_file', 'ensure_model_available'
]

