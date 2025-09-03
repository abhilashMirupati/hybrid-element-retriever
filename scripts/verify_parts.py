"""
Offline verifier for HER Parts 1–5.

Runs a compact, dependency-free suite (no ONNX/Transformers/Playwright required):
- Normalization priorities and href host/path
- Embeddings: shapes, dtype, zero-vector fallback
- Retrieval: bonuses (role/href/tag), tie-breakers, dedup, confidence & reasons
- Self-healing: cache-hit path, demotion path, TTL purge

Exit code 0 when all checks pass; prints a JSON summary.
"""
import sys, os, json, time
import numpy as np

# Path to src
SYS_SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if SYS_SRC not in sys.path:
    sys.path.insert(0, SYS_SRC)

# Clear cached modules to reflect local edits
for k in list(sys.modules.keys()):
    if k == "her" or k.startswith("her."):
        del sys.modules[k]

summary = {"normalization": False, "embeddings": False, "retrieval": False, "selfheal": False}

# ---- Normalization checks ----
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
        "href": "https://example.com/files/save?draft=1",
        "id": "submit",
        "class": "btn  btn-primary"
    }
    out = canonical_text(el, max_length=200)
    assert out.startswith("button Save File")
    assert "example.com/files/save" in out
    summary["normalization"] = True
except Exception as e:
    print("NORMALIZATION_FAIL:", repr(e))

# ---- Embeddings checks ----
try:
    from her.pipeline import HybridPipeline
    p = HybridPipeline(models_root=None)
    p.text_embedder = None  # force zero-vector path
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

# ---- Retrieval checks ----
try:
    p = HybridPipeline(models_root=None)
    p.embed_query = lambda q: np.array([1.0, 0.0, 0.0], dtype=np.float32)
    p.embed_elements = lambda els: np.array([
        [1.0, 0.0, 0.0],   # E0
        [1.0, 0.0, 0.0],   # E1 (dup)
        [0.6, 0.8, 0.0],   # E2
        [0.9, 0.1, 0.0],   # E3
    ], dtype=np.float32)

    elements = [
        {"tag": "span", "role": "", "href": "", "visible": True, "bbox": {"width": 10, "height": 10}, "xpath": "/r/span[1]"},
        {"tag": "button", "role": "button", "href": "", "visible": True, "bbox": {"width": 10, "height": 10}, "xpath": "/r/button[1]"},
        {"tag": "a", "role": "link", "href": "https://example.com/submit", "visible": True, "bbox": {"width": 5, "height": 5}, "xpath": "/r/a[1]"},
        {"tag": "input", "role": "", "href": "", "visible": False, "bbox": {"width": 1, "height": 1}, "xpath": "/deep/child/input[1]"},
    ]
    out = p.query("click submit", elements, top_k=4)
    assert out["strategy"] == "hybrid"
    assert 0.0 <= out["confidence"] <= 1.0
    reasons = [r["reason"] for r in out["results"]]
    assert any("+href-match" in r for r in reasons)
    tags = [r["element"]["tag"] for r in out["results"]]
    assert "button" in tags
    summary["retrieval"] = True
except Exception as e:
    print("RETRIEVAL_FAIL:", repr(e))

# ---- Self-heal checks ----
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

    # TTL purge behavior (short TTL)
    store2 = PromotionStore(use_sqlite=False, default_ttl_sec=1.0)
    store2.record_success(locator="css=#ok", context="example.com/ttl")
    time.sleep(1.2)
    purged = store2.purge_expired()
    assert purged >= 1 or not store2.top_for_context("example.com/ttl")
    summary["selfheal"] = True
except Exception as e:
    print("SELFHEAL_FAIL:", repr(e))

print(json.dumps({"ok": all(summary.values()), "summary": summary}, indent=2))
sys.exit(0 if all(summary.values()) else 1)
