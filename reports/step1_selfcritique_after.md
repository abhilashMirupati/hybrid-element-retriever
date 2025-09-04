- **Hidden import risk & mitigation**
  - Grep commands run (0 matches):
    - CMD: grep -R -n --include=*.py -E 'from\s+her\\.embeddings\\.real_embedder' /workspace
    - CMD: grep -R -n --include=*.py -E 'from\s+her\\.embeddings\\.cache' /workspace
    - CMD: grep -R -n --include=*.py -E 'from\s+her\\.embeddings\\.enhanced_element_embedder' /workspace
    - CMD: grep -R -n --include=*.py -E 'from\s+her\\.matching\\.intelligent_matcher' /workspace

- **Signature/contract drift risk & mitigation**
  - Shim provides `.embed_query(str)` and `.embed_element(dict)` returning 384-d float32 vectors.

- **Windows/macOS/Linux path risks & mitigation**
  - No absolute paths added. Used `PYTHONPATH=/workspace/src` only for local smoke test; not required in library code.

- **Model availability risk & mitigation**
  - Confirmed: shim returns zero-vectors if `TextEmbedder` or models unavailable.

- **Scope creep risk & mitigation**
  - Only Step-1 files touched: 5 renames + 1 new shim + reports + TODO/changes.
  - No other files modified.

- **Import smoke test output**
  - Executed (isolated namespace to avoid unrelated package init):
    - `PYTHONPATH=/workspace/src python3 -c "import sys, types; her=types.ModuleType('her'); her.__path__=['/workspace/src/her']; sys.modules['her']=her; emb=types.ModuleType('her.embeddings'); emb.__path__=['/workspace/src/her/embeddings']; sys.modules['her.embeddings']=emb; from her.embeddings.minilm_embedder import MiniLMEmbedder; m=MiniLMEmbedder(); print('MiniLM shim OK; dim=', getattr(m,'dim',None))"`
  - Stdout:
    - `MiniLM shim OK; dim= 384`