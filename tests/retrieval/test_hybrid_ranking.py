import numpy as np
from her.pipeline import HybridPipeline

def _pipeline_for_tests():
    p = HybridPipeline(models_root=None)
    p.embed_query = lambda q: np.array([1.0, 0.0, 0.0], dtype=np.float32)
    p.embed_elements = lambda els: np.array([
        [1.0, 0.0, 0.0],   # E0
        [1.0, 0.0, 0.0],   # E1 (dup)
        [0.6, 0.8, 0.0],   # E2
        [0.9, 0.1, 0.0],   # E3 (slightly different)
    ], dtype=np.float32)
    return p

def test_bonuses_href_role_tag_and_dedup():
    p = _pipeline_for_tests()
    elements = [
        {"tag": "span", "role": "", "href": "", "visible": True, "bbox": {"width": 10, "height": 10}, "xpath": "/r/span[1]"},           # E0
        {"tag": "button", "role": "button", "href": "", "visible": True, "bbox": {"width": 10, "height": 10}, "xpath": "/r/button[1]"}, # E1 (dup vec of E0, but button)
        {"tag": "a", "role": "link", "href": "https://example.com/submit", "visible": True, "bbox": {"width": 5, "height": 5}, "xpath": "/r/a[1]"}, # E2
        {"tag": "input", "role": "", "href": "", "visible": False, "bbox": {"width": 1, "height": 1}, "xpath": "/deep/child/input[1]"}, # E3
    ]
    out = p.query("click submit", elements, top_k=4)
    assert out["strategy"] == "hybrid"
    assert 0.0 <= out["confidence"] <= 1.0
    reasons = [r["reason"] for r in out["results"]]
    assert any("+href-match" in r for r in reasons)
    # dedup should prefer button(winner in tie-breakers) over span for identical vectors
    tags = [r["element"]["tag"] for r in out["results"]]
    assert "button" in tags

def test_tie_breakers_visibility_depth_area_interactivity():
    p = _pipeline_for_tests()
    elements = [
        {"tag": "span", "role": "", "href": "", "visible": False, "bbox": {"width": 100, "height": 100}, "xpath": "/deep/a/b/c/span"}, # deep, large but hidden
        {"tag": "a", "role": "link", "href": "", "visible": True, "bbox": {"width": 5, "height": 5}, "xpath": "/a"},                     # shallow, visible
    ]
    out = p.query("go", elements, top_k=2)
    # visible shallow 'a' should rank ahead of hidden deep span on ties
    assert out["results"][0]["element"]["tag"] == "a"
