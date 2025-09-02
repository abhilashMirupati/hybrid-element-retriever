from her.cache.two_tier import TwoTierCache, get_global_cache  # re-export

__all__ = ["TwoTierCache", "get_global_cache", "set_global_cache"]


def set_global_cache(cache: TwoTierCache) -> None:
    # Mirror global set behavior for tests expecting this symbol
    try:
        import her.cache.two_tier as _ct
        _ct._global_cache = cache  # type: ignore[attr-defined]
    except Exception:
        pass
