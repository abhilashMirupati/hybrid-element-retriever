# tests/core/test_cache_batching.py
"""
Tests for TwoTierCache batch operations.
- Ensures put_batch/get_batch correctness.
- Verifies memory promotion from disk.
- Validates stats() consistency.
"""

import json
import tempfile
from pathlib import Path

import pytest

from src.her.cache.two_tier import TwoTierCache


def build_cache(tmp_path):
    return TwoTierCache(
        db_path=str(tmp_path / "test_cache.sqlite"),
        memory_limit=20,
    )


def test_put_and_get_batch(tmp_path):
    cache = build_cache(tmp_path)

    # Arrange: 50 items
    items = {f"k{i}": {"v": i} for i in range(50)}
    cache.put_batch(items)

    # Act: full get_batch
    out = cache.get_batch(list(items.keys()))

    # Assert: all present
    assert set(out.keys()) == set(items.keys())
    for k, v in items.items():
        assert out[k] == v

    # Memory promotion occurred
    assert len(cache.memory_cache) > 0

    # Stats consistency
    stats = cache.stats()
    assert "mem_items" in stats
    assert "disk_items" in stats
    assert stats["disk_items"] >= len(items)


def test_miss_write_hit_cycle(tmp_path):
    cache = build_cache(tmp_path)

    # Keys that don’t exist
    miss_keys = [f"miss{i}" for i in range(5)]
    out1 = cache.get_batch(miss_keys)
    assert all(v is None for v in out1.values())

    # Write same keys
    payload = {k: {"payload": k} for k in miss_keys}
    cache.put_batch(payload)

    # Fetch again
    out2 = cache.get_batch(miss_keys)
    for k in miss_keys:
        assert out2[k] == {"payload": k}
