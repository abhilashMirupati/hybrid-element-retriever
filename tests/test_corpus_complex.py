from her.embeddings.query_embedder import QueryEmbedder
from her.embeddings.element_embedder import ElementEmbedder


def test_embed_consistency() -> None:
    qe = QueryEmbedder()
    ee = ElementEmbedder()
    phrase = "Login button"
    vec1 = qe.embed(phrase)
    vec2 = qe.embed(phrase)
    assert (vec1 == vec2).all()
    elem = {"backendNodeId": 1, "tag": "button", "text": "Login"}
    evec1 = ee.embed(elem)
    evec2 = ee.embed(elem)
    assert (evec1 == evec2).all()