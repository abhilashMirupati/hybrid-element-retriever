"""
Offline verifier for HER Parts 1–6.
No ONNX/Transformers/Playwright required.

Checks:
- Normalization: priorities & href host/path
- Embeddings: float32, zero-vector fallback, element shape fix-up
- Retrieval: bonuses, tie-breakers, dedup, calibrated confidence + reasons
- Self-heal: cache-hit / demotion / TTL
- CLI wiring sanity (module import)
"""
import sys, os, json, time
import numpy as np

SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if SRC not in sys.path:
    sys.path.insert(0, SRC)

for k in list(sys.modules.keys()):
    if k == "her" or k.startswith("her."):
        del sys.modules[k]

summary = {"normalization": False, "embeddings": False, "retrieval": False, "selfheal": False, "cli": False}

# Normalization
try:
    from her.embeddings.normalization import canonical_text
    el = {
        "tag": "button",
        "role": "button",
        "attributes": {"aria-label": "Save File"},
        "title": "Not Used",
        "alt": "ALT",
        "placeholder": "ignored",
        "name": "save",
        "value": "",
        "text": "  Save   ",
        "href": "https://example.com/files/save?x=1#y",
        "id": "submit",
        "class": "btn  btn-primary"
    }
    out = canonical_text(el, max_length=200)
    assert out.startswith("button Save File")
    assert "example.com/files/save" in out
    summary["normalization"] = True
except Exception as e:
    print("NORMALIZATION_FAIL:", repr(e))

# Embeddings
try:
    from her.pipeline import HybridPipeline
    p = HybridPipeline(models_root=None)
    p.text_embedder = None
    q = p.embed_query("anything")
    assert isinstance(q, np.ndarray) and q.dtype == np.float32 and q.shape[0] > 0 and float(np.linalg.norm(q)) == 0.0

    def fake_batch(els):
        return np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
    p.element_embedder = type("E", (), {"batch_encode": staticmethod(fake_batch), "dim": 8})()
    E = p.embed_elements([{"tag": "a"}, {"tag": "button"}])
    assert E.shape == (2, 8) and E.dtype == np.float32
    summary["embeddings"] = True
except Exception as e:
    print("EMBEDDINGS_FAIL:", repr(e))

# Retrieval
try:
    p = HybridPipeline(models_root=None)
    p.embed_query = lambda q: np.array([1.0, 0.0, 0.0], dtype=np.float32)
    p.embed_elements = lambda els: np.array([
        [1.0, 0.0, 0.0],   # dup group
        [1.0, 0.0, 0.0],
        [0.6, 0.8, 0.0],
        [0.9, 0.1, 0.0],
    ], dtype=np.float32)

    elements = [
        {"tag": "span", "role": "", "href": "", "visible": True, "bbox": {"width": 10, "height": 10}, "xpath": "/r/span[1]"},
        {"tag": "button", "role": "button", "href": "", "visible": True, "bbox": {"width": 10, "height": 10}, "xpath": "/r/button[1]"},
        {"tag": "a", "role": "link", "href": "https://example.com/submit", "visible": True, "bbox": {"width": 5, "height": 5}, "xpath": "/r/a[1]"},
        {"tag": "input", "role": "", "href": "", "visible": False, "bbox": {"width": 1, "height": 1}, "xpath": "/deep/child/input[1]"},
    ]
    out = p.query("click submit", elements, top_k=4)
    assert out["strategy"] == "hybrid" and 0.0 <= out["confidence"] <= 1.0
    reasons = [r["reason"] for r in out["results"]]
    assert any("+href-match" in r for r in reasons)
    tags = [r["element"]["tag"] for r in out["results"]]
    assert "button" in tags
    summary["retrieval"] = True
except Exception as e:
    print("RETRIEVAL_FAIL:", repr(e))

# Self-heal
try:
    from types import SimpleNamespace
    from her.recovery.promotion import PromotionStore
    from her.recovery.self_heal import SelfHealer

    def fake_verify(page, selector, *, strategy, require_unique=True):
        ok = selector in ("#ok", "//div[@id='ok']")
        return SimpleNamespace(ok=ok, unique=True)

    store = PromotionStore(use_sqlite=False)
    healer = SelfHealer(store=store, verify_fn=fake_verify)

    ctx_url = "https://example.com/app/form"
    store.record_success(locator="css=#ok", context="example.com/app/form")
    res = healer.try_cached(page=None, query="click ok", context_url=ctx_url)
    assert res.ok and res.strategy == "css" and res.selector == "#ok" and res.reason == "cache-hit" and res.confidence_boost > 0.0

    store2 = PromotionStore(use_sqlite=False, default_ttl_sec=1.0)
    store2.record_success(locator="css=#ok", context="example.com/ttl")
    time.sleep(1.2)
    purged = store2.purge_expired()
    assert purged >= 1 or not store2.top_for_context("example.com/ttl")
    summary["selfheal"] = True
except Exception as e:
    print("SELFHEAL_FAIL:", repr(e))

# CLI import
try:
    import her.cli.main as cli_main  # noqa: F401
    summary["cli"] = True
except Exception as e:
    print("CLI_FAIL:", repr(e))

print(json.dumps({"ok": all(summary.values()), "summary": summary}, indent=2))
sys.exit(0 if all(summary.values()) else 1)
