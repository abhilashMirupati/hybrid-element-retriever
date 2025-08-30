
from her.cli_api import HybridClient

def _mock_dom():
    return [
        {"tag": "button", "text": "Login", "attrs": {"id": "login"}, "role": "button", "xpath": "//button[@id='login']", "depth": 3},
        {"tag": "a", "text": "Home", "attrs": {}, "role": "link", "xpath": "//a[text()='Home']", "depth": 2},
        {"tag": "input", "text": "", "attrs": {"type": "email", "id": "email"}, "role": "textbox", "xpath": "//input[@id='email']", "depth": 4},
    ]

def test_query_contract_login_xpath_present(monkeypatch):
    mock_dom = _mock_dom()
    client = HybridClient(enable_pipeline=False, enable_resilience=False)
    def fake_find_candidates(self, phrase, descriptors):
        for el in mock_dom:
            if 'login' in el.get('text', '').lower() or el.get('attrs', {}).get('id') == 'login':
                return [(el, 0.9, 'fusion')]
        return []
    client._find_candidates = fake_find_candidates.__get__(client, type(client))
    result = client.query('click login')
    assert isinstance(result, (dict, list))
    if isinstance(result, dict):
        assert 'selector' in result or 'xpath' in result
        if 'selector' in result:
            assert result['selector']
    else:
        assert result
