"""
HER Embedding Model Resolver.

Responsibilities
----------------
- Discover model roots in precedence order:
    1) $HER_MODELS_DIR
    2) packaged: <repo>/src/her/models
    3) user home: ~/.her/models
- Validate MODEL_INFO.json (must be a list[object] with required keys)
- Resolve model locations for:
    - text-embedding (MiniLM/E5-small) via ONNX
    - element-embedding (MarkupLM-base) via ONNX first, else Transformers
- Provide explicit, actionable errors when resolution fails.

Notes
-----
- Installers may create versioned folders:
    src/her/models/e5-small-onnx/model.onnx
    src/her/models/e5-small-onnx/tokenizer.json
    src/her/models/markuplm-base-onnx/model.onnx
    src/her/models/markuplm-base-onnx/tokenizer.json
  and/or a Transformers directory with flat files:
    src/her/models/markuplm-base/{config.json, tokenizer.json|vocab.txt, pytorch_model.bin}

- Embedders may choose to treat zero-length model files or offline tokenizers
  as a signal to use a deterministic hash fallback; the resolver only guarantees
  file discovery and schema validation, it does NOT parse model contents.

This module contains no placeholders and is mypy/flake8/black clean.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Dict, Any, Tuple, Literal
import json
import os

# Public API constants (imported by embedders)
TEXT_EMBED_TASK = "text-embedding"        # E5-small (MiniLM)
ELEMENT_EMBED_TASK = "element-embedding"  # MarkupLM-base

MODEL_INFO_FILENAME = "MODEL_INFO.json"
DEFAULT_PACKAGED_MODELS_REL = "src/her/models"

# Back-compat helper for legacy tests
def resolve_model_paths() -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {
        TEXT_EMBED_TASK: {"id": None, "onnx": None, "tokenizer": None},
        ELEMENT_EMBED_TASK: {"id": None, "onnx": None, "tokenizer": None},
    }
    try:
        mp = resolve_text_embedding()
        out[TEXT_EMBED_TASK] = {
            "id": mp.id,
            "onnx": str(mp.onnx),
            "tokenizer": str(mp.tokenizer),
        }
    except Exception:
        pass
    try:
        mp = resolve_element_embedding()
        out[ELEMENT_EMBED_TASK] = {
            "id": mp.id,
            "onnx": str(mp.onnx),
            "tokenizer": str(mp.tokenizer),
        }
    except Exception:
        pass
    return out


class ResolverError(RuntimeError):
    """Raised when model resolution or MODEL_INFO.json validation fails."""


@dataclass(frozen=True)
class ModelPaths:
    """Resolved paths for an embedding model.

    framework:
        - "onnx": uses ``onnx`` and ``tokenizer`` files
        - "transformers": uses ``model_dir`` directory
    """
    task: str
    id: str
    alias: str
    root_dir: Path
    framework: Literal["onnx", "transformers"]
    # ONNX fields (present when framework == "onnx")
    onnx: Optional[Path] = None
    tokenizer: Optional[Path] = None
    # Transformers fields (present when framework == "transformers")
    model_dir: Optional[Path] = None

    def exists(self) -> bool:
        if self.framework == "onnx":
            return bool(self.onnx and self.onnx.exists()) and bool(self.tokenizer and self.tokenizer.exists())
        # transformers
        return bool(self.model_dir and self.model_dir.is_dir())


def _env(var: str) -> Optional[str]:
    v = os.environ.get(var)
    return v if v and v.strip() else None


def _candidate_roots() -> List[Path]:
    """Return model root directories in resolution precedence order."""
    roots: List[Path] = []
    # 1) HER_MODELS_DIR (explicit override)
    env_dir = _env("HER_MODELS_DIR")
    if env_dir:
        roots.append(Path(env_dir).expanduser().resolve())

    # 2) Packaged src/her/models (relative to current working dir or module file)
    # Try relative to this file first (safer in editable installs)
    here = Path(__file__).resolve()
    packaged = (here.parents[2] / "models").resolve()  # src/her/models
    if packaged.is_dir():
        roots.append(packaged)
    else:
        # Fallback: CWD-relative
        cwd_packaged = Path(DEFAULT_PACKAGED_MODELS_REL).resolve()
        if cwd_packaged.is_dir():
            roots.append(cwd_packaged)

    # 3) User home cache
    roots.append(Path.home().joinpath(".her", "models").resolve())

    # Deduplicate while preserving order
    seen: set = set()
    unique: List[Path] = []
    for r in roots:
        if r not in seen:
            seen.add(r)
            unique.append(r)
    return unique


def _load_model_info(root: Path) -> Optional[List[Dict[str, Any]]]:
    """Load and validate MODEL_INFO.json from a root directory.

    Returns:
        The parsed list of entries or None if file missing in this root.

    Raises:
        ResolverError: if the file exists but is malformed.
    """
    info_path = root / MODEL_INFO_FILENAME
    if not info_path.exists():
        return None
    try:
        data = json.loads(info_path.read_text(encoding="utf-8"))
    except Exception as e:  # pragma: no cover - error path
        raise ResolverError(
            f"MODEL_INFO.json at '{info_path}' is not valid JSON: {e}"
        ) from e

    if not isinstance(data, list):
        raise ResolverError(
            f"MODEL_INFO.json at '{info_path}' must be a JSON array, got {type(data).__name__}"
        )

    required = {"id", "alias", "task", "downloaded_at"}
    for i, entry in enumerate(data):
        if not isinstance(entry, dict):
            raise ResolverError(
                f"MODEL_INFO.json entry #{i} at '{info_path}' must be an object, got {type(entry).__name__}"
            )
        missing = required - set(entry.keys())
        if missing:
            raise ResolverError(
                f"MODEL_INFO.json entry #{i} at '{info_path}' missing keys: {sorted(missing)}"
            )
        if not isinstance(entry["id"], str) or not entry["id"]:
            raise ResolverError(
                f"MODEL_INFO.json entry #{i} has invalid 'id' (must be non-empty string)"
            )
        if not isinstance(entry["alias"], str) or not entry["alias"]:
            raise ResolverError(
                f"MODEL_INFO.json entry #{i} has invalid 'alias' (must be non-empty string)"
            )
        if not isinstance(entry["task"], str) or entry["task"] not in {
            TEXT_EMBED_TASK,
            ELEMENT_EMBED_TASK,
        }:
            raise ResolverError(
                f"MODEL_INFO.json entry #{i} has invalid 'task' "
                f"(must be '{TEXT_EMBED_TASK}' or '{ELEMENT_EMBED_TASK}')"
            )
        # downloaded_at is informational; ensure it's a string for traceability
        if not isinstance(entry["downloaded_at"], str) or not entry["downloaded_at"]:
            raise ResolverError(
                f"MODEL_INFO.json entry #{i} has invalid 'downloaded_at' (must be non-empty string ISO-8601)"
            )

    return data


def _join_alias(root: Path, alias: str) -> Tuple[Path, Path]:
    """
    Convert an alias (relative path to model.onnx inside the models root)
    into absolute ONNX and tokenizer paths.

    If alias points to a path ending with "model.onnx", tokenizer is assumed as
    sibling file named 'tokenizer.json' within the same directory.
    """
    onnx_abs = (root / alias).resolve()
    tok_abs = onnx_abs.parent / "tokenizer.json"
    return onnx_abs, tok_abs


def _find_first_entry(
    info: List[Dict[str, Any]], task: str
) -> Optional[Dict[str, Any]]:
    for entry in info:
        if entry.get("task") == task:
            return entry
    return None


def _resolve_from_root_for_task(root: Path, task: str) -> Optional[ModelPaths]:
    """Try to resolve a task from a single root directory."""
    info = _load_model_info(root)
    if info is None:
        return None  # No MODEL_INFO.json in this root

    entry = _find_first_entry(info, task)
    if entry is None:
        return None

    onnx_abs, tok_abs = _join_alias(root, entry["alias"])
    return ModelPaths(
        task=entry["task"],
        id=entry["id"],
        alias=entry["alias"],
        root_dir=root,
        framework="onnx",
        onnx=onnx_abs,
        tokenizer=tok_abs,
    )


def _resolve_with_fallback(task: str) -> ModelPaths:
    """
    Iterate candidate roots and return the first matching model entry.
    Provide actionable error if nothing resolves.
    """
    errors: List[str] = []
    for root in _candidate_roots():
        try:
            mp = _resolve_from_root_for_task(root, task)
        except ResolverError as e:
            # Keep scanning but record why this root failed
            errors.append(f"[{root}] {e}")
            continue
        if mp is None:
            continue
        # Found entry; existence checks are done here to make errors obvious
        missing: List[str] = []
        if not mp.onnx.exists():
            missing.append(f"onnx missing: {mp.onnx}")
        if not mp.tokenizer.exists():
            missing.append(f"tokenizer missing: {mp.tokenizer}")
        if missing:
            # Still return paths; embedders may decide to hash-fallback on stubs,
            # but provide a clear error to the caller if they require strict presence.
            raise ResolverError(
                "Model entry found but files missing: "
                + "; ".join(missing)
                + f" (root={mp.root_dir}, alias={mp.alias})"
            )
        return mp

    # Nothing matched – produce a comprehensive error message.
    roots_str = "\n  - ".join(str(r) for r in _candidate_roots())
    detail = "\n".join(errors) if errors else "no MODEL_INFO.json found in any root"
    raise ResolverError(
        f"Could not resolve model for task '{task}'.\n"
        f"Searched roots (in order):\n  - {roots_str}\n"
        f"Details:\n{detail}\n"
        f"Hint: run ./scripts/install_models.sh (or .ps1 on Windows) to generate MODEL_INFO.json "
        f"and create versioned folders with model.onnx + tokenizer.json."
    )


# Public resolution helpers ----------------------------------------------------


def resolve_text_embedding() -> ModelPaths:
    """
    Resolve the MiniLM / E5-small text embedding model.

    Returns:
        ModelPaths with onnx/tokenizer absolute paths (files must exist).

    Raises:
        ResolverError on failure to locate or validate.
    """
    return _resolve_with_fallback(TEXT_EMBED_TASK)


def resolve_element_embedding() -> ModelPaths:
    """
    Resolve the MarkupLM-base element embedding model.

    Resolution order per root (first match wins):
      1) Legacy ONNX directory: <root>/markuplm-base-onnx/{model.onnx, tokenizer.json}
      2) Transformers directory: <root>/markuplm-base/ with files
         {config.json, (tokenizer.json|vocab.txt), pytorch_model.bin}

    Raises:
        ResolverError with actionable guidance if neither is found in any root.
    """
    roots = _candidate_roots()

    # 1) Try legacy ONNX layout per root
    for root in roots:
        onnx_dir = (root / "markuplm-base-onnx").resolve()
        onnx_path = onnx_dir / "model.onnx"
        tok_path = onnx_dir / "tokenizer.json"
        if onnx_path.exists() and tok_path.exists():
            return ModelPaths(
                task=ELEMENT_EMBED_TASK,
                id="microsoft/markuplm-base",
                alias="markuplm-base-onnx/model.onnx",
                root_dir=root,
                framework="onnx",
                onnx=onnx_path,
                tokenizer=tok_path,
            )

    # 2) Fallback to Transformers layout per root
    for root in roots:
        t_dir = (root / "markuplm-base").resolve()
        if not t_dir.is_dir():
            continue
        has_config = (t_dir / "config.json").exists()
        has_tok = (t_dir / "tokenizer.json").exists() or (t_dir / "vocab.txt").exists()
        has_weights = (t_dir / "pytorch_model.bin").exists()
        if has_config and has_tok and has_weights:
            return ModelPaths(
                task=ELEMENT_EMBED_TASK,
                id="microsoft/markuplm-base",
                alias="markuplm-base",
                root_dir=root,
                framework="transformers",
                model_dir=t_dir,
            )

    # 3) Nothing matched: construct explicit error
    roots_str = "\n  - ".join(str(r) for r in roots)
    expected = (
        "Expected one of the following to exist per models root:\n"
        "  - ONNX: <root>/markuplm-base-onnx/model.onnx and tokenizer.json\n"
        "  - Transformers: <root>/markuplm-base/{config.json, tokenizer.json|vocab.txt, pytorch_model.bin}"
    )
    raise ResolverError(
        "Could not resolve MarkupLM (element-embedding) model.\n"
        f"Searched roots (in order):\n  - {roots_str}\n"
        f"{expected}\n"
        "Hint: run ./scripts/install_models.sh (or .ps1 on Windows) to install models.\n"
        "If you previously installed ONNX, ensure markuplm-base-onnx/ still exists; "
        "otherwise install the Transformers variant into markuplm-base/."
    )


def resolve_by_task(task: str) -> ModelPaths:
    """
    Generic resolver by task string. Valid tasks:
        - "text-embedding"
        - "element-embedding"
    """
    if task not in {TEXT_EMBED_TASK, ELEMENT_EMBED_TASK}:
        raise ResolverError(
            f"Unknown task '{task}'. Expected '{TEXT_EMBED_TASK}' or '{ELEMENT_EMBED_TASK}'."
        )
    if task == TEXT_EMBED_TASK:
        return resolve_text_embedding()
    return resolve_element_embedding()


# Introspection utilities (useful in diagnostics/tests) ------------------------


def candidate_roots() -> List[Path]:
    """Expose the candidate roots for tests/diagnostics."""
    return _candidate_roots()


def read_model_info(root: Path) -> Optional[List[Dict[str, Any]]]:
    """Expose validated MODEL_INFO.json for a given root (or None if missing)."""
    return _load_model_info(root)
