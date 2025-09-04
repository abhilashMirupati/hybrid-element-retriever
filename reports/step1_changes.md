- Renamed files:
  - src/her/embeddings/real_embedder.py → src/her/embeddings/real_embedder.py.deprecated
  - src/her/embeddings/minilm_embedder.py → src/her/embeddings/minilm_embedder.py.deprecated
  - src/her/embeddings/cache.py → src/her/embeddings/cache.py.deprecated
  - src/her/embeddings/enhanced_element_embedder.py → src/her/embeddings/enhanced_element_embedder.py.deprecated
  - src/her/matching/intelligent_matcher.py → src/her/matching/intelligent_matcher.py.deprecated

- Added new file:
  - src/her/embeddings/minilm_embedder.py (compatibility shim)

- Imports updated:
  - None found by grep. If any appear later, update to `her.embeddings.minilm_embedder`.