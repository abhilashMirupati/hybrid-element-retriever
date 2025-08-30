
import importlib

TOP_LEVEL = [
    'her',
    'her.cli_api',
    'her.pipeline',
    'her.production_client',
    'her.embeddings._resolve',
    'her.cache.two_tier',
    'her.rank.fusion',
]

def test_imports_all():
    for name in TOP_LEVEL:
        mod = importlib.import_module(name)
        assert mod is not None
