from __future__ import annotations
from pathlib import Path

def resolve_element_embedding(models_root: Path):
    """
    Preference:
      1) ONNX at models_root / 'markuplm-base-onnx' / 'model.onnx'   (if you add it later)
      2) Transformers at models_root / 'markuplm-base' (config.json + pytorch_model.bin/safetensors)
      Else -> raise with installer hint.
    """
    onnx_path = models_root / "markuplm-base-onnx" / "model.onnx"
    if onnx_path.is_file():
        return {"framework": "onnx", "model_path": onnx_path}

    tf_dir = models_root / "markuplm-base"
    if (tf_dir / "config.json").is_file() and (
        (tf_dir / "pytorch_model.bin").is_file() or (tf_dir / "model.safetensors").is_file()
    ):
        return {"framework": "transformers", "model_dir": tf_dir}

    raise RuntimeError(
        "Element embedding model not found.\n"
        f"Tried ONNX at: {onnx_path}\n"
        f"Tried Transformers dir: {tf_dir}\n"
        "Install models first: scripts/install_models.ps1 (Windows) or ./scripts/install_models.sh (Linux/Mac)."
    )

def resolve_text_embedding(models_root: Path):
    """
    Resolve MiniLM/E5 ONNX dir. Must include tokenizer + ONNX.
    """
    e5_dir = models_root / "e5-small-onnx"
    if e5_dir.is_dir():
        return {"model_dir": e5_dir}
    raise RuntimeError(
        f"Text embedding ONNX not found at {e5_dir}. "
        "Install models: scripts/install_models.ps1 or ./scripts/install_models.sh."
    )
