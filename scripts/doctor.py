import json, importlib
def check(name, attr=None):
    try:
        mod = importlib.import_module(name)
        if attr:
            getattr(mod, attr)
        return True, f"{name}:{attr or '<module>'}"
    except Exception as e:
        return False, f"{name}:{attr or '<module>'} -> {e}"
checks = [
    ("her.compat", "HERPipeline"),
    ("her.embeddings.query_embedder", "QueryEmbedder"),
    ("her.embeddings.element_embedder", "ElementEmbedder"),
    ("her.vectordb.two_tier_cache", "TwoTierCache"),
    ("her.locator.verify", "verify_selector"),
    ("her.cli", None),
]
print(json.dumps({k:v for ok,(k,v) in [(check(*c),c) for c in checks]}, indent=2))
