from her.rank.fusion import rank_candidates
from her.config import DEFAULT_CONFIG


def test_rank_produces_top_candidates() -> None:
    phrase = "button"
    elements = [
        {"backendNodeId": 1, "tag": "button", "text": "First"},
        {"backendNodeId": 2, "tag": "div", "text": "Second"},
    ]
    import numpy as np
    query_vec = np.ones(16)
    element_vecs = [np.ones(16), np.zeros(16)]
    ranked = rank_candidates(phrase, elements, query_vec, element_vecs, DEFAULT_CONFIG)
    assert ranked[0]["selector"].startswith("button")