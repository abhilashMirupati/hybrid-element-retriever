def test_imports():
    import her
    from her.cli_api import HybridClient
    assert hasattr(HybridClient, 'query') and hasattr(HybridClient, 'act')
