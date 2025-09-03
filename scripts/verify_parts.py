"""
Offline verifier for Part 3.
Run: python scripts/verify_parts.py
"""
import sys, os, json, numpy as np

# Add src/ to path and purge old 'her' modules to reflect local edits
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
for k in list(sys.modules.keys()):
    if k == "her" or k.startswith("her."):
        del sys.modules[k]

from her.pipeline import HybridPipeline

p = HybridPipeline(models_root=None)

# Deterministic small embeddings (no models required)
p.embed_query = lambda q: np.array([1.0, 0.0, 0.0], dtype=np.float32)
p.embed_elements = lambda els: np.array([
    [1.0, 0.0, 0.0],
    [1.0, 0.0, 0.0],
    [0.6, 0.8, 0.0],
], dtype=np.float32)

elements = [
    {"tag": "span", "role": "", "href": "", "visible": True, "bbox": {"width": 10, "height": 10}, "xpath": "/div/span"},
    {"tag": "button", "role": "button", "href": "", "visible": True, "bbox": {"width": 10, "height": 10}, "xpath": "/div/button"},
    {"tag": "a", "role": "link", "href": "https://example.com/go", "visible": True, "bbox": {"width": 5, "height": 5}, "xpath": "/div/a"},
]

out = p.query("click go", elements, top_k=3)
print(json.dumps(out, indent=2))
