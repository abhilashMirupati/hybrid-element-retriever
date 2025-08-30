import numpy as np
from her.embeddings.query_embedder import QueryEmbedder
from her.embeddings.element_embedder import ElementEmbedder


def test_query_embedder_shapes_and_determinism():
  qe = QueryEmbedder(dim=64)
  a = qe.encode("hello")
  b = qe.encode("hello")
  assert isinstance(a, np.ndarray)
  assert a.shape == (64,)
  assert np.allclose(a, b)
  batch = qe.batch_encode(["a", "b"]) 
  assert batch.shape == (2, 64)


def test_element_embedder_partial_and_cache(tmp_path):
  ee = ElementEmbedder(cache_dir=tmp_path, dim=32)
  elems = [
    {"tag":"button","text":"Buy now","attributes":{"data-testid":"buy"}},
    {"tag":"input","attributes":{"name":"email"}},
  ]
  v1 = ee.batch_encode(elems)
  v2 = ee.batch_encode(elems)
  assert v1.shape == (2, 32)
  assert np.allclose(v1, v2)
