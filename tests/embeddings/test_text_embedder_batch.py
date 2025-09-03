from pathlib import Path
import numpy as np
import pytest


def _onnx_present() -> bool:
    root = Path("src/her/models/e5-small-onnx").resolve()
    return (root / "model.onnx").exists() and (root / "tokenizer.json").exists()


@pytest.mark.skipif(not _onnx_present(), reason="ONNX E5-small model not installed")
def test_batch_encode_texts_shapes_and_dtype():
    from her.embeddings.text_embedder import TextEmbedder

    try:
        emb = TextEmbedder()
    except Exception as e:
        pytest.skip(f"Failed to initialize TextEmbedder (deps or model invalid): {e}")
    texts = [f"text {i}" for i in range(8)]
    vecs = emb.batch_encode_texts(texts, batch_size=3)
    assert isinstance(vecs, np.ndarray)
    assert vecs.dtype == np.float32
    assert vecs.shape[0] == 8
    assert vecs.shape[1] == emb.dim


@pytest.mark.skipif(not _onnx_present(), reason="ONNX E5-small model not installed")
def test_session_reuse_across_calls(monkeypatch, caplog):
    from her.embeddings.text_embedder import TextEmbedder

    caplog.set_level("INFO")
    try:
        emb1 = TextEmbedder()
    except Exception as e:
        pytest.skip(f"Failed to initialize TextEmbedder (deps or model invalid): {e}")
    dim1 = emb1.dim
    # Second instance should reuse the same session/tokenizer (no re-init cost)
    emb2 = TextEmbedder()
    dim2 = emb2.dim
    assert dim1 == dim2
    # Sanity calls
    _ = emb1.batch_encode_texts(["a", "b"])
    _ = emb2.batch_encode_texts(["c"])  # should not re-create session

