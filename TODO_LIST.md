# Implementation TODO List

## Phase 2: Full Implementation (Bottom-up Order)

### 1. Core Utilities & Config
- [ ] `src/her/config.py` - Add proper configuration management
  - **Done when:** Environment variables, paths, and constants properly defined

### 2. Model Infrastructure
- [ ] `scripts/install_models.sh` - Fix model export and add MODEL_INFO.json
  - **Done when:** Creates ONNX files and MODEL_INFO.json with HF IDs
- [ ] `scripts/install_models.ps1` - Fix model export and add MODEL_INFO.json  
  - **Done when:** Windows equivalent working identically
- [ ] `src/her/embeddings/_resolve.py` - Add HER_MODELS_DIR env check
  - **Done when:** Checks env var → packaged → home directory in order

### 3. Embeddings Layer
- [ ] `src/her/embeddings/query_embedder.py` - Use correct e5-small model
  - **Done when:** References sentence-transformers/e5-small
- [ ] `src/her/embeddings/element_embedder.py` - Verify markuplm-base usage
  - **Done when:** Properly uses microsoft/markuplm-base
- [ ] `src/her/embeddings/cache.py` - Verify two-tier cache working
  - **Done when:** LRU memory + SQLite disk cache functional

### 4. Bridge Layer (CDP)
- [ ] `src/her/bridge/cdp_bridge.py` - Remove bare except, add proper CDP calls
  - **Done when:** No bare except, proper error types
- [ ] `src/her/bridge/snapshot.py` - Use getFlattenedDocument(pierce=true)
  - **Done when:** Shadow DOM captured, iframe recursion complete

### 5. Parser Layer
- [ ] `src/her/parser/intent.py` - Verify intent parsing complete
  - **Done when:** All action types properly parsed

### 6. Ranking Layer
- [ ] `src/her/rank/fusion.py` - Fix fusion weights to α=1.0, β=0.5, γ=0.2
  - **Done when:** Correct weights applied in scoring
- [ ] `src/her/rank/heuristics.py` - Verify heuristic scoring
  - **Done when:** All heuristics properly weighted

### 7. Locator Layer
- [ ] `src/her/locator/synthesize.py` - Verify locator synthesis
  - **Done when:** Semantic → CSS → XPath order enforced
- [ ] `src/her/locator/verify.py` - Ensure frame uniqueness
  - **Done when:** Locators unique within frame context

### 8. Executor Layer
- [ ] `src/her/executor/actions.py` - Add occlusion guard, fix exceptions
  - **Done when:** elementFromPoint check, no bare except

### 9. Recovery Layer
- [ ] `src/her/recovery/self_heal.py` - Fix bare except clauses
  - **Done when:** Proper exception handling
- [ ] `src/her/recovery/promotion.py` - Verify promotion persistence
  - **Done when:** SQLite store working with correct gamma weight

### 10. Session Management
- [ ] `src/her/session/manager.py` - Add SPA route tracking
  - **Done when:** pushState/replaceState/popstate listeners active

### 11. VectorDB Layer
- [ ] `src/her/vectordb/faiss_store.py` - Verify vector store working
  - **Done when:** FAISS operations functional

### 12. API Layer
- [ ] `src/her/cli_api.py` - Ensure strict JSON output
  - **Done when:** No empty fields in JSON responses
- [ ] `src/her/cli.py` - Update for correct command structure
  - **Done when:** `her act` and `her query` commands working

### 13. Java Integration
- [ ] `java/src/main/java/com/example/her/HybridClientJ.java` - Fix package
  - **Done when:** Proper package namespace
- [ ] `src/her/gateway_server.py` - Verify Py4J gateway
  - **Done when:** Gateway properly exposes HybridClient

### 14. Test Suite
- [ ] `tests/test_*.py` - Remove placeholder tests, ensure coverage
  - **Done when:** All tests meaningful, no stubs
- [ ] `tests/conftest.py` - Add proper fixtures
  - **Done when:** Shared test infrastructure ready

### 15. CI/CD Pipeline
- [ ] `.github/workflows/ci.yml` - Add all quality gates
  - **Done when:** black, flake8, mypy, pytest --cov, build steps
- [ ] `ci/github-actions.yml` - Remove if redundant
  - **Done when:** Single workflow file

### 16. Packaging
- [ ] `pyproject.toml` - Fix console script to `her`
  - **Done when:** Entry point is `her` not `her-act`
- [ ] `setup.cfg` - Sync with pyproject.toml
  - **Done when:** Dependencies and entry points match
- [ ] `setup.py` - Ensure proper for build
  - **Done when:** `python -m build` works

### 17. Documentation
- [ ] `README.md` - Update for production status
  - **Done when:** Clear usage instructions, no TODOs
- [ ] `CHANGELOG.md` - Document all changes
  - **Done when:** Version bump with full changelist

## Acceptance Criteria

### Each file is "Done when":
1. **No placeholders:** No `...`, `TODO`, `stub`, or bare `pass`
2. **No bare except:** All exceptions properly typed
3. **Imports work:** All imports resolve correctly
4. **Tests pass:** Unit tests for the module pass
5. **Types check:** mypy reports no errors
6. **Style clean:** black and flake8 report no issues
7. **Documented:** Docstrings present and accurate

### Overall "Done when":
1. `pip install .[dev]` installs cleanly
2. `pytest --cov=src --cov-fail-under=80` passes
3. `black --check src tests` passes
4. `flake8 src tests` passes  
5. `mypy src` passes
6. `python -m build` creates wheel and sdist
7. `mvn package` builds Java JAR
8. CI workflow green on Ubuntu + Windows
9. `her act "click button" --url https://example.com` works
10. `her query "search box" --url https://example.com` returns JSON