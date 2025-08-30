
from pathlib import Path
from her.embeddings import _resolve

def test_resolver_reads_model_info():
    root = Path('src/her/models').resolve()
    info = _resolve.read_model_info(root)
    assert isinstance(info, list)
    tasks = {e['task'] for e in info}
    assert 'text-embedding' in tasks
    assert 'element-embedding' in tasks
