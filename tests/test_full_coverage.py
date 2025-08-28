# PLACE THIS FILE AT: tests/test_full_coverage.py

import pytest
from her.rank.fusion import RankFusion


def test_rankfusion():
    rf = RankFusion()
    res = rf.fuse({"a": [("x", 0.5), ("y", 0.2)], "b": [("x", 0.3)]})
    assert res[0][0] == "x"
