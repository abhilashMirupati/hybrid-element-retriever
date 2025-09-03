import numpy as np
from her.pipeline import HybridPipeline

def test_hybrid_bonuses_and_dedup():
    p = HybridPipeline(models_root=None)
    p.embed_query = lambda q: np.array([1.0, 0.0, 0.0], dtype=np.float32)
    p.embed_elements = lambda els: np.array([
        [1.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [0.6, 0.8, 0.0],
    ], dtype=np.float32)

    elements = [
        {"tag": "span", "role": "", "href": "", "visible": True, "bbox": {"width": 10, "height": 10}, "xpath": "/div/span"},
        {"tag": "button", "role": "button", "href": "", "visible": True, "bbox": {"width": 10, "height": 10}, "xpath": "/div/button"},
        {"tag": "a", "role": "link", "href": "https://example.com/submit", "visible": True, "bbox": {"width": 5, "height": 5}, "xpath": "/div/a"},
    ]

    out = p.query("click submit", elements, top_k=3)
    assert out["strategy"] == "hybrid"
    results = out["results"]

    assert any("cosine=" in r["reason"] for r in results)
    assert any(r["element"]["tag"] == "a" and "+href-match" in r["reason"] for r in results)
    assert 0.0 <= out["confidence"] <= 1.0
