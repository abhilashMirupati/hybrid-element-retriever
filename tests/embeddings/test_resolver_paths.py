from pathlib import Path
import os
import json
import shutil
import tempfile
import pytest

from her.embeddings import _resolve


def _make_root(tmp: Path) -> Path:
    root = tmp / "models"
    root.mkdir(parents=True, exist_ok=True)
    # Minimal MODEL_INFO for text to avoid unrelated failures
    (root / "e5-small-onnx").mkdir(parents=True, exist_ok=True)
    mi = [
        {
            "id": "sentence-transformers/ms-marco-MiniLM-L-6-v3",
            "alias": "e5-small-onnx/model.onnx",
            "task": "text-embedding",
            "downloaded_at": "2025-01-01T00:00:00Z",
        }
    ]
    (root / "MODEL_INFO.json").write_text(json.dumps(mi), encoding="utf-8")
    # Provide stub files for text model to satisfy exists checks (may be non-functional)
    (root / "e5-small-onnx" / "model.onnx").write_bytes(b"\x00")
    (root / "e5-small-onnx" / "tokenizer.json").write_text("{}", encoding="utf-8")
    return root


def test_resolver_transformers_fallback_when_only_markuplm_transformers_present(monkeypatch):
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        root = _make_root(tmp)
        tdir = root / "markuplm-base"
        tdir.mkdir(parents=True, exist_ok=True)
        (tdir / "config.json").write_text("{}", encoding="utf-8")
        (tdir / "tokenizer.json").write_text("{}", encoding="utf-8")
        (tdir / "pytorch_model.bin").write_bytes(b"\x00")
        monkeypatch.setenv("HER_MODELS_DIR", str(root))
        mp = _resolve.resolve_element_embedding()
        assert mp.framework == "transformers"
        assert mp.model_dir and mp.model_dir.exists()


def test_resolver_onnx_first_when_only_markuplm_onnx_present(monkeypatch):
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        root = _make_root(tmp)
        o_dir = root / "markuplm-base-onnx"
        o_dir.mkdir(parents=True, exist_ok=True)
        (o_dir / "model.onnx").write_bytes(b"\x00")
        (o_dir / "tokenizer.json").write_text("{}", encoding="utf-8")
        monkeypatch.setenv("HER_MODELS_DIR", str(root))
        mp = _resolve.resolve_element_embedding()
        assert mp.framework == "onnx"
        assert mp.onnx and mp.onnx.exists()
        assert mp.tokenizer and mp.tokenizer.exists()


def test_resolver_raises_when_neither_present(monkeypatch):
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        root = _make_root(tmp)
        monkeypatch.setenv("HER_MODELS_DIR", str(root))
        with pytest.raises(_resolve.ResolverError):
            _resolve.resolve_element_embedding()

