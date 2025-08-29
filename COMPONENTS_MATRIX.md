# Components Matrix

## Framework Component Inventory

### 1. Snapshot Component
**Files**: `src/her/bridge/snapshot.py`  
**Dependencies**: CDP protocol, Playwright  
**Contract**:
- **Input**: Page instance, pierce_shadow_dom flag
- **Output**: 
  ```json
  {
    "frames": [{
      "frame_id": "main",
      "url": "https://...",
      "dom_hash": "sha256...",
      "dom_nodes": [...],
      "ax_nodes": [...]
    }],
    "total_nodes": 1234
  }
  ```
- **Method**: `CDP DOM.getFlattenedDocument(pierce=true) + Accessibility.getFullAXTree`
- **Risk**: Low - isolated CDP calls

### 2. Session Manager
**Files**: `src/her/executor/session.py`, `src/her/session/manager.py`  
**Dependencies**: Browser events, DOM monitoring  
**Contract**:
- **Input**: Route change events (pushState/replaceState/popstate)
- **Output**: Reindex trigger, DOM delta detection
- **Methods**: 
  - `detect_spa_navigation()` - monitors route changes
  - `reindex_if_needed()` - triggers on threshold
  - DOM delta threshold: 30% change
- **Risk**: Medium - event listener management

### 3. Embeddings Resolver
**Files**: `src/her/embeddings/_resolve.py`  
**Dependencies**: File system, model loader  
**Contract**:
- **Input**: Model name (e5_small, markuplm_base)
- **Output**: Model path or fallback
- **Resolution Order**:
  1. `HER_MODELS_DIR` environment variable
  2. Packaged `src/her/models/`
  3. User home `~/.her/models/`
- **Risk**: Low - filesystem operations

### 4. Query Embedder
**Files**: `src/her/embeddings/query_embedder.py`  
**Dependencies**: ONNX Runtime, E5-small model  
**Contract**:
- **Input**: Query string
- **Output**: Intent vector [384 dimensions]
- **Model**: E5-small ONNX or deterministic hash fallback
- **Risk**: Low - pure transformation

### 5. Element Embedder
**Files**: `src/her/embeddings/element_embedder.py`  
**Dependencies**: ONNX Runtime, MarkupLM-base  
**Contract**:
- **Input**: Element descriptor {tag, text, attributes}
- **Output**: Element vector [768 dimensions]
- **Features**: Partial re-embed on DOM deltas
- **Risk**: Medium - memory management for large DOMs

### 6. Vector Cache
**Files**: `src/her/vectordb/sqlite_cache.py`, `src/her/cache/two_tier.py`  
**Dependencies**: SQLite, LRU cache  
**Contract**:
- **Input**: Key-value pairs (embeddings)
- **Output**: Cached vectors or None
- **Storage**: `.cache/embeddings/` directory
- **Methods**: `batch_get()`, `batch_put()`
- **LRU Size**: 1000 items in memory
- **Risk**: Low - standard caching

### 7. Ranking/Fusion
**Files**: `src/her/rank/fusion.py`, `src/her/rank/heuristics.py`  
**Dependencies**: NumPy for vector operations  
**Contract**:
- **Input**: Query vector, element vectors, descriptors
- **Output**: Fusion scores [0-1]
- **Weights**:
  - α=1.0 semantic similarity
  - β=0.5 robust CSS scoring
  - γ=0.2 promotion bonus
- **Rule**: Semantics MUST influence (no rule-only decisions)
- **Risk**: High - scoring accuracy critical

### 8. Locator Synthesis
**Files**: `src/her/locator/synthesize.py`  
**Dependencies**: XPath/CSS generation  
**Contract**:
- **Input**: Element descriptor
- **Output**: 
  ```json
  {
    "selector": "button[type='submit']",
    "strategy": "css|xpath",
    "meta": {...}
  }
  ```
- **Priority**: CSS primary, contextual XPath fallback
- **Risk**: Medium - uniqueness guarantee

### 9. Verification
**Files**: `src/her/locator/verify.py`  
**Dependencies**: CDP evaluation  
**Contract**:
- **Input**: Selector, frame context
- **Output**:
  ```json
  {
    "ok": true,
    "unique": true,
    "count": 1,
    "visible": true,
    "occluded": false,
    "disabled": false,
    "used_selector": "...",
    "strategy": "css",
    "explanation": "..."
  }
  ```
- **Checks**: Per-frame uniqueness, visibility, occlusion via elementFromPoint
- **Risk**: Medium - browser state dependent

### 10. Executor
**Files**: `src/her/executor/actions.py`  
**Dependencies**: Playwright actions  
**Contract**:
- **Input**: Action descriptor, target element
- **Output**: Action result with post-verification
- **Features**:
  - `wait_for_idle()` - readyState + network-idle
  - Spinner/overlay detection and wait
  - Auto-close safe modals
  - Scroll-into-view
  - Post-action verification
- **Risk**: High - user-facing actions

### 11. Self-Heal & Promotion
**Files**: `src/her/recovery/self_heal.py`, `src/her/recovery/promotion.py`  
**Dependencies**: Fallback strategies, persistence  
**Contract**:
- **Input**: Failed selector
- **Output**: Healed selector or fallback
- **Storage**: `.cache/promotion.db`
- **Integration**: γ weight in fusion scoring
- **Risk**: Medium - recovery logic

### 12. API/CLI
**Files**: `src/her/cli_api.py`, `src/her/cli.py`  
**Dependencies**: All components  
**Contract**:
- **Methods**:
  - `HybridClient.query(phrase, url)` → element + metadata
  - `HybridClient.act(step, url)` → action result
- **Output**: Strict JSON with waits, frame, post_action blocks
- **Risk**: Low - API wrapper

### 13. Java Wrapper
**Files**: `java/src/main/java/com/her/*.java`  
**Dependencies**: Py4J bridge  
**Contract**:
- **Build**: `mvn package` → thin JAR
- **Bridge**: Py4J RPC to Python backend
- **Risk**: Low - thin wrapper

## Component Dependencies Graph

```
CLI/API → Pipeline → Ranking/Fusion → Query/Element Embedders
                  ↓                 ↓
              Snapshot ←→ Session   Vector Cache
                  ↓                 ↓
              Locator Synthesis → Verification
                  ↓
              Executor → Self-Heal/Promotion
```

## Import Cycle Risks

1. **Low Risk**: 
   - Embedders (leaf components)
   - Cache (standalone)
   - Java wrapper (external)

2. **Medium Risk**:
   - Session ↔ Snapshot (managed via events)
   - Ranking ↔ Promotion (γ weight injection)

3. **High Risk**:
   - Pipeline ↔ all components (central orchestrator)
   - Mitigated by dependency injection

## Critical Contracts

### Strict JSON Output Format
```json
{
  "element": {...},
  "xpath": "//button[@type='submit']",
  "css": "button[type='submit']",
  "confidence": 0.95,
  "strategy": "css",
  "frame": {
    "id": "main",
    "path": ["main"]
  },
  "waits": {
    "idle_ms": 500,
    "spinner_gone": true,
    "overlay_dismissed": "cookie-banner"
  },
  "post_action": {
    "url_changed": false,
    "dom_mutated": true,
    "value_set": null,
    "toggled": false
  }
}
```

## Performance Contracts

- **Cold Start**: < 2s for first query
- **Warm Cache**: < 500ms for cached elements
- **Large DOM (10k nodes)**: < 5s processing
- **SPA Delta**: Only new elements embedded
- **Cache Hit Rate**: > 60% on repeated queries