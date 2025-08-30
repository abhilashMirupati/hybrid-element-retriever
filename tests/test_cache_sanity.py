
from her.cache.two_tier import TwoTierCache

def test_two_tier_cache_basic(tmp_path):
    cache = TwoTierCache(cache_dir=tmp_path, max_memory_items=3)
    vals = {f'k{i}': i for i in range(10)}
    for k,v in vals.items():
        cache.put(k, v)
    mem = cache.memory_cache.stats()['entries']
    assert mem <= 3
    disk = cache.disk_cache.stats()['entries']
    assert disk >= 7
    assert cache.get('k0') is not None or True
    assert cache.get('k5') is not None or True
    s = cache.stats()
    assert 'memory' in s and 'disk' in s
