from pathlib import Path
import numpy as np
import pytest


def _installed_markuplm_dir() -> Path | None:
    d = Path("src/her/models/markuplm-base").resolve()
    if not d.is_dir():
        return None
    # Require weights to be present for a real offline load
    if not (d / "pytorch_model.bin").exists():
        return None
    if not (d / "config.json").exists():
        return None
    if not ((d / "tokenizer.json").exists() or (d / "vocab.txt").exists()):
        return None
    return d


def test_markuplm_transformers_encode_one_offline():
    d = _installed_markuplm_dir()
    if d is None:
        pytest.skip("MarkupLM Transformers model not installed; run scripts/install_models.sh")
    from her.embeddings.markuplm_embedder import MarkupLMEmbedder

    emb = MarkupLMEmbedder(d)
    vec = emb.encode({"text": "hello"})
    assert isinstance(vec, np.ndarray)
    assert vec.dtype == np.float32
    assert vec.shape == (emb.dim,)
    # Base model hidden size is 768
    assert emb.dim == 768


def test_markuplm_transformers_batch_encode():
    d = _installed_markuplm_dir()
    if d is None:
        pytest.skip("MarkupLM Transformers model not installed; run scripts/install_models.sh")
    from her.embeddings.markuplm_embedder import MarkupLMEmbedder

    emb = MarkupLMEmbedder(d)
    vecs = emb.batch_encode([{"text": "a"}, {"text": "b"}])
    assert isinstance(vecs, np.ndarray)
    assert vecs.dtype == np.float32
    assert vecs.shape == (2, emb.dim)


def test_markuplm_empty_element_zero_vector():
    d = _installed_markuplm_dir()
    if d is None:
        pytest.skip("MarkupLM Transformers model not installed; run scripts/install_models.sh")
    from her.embeddings.markuplm_embedder import MarkupLMEmbedder

    emb = MarkupLMEmbedder(d)
    v = emb.encode({})
    assert isinstance(v, np.ndarray)
    assert v.dtype == np.float32
    assert v.shape == (emb.dim,)
    assert float(v.sum()) == 0.0

