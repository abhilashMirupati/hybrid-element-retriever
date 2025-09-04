from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


class ResolverError(RuntimeError):
    """Raised when an embedding model cannot be resolved from local files."""
    pass


@dataclass
class ResolvedElementPaths:
    """
    Resolution result for element embedding:
      - framework: "onnx" or "transformers"
      - model_dir: directory containing transformers model (config + weights)
      - onnx:      path to ONNX model file
      - tokenizer: optional tokenizer.json path (for ONNX, if present)
    """
    framework: str
    model_dir: Path | None = None
    onnx: Path | None = None
    tokenizer: Path | None = None


def _models_root_from_env() -> Path:
    """Get models root from HER_MODELS_DIR or fall back to repo src/her/models."""
    base = os.getenv("HER_MODELS_DIR")
    if base:
        return Path(base)
    return (Path(__file__).resolve().parents[1] / "models")


def resolve_element_embedding() -> ResolvedElementPaths:
    """
    Preference order:
      1) ONNX at   <root>/markuplm-base-onnx/model.onnx
      2) HF Transformers at <root>/markuplm-base/ (config.json + weights)
      else -> ResolverError with actionable message.

    Matches tests that call resolve_element_embedding() with no args and
    expect attributes and ResolverError.
    """
    root = _models_root_from_env()

    # Try ONNX
    onnx_dir = root / "markuplm-base-onnx"
    onnx_model = onnx_dir / "model.onnx"
    onnx_tok = onnx_dir / "tokenizer.json"
    if onnx_model.is_file():
        return ResolvedElementPaths(
            framework="onnx",
            onnx=onnx_model,
            tokenizer=onnx_tok if onnx_tok.exists() else None,
        )

    # Try Transformers
    tf_dir = root / "markuplm-base"
    if (tf_dir / "config.json").is_file() and (
        (tf_dir / "pytorch_model.bin").is_file() or (tf_dir / "model.safetensors").is_file()
    ):
        return ResolvedElementPaths(framework="transformers", model_dir=tf_dir)

    # Neither present
    raise ResolverError(
        "Element model not found.\n"
        f"Tried ONNX:          {onnx_model}\n"
        f"Tried Transformers:  {tf_dir}\n"
        "Install models first via scripts/install_models.ps1 (Windows) or "
        "./scripts/install_models.sh (Linux/Mac)."
    )


def resolve_text_embedding(models_root: Path | None = None) -> dict:
    """
    Resolve MiniLM/E5 ONNX directory (for queries/text).
    Must include tokenizer + an ONNX model file.
    Returns a dict with 'model_dir'.
    """
    root = models_root or _models_root_from_env()
    e5_dir = root / "e5-small-onnx"
    if e5_dir.is_dir():
        return {"model_dir": e5_dir}
    raise ResolverError(
        f"Text embedding ONNX not found at {e5_dir}. "
        "Install models via scripts/install_models.ps1 or ./scripts/install_models.sh."
    )
