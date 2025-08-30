"""Test for rank and locator modules."""

from her.rank.fusion import RankFusion


def test_rank_produces_top_candidates() -> None:
    """Test that rank fusion produces top candidates."""
    phrase = "button"
    elements = [
        {"backendNodeId": 1, "tagName": "button", "text": "First", "attributes": {}},
        {"backendNodeId": 2, "tagName": "div", "text": "Second", "attributes": {}},
    ]

    # Create fusion ranker
    ranker = RankFusion()

    # Create candidates with semantic and heuristic scores
    candidates = [
        (elements[0], 0.8, 0.9),  # (element, semantic_score, heuristic_score)
        (elements[1], 0.5, 0.3),
    ]

    result = ranker.rank_candidates(candidates)
    assert len(result) > 0
    assert result[0][0]["tagName"] == "button"  # Button should rank higher
