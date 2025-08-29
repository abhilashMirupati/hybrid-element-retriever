from her.cli_api import HybridElementRetrieverClient as HybridClient


def test_act_and_query() -> None:
    client = HybridClient()
    # query first
    candidates = client.query("login button", url="http://example.com")
    assert isinstance(candidates, list)
    # act
    result = client.act("Click login button", url="http://example.com")
    assert result["status"] in ("ok", "fail")
