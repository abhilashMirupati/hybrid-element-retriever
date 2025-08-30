import json
from pathlib import Path

from her.vectordb.two_tier_cache import TwoTierCache
from her.embeddings._resolve import resolve_model_paths


def test_two_tier_cache_roundtrip(tmp_path: Path):
  c = TwoTierCache(tmp_path, max_memory_items=2)
  import numpy as np
  v = np.arange(4, dtype=np.float32)
  c.put('a', v, {'m': 1})
  got = c.get('a')
  assert got is not None
  assert got.dtype == v.dtype
  assert got.shape == v.shape
  assert c.get_raw('a') is not None
  s = c.stats()
  assert 'mem_items' in s and 'disk_items' in s


def test_resolver_reads_model_info():
  mp = resolve_model_paths()
  assert 'text-embedding' in mp and 'element-embedding' in mp
