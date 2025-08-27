# TODO Plan - Bottom-Up Implementation

## Phase 1: Foundation (Embeddings & Utils)
- [x] Fix src/her/embeddings/_resolve.py - Add ONNX path resolution + deterministic fallback
- [x] Fix src/her/embeddings/query_embedder.py - Add ONNX loading with fallback
- [x] Fix src/her/embeddings/element_embedder.py - Add proper element embedding
- [x] Update src/her/embeddings/cache.py - Ensure LRU/sqlite integration
- [x] Create scripts/install_models.sh - ONNX model download script
- [x] Create scripts/install_models.ps1 - Windows model download script
  - **Acceptance**: ✅ Deterministic vectors without ONNX; with ONNX, vectors stable; cache hits logged

## Phase 2: Bridge & Session
- [x] Fix src/her/bridge/cdp_bridge.py - Proper CDP DOM.getFlattenedDocument + AX tree
- [x] Fix src/her/bridge/snapshot.py - Join DOM/AX by backendNodeId, compute dom_hash
- [x] Fix src/her/session/manager.py - Add auto-reindex on DOM change/failure
- [x] Update src/her/descriptors.py - Complete element descriptor fields
  - **Acceptance**: ✅ First action triggers snapshot; DOM changes update dom_hash; cache key = url|frame|hash

## Phase 3: Ranking System
- [x] Fix src/her/rank/heuristics.py - Complete heuristic scoring with all signals
- [x] Fix src/her/rank/fusion.py - Implement α/β/γ weighted fusion with reasons
- [x] Create src/her/vectordb/faiss_store.py integration - Connect to ranking
  - **Acceptance**: ✅ Promotion increases score on subsequent runs; reasons logged

## Phase 4: Locator Generation
- [x] Fix src/her/locator/synthesize.py - Role→CSS→XPath progression with uniqueness
- [x] Fix src/her/locator/verify.py - Add stability and uniqueness verification
  - **Acceptance**: ✅ Returns 1 verified selector or fails with reason

## Phase 5: Executor
- [x] Fix src/her/executor/actions.py - Add scroll, visibility, overlays, retries, verification
- [x] Add timeout management and post-action checks
  - **Acceptance**: ✅ JSON includes overlay_events, retries, verification; respects timeouts

## Phase 6: Recovery System
- [x] Fix src/her/recovery/self_heal.py - Multi-strategy retry logic
- [x] Fix src/her/recovery/promotion.py - Persist promotions to sqlite/json
  - **Acceptance**: ✅ Failure triggers resnapshot + alt strategies; winners persisted

## Phase 7: Parser
- [x] Fix src/her/parser/intent.py - Complete intent parsing with all actions
  - **Acceptance**: ✅ Handles click, type, select, hover, wait with constraints

## Phase 8: CLI/API
- [x] Create proper src/her/cli_api.py - HybridClient class with frozen JSON contract
- [x] Fix src/her/cli.py - Connect to HybridClient properly
- [x] Add JSON contract fields: status, used_locator, n_best, overlay_events, retries, explanation, dom_hash, framePath
  - **Acceptance**: ✅ Examples in README produce identical JSON

## Phase 9: Java Integration
- [x] Create Python gateway server for Py4J
- [x] Update java/src/main/java/com/example/her/HybridClientJ.java
- [x] Add Java smoke tests structure
  - **Acceptance**: ✅ Smoke test calling Python client via Py4J ready

## Phase 10: CI/CD
- [x] Move ci/github-actions.yml to .github/workflows/ci.yml
- [x] Add Playwright browser installation
- [x] Add linting (black/flake8/mypy)
- [x] Add coverage enforcement (≥80%)
- [x] Add wheel/sdist build
- [x] Add Java JAR build
  - **Acceptance**: ✅ CI configured for Ubuntu/Windows matrix

## Phase 11: Tests
- [x] Implement test_embeddings.py - Test embedding modules
- [x] Implement test_bridge.py - Test DOM/AX join
- [x] Implement test_session.py - Test session management
- [x] Implement test_rank.py - Test ranking system
- [x] Implement test_locator.py - Test locator generation
- [x] Additional test files created for comprehensive coverage
  - **Acceptance**: ✅ pytest --cov=src --cov-fail-under=80 ready