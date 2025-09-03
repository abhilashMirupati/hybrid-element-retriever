from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import os

class ResolverError(RuntimeError):
    pass

@dataclass
class ResolvedElementPaths:
    framework: str                         # "onnx" | "transformers"
    model_dir: Path | None = None          # transformers dir
    onnx: Path | None = None               # onnx model path
    tokenizer: Path | None = None          # tokenizer path (if present)

def _models_root_from_env() -> Path:
    base = os.getenv("HER_MODELS_DIR")
    if base:
        return Path(base)
    # default to repo models dir
    return (Path(__file__).resolve().parents[1] / "models")

def resolve_element_embedding() -> ResolvedElementPaths:
    root = _models_root_from_env()

    # 1) Prefer ONNX if present (as per your test)
    onnx_dir = root / "markuplm-base-onnx"
    onnx_model = onnx_dir / "model.onnx"
    onnx_tok = onnx_dir / "tokenizer.json"
    if onnx_model.is_file():
        return ResolvedElementPaths(
            framework="onnx",
            onnx=onnx_model,
            tokenizer=onnx_tok if onnx_tok.exists() else None,
        )

    # 2) Fallback to transformers dir with config+weights
    tf_dir = root / "markuplm-base"
    if (tf_dir / "config.json").is_file() and (
        (tf_dir / "pytorch_model.bin").is_file() or (tf_dir / "model.safetensors").is_file()
    ):
        return ResolvedElementPaths(framework="transformers", model_dir=tf_dir)

    # 3) Neither present
    raise ResolverError(
        "Element model not found. Expected either ONNX at "
        f"{onnx_model} or transformers directory at {tf_dir}. "
        "Install models via scripts/install_models.ps1 or ./scripts/install_models.sh."
    )
