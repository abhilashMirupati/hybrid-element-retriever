import numpy as np
import pytest
from pathlib import Path


def _both_models_present() -> bool:
    t_ok = (Path("src/her/models/markuplm-base").resolve() / "pytorch_model.bin").exists()
    t_ok = t_ok and (Path("src/her/models/markuplm-base").resolve() / "config.json").exists()
    t_ok = t_ok and ((Path("src/her/models/markuplm-base").resolve() / "tokenizer.json").exists() or (Path("src/her/models/markuplm-base").resolve() / "vocab.txt").exists())
    q_ok = (Path("src/her/models/e5-small-onnx").resolve() / "model.onnx").exists() and (Path("src/her/models/e5-small-onnx").resolve() / "tokenizer.json").exists()
    return bool(t_ok and q_ok)


@pytest.mark.skipif(not _both_models_present(), reason="Models not installed; run scripts/install_models.sh")
def test_pipeline_smoke_embeddings():
    from her.pipeline import HybridPipeline

    pipe = HybridPipeline()
    # Two simple elements
    elements = [
        {"tag": "button", "text": "Login", "attributes": {"id": "login"}},
        {"tag": "input", "attributes": {"placeholder": "Email"}},
    ]
    # Element embeddings
    vecs = pipe.element_embedder.batch_encode(elements)
    assert isinstance(vecs, np.ndarray)
    assert vecs.dtype == np.float32
    assert vecs.shape[0] == 2 and vecs.shape[1] == getattr(pipe.element_embedder, 'dim', 768)

    # Query embeddings (batched)
    qvecs = pipe.text_embedder.batch_encode_texts(["log in"], batch_size=1)
    assert qvecs.shape[0] == 1 and qvecs.shape[1] == pipe.text_embedder.dim

