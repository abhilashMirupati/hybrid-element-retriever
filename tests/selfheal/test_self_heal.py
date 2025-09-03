import time
from types import SimpleNamespace

from her.recovery.promotion import PromotionStore
from her.recovery.self_heal import SelfHealer, SelfHealResult

def fake_verify(page, selector, *, strategy, require_unique=True):
    ok = selector in ("#ok", "//div[@id='ok']")
    return SimpleNamespace(ok=ok, unique=True)

def test_cache_hit_promotes_and_returns():
    store = PromotionStore(use_sqlite=False)
    healer = SelfHealer(store=store, verify_fn=fake_verify)

    ctx_url = "https://example.com/app/form"
    # Pre-insert a winning locator in the same context
    store.record_success(locator="css=#ok", context="example.com/app/form")

    res: SelfHealResult = healer.try_cached(page=None, query="click ok", context_url=ctx_url)
    assert res.ok is True
    assert res.strategy == "css"
    assert res.selector == "#ok"
    assert res.reason == "cache-hit"
    assert res.confidence_boost > 0.0

def test_demotes_bad_candidates_and_falls_through():
    store = PromotionStore(use_sqlite=False)
    healer = SelfHealer(store=store, verify_fn=fake_verify, max_candidates=5)

    ctx = "example.com/app/failure"
    store.record_success(locator="css=#bad1", context=ctx)
    store.record_success(locator="xpath=//div[@id='bad2']", context=ctx)

    res = healer.try_cached(page=None, query="something", context_url="https://example.com/app/failure")
    assert res.ok is False
    assert res.reason in ("no-cached-candidates", "candidates-failed")

def test_ttl_and_decay_behavior():
    store = PromotionStore(use_sqlite=False, default_ttl_sec=1.0)  # short TTL
    ctx = "example.com/page"

    rec = store.record_success(locator="css=#ok", context=ctx)
    assert rec.is_fresh()

    time.sleep(1.2)
    purged = store.purge_expired()
    assert purged >= 1 or not store.top_for_context(context=ctx)
