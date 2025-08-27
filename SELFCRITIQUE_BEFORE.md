# Self-Critique Report - BEFORE Implementation

## Executive Summary

Initial analysis of the Hybrid Element Retriever (HER) repository reveals significant gaps and placeholder code that must be addressed before production readiness.

## Requirements Compliance Status

| Requirement | Status | Notes |
|------------|--------|-------|
| **Models & Resolver** | ⚠️ | Scripts exist but models not properly configured |
| - ONNX model export scripts | ✅ | `install_models.sh/.ps1` present |
| - E5-small for queries | ⚠️ | Script references wrong model ID |
| - MarkupLM for elements | ✅ | Correct model referenced |
| - Resolver load order | ⚠️ | Missing HER_MODELS_DIR check |
| - MODEL_INFO.json | ❌ | Not created by scripts |
| **Snapshot & DOM/AX Join** | ⚠️ | Partial implementation |
| - CDP getFlattenedDocument | ⚠️ | Using getDocument instead |
| - AX tree integration | ✅ | getFullAXTree implemented |
| - Frame path isolation | ⚠️ | TODO comment for iframe recursion |
| - Shadow DOM support | ⚠️ | Pierce flag not used correctly |
| - DOM hash per frame | ✅ | Hash computation present |
| **Retrieval & Fusion** | ⚠️ | Wrong weight values |
| - Two-tier cache | ✅ | LRU + SQLite implemented |
| - Fusion weights | ❌ | α=0.4, β=0.4, γ=0.2 (should be 1.0, 0.5, 0.2) |
| - Locator order | ✅ | Semantic → CSS → XPath |
| - Frame uniqueness | ✅ | Verify.py checks uniqueness |
| **Executor** | ⚠️ | Missing occlusion guard |
| - Scroll-into-view | ✅ | Implemented |
| - Occlusion guard | ❌ | No elementFromPoint check |
| - Overlay handler | ⚠️ | Basic implementation with bare except |
| - Post-action verify | ✅ | Verification present |
| **Self-Heal & Promotion** | ⚠️ | Bare except clauses |
| - Fallback locators | ✅ | Implemented |
| - Stateless re-snapshot | ✅ | Re-index on failure |
| - Promotion persistence | ✅ | SQLite store present |
| **Session** | ⚠️ | Missing SPA tracking |
| - SPA route tracking | ❌ | No pushState/popstate listeners |
| - Multi-frame support | ⚠️ | Partial (TODO for recursion) |
| - Auto re-index | ✅ | DOM delta detection present |
| **API/CLI** | ⚠️ | Wrong entry point name |
| - Python API | ✅ | HybridClient.act/query present |
| - CLI commands | ✅ | Commands implemented |
| - JSON output | ⚠️ | May have empty fields |
| - Entry point | ❌ | `her-act` instead of `her` |
| **Java Wrapper** | ⚠️ | Wrong package name |
| - HybridClientJ.java | ⚠️ | Package is com.example.her |
| - Py4J integration | ✅ | Basic structure present |
| - Maven build | ✅ | pom.xml configured |
| **Tests** | ❌ | Coverage likely < 80% |
| - Coverage gate | ❌ | Not enforced in CI |
| - Test cases | ⚠️ | Some placeholder tests |
| **CI/CD** | ❌ | Incomplete workflow |
| - Ubuntu + Windows | ✅ | Matrix configured |
| - Linting checks | ❌ | No black/flake8/mypy |
| - Coverage gate | ❌ | Not enforced |
| - Build artifacts | ⚠️ | Partial implementation |
| **Packaging** | ⚠️ | Inconsistent configs |
| - Console script | ❌ | `her-act` not `her` |
| - Dependencies | ⚠️ | Mismatch between files |

## Critical Issues Found

### 1. Placeholder Code (HIGH PRIORITY)
- **Files with `pass` statements:**
  - `src/her/executor/actions.py` - Lines 198, 211, 247, 363, 369, 375, 381
  - `src/her/recovery/self_heal.py` - Line 119
  - `src/her/bridge/cdp_bridge.py` - Line 181
- **Files with TODO comments:**
  - `src/her/bridge/snapshot.py` - Line 214: "TODO: Recursively capture iframe content"
- **Files with ellipsis logging:**
  - Multiple files use `...` in logging statements

### 2. Configuration Issues
- **Fusion weights incorrect:** Should be α=1.0, β=0.5, γ=0.2 (currently 0.4, 0.4, 0.2)
- **Console entry point:** Should be `her` not `her-act`
- **Package name:** Java wrapper uses `com.example.her` instead of proper namespace
- **Model IDs:** Query embedder references wrong HuggingFace model

### 3. Missing Implementations
- **Occlusion guard:** No elementFromPoint checking
- **SPA tracking:** No pushState/popstate/replaceState listeners
- **MODEL_INFO.json:** Not created by install scripts
- **CDP pierce flag:** Not using getFlattenedDocument(pierce=true)
- **CI gates:** No linting, typing, or coverage enforcement

### 4. Code Quality Issues
- **Bare except clauses:** Security and debugging risk
- **No proper error types:** Generic exceptions everywhere
- **Missing type hints:** Several functions lack proper typing
- **Import issues:** Some imports may fail

## Gap Analysis Table

| File | Problem | Impact | Priority | Fix Required |
|------|---------|--------|----------|--------------|
| `scripts/install_models.sh/.ps1` | No MODEL_INFO.json creation | Models won't resolve | HIGH | Add JSON generation |
| `src/her/embeddings/_resolve.py` | No HER_MODELS_DIR env check | Wrong load order | HIGH | Add env var check |
| `src/her/rank/fusion.py` | Wrong weight values | Poor ranking | HIGH | Fix to α=1.0, β=0.5, γ=0.2 |
| `src/her/executor/actions.py` | Bare except, no occlusion guard | Failures hidden | HIGH | Add proper exceptions |
| `src/her/bridge/snapshot.py` | No getFlattenedDocument(pierce) | Shadow DOM missed | HIGH | Use correct CDP call |
| `src/her/session/manager.py` | No SPA route tracking | Navigation missed | HIGH | Add event listeners |
| `pyproject.toml` | Wrong console script name | CLI broken | HIGH | Change to `her` |
| `setup.cfg` | Dependency mismatch | Install issues | MEDIUM | Sync with pyproject |
| `.github/workflows/ci.yml` | No quality gates | Bad code merged | HIGH | Add all checks |
| `java/*/HybridClientJ.java` | Wrong package name | Import issues | MEDIUM | Fix package |

## Import Graph Risks

### Circular Dependencies
- None detected (good!)

### Missing Dependencies
- `transformers` not in base requirements
- `tokenizers` not in base requirements  
- `huggingface_hub` not in base requirements

### Heavy Dependencies
- `torch` required for model export (should be optional)
- `onnx` required for model export (should be optional)

## Next Steps Priority Order

1. **Fix all bare except clauses** - Security critical
2. **Fix fusion weights** - Core functionality
3. **Fix console entry point** - User-facing
4. **Add MODEL_INFO.json generation** - Required for resolver
5. **Fix CDP calls for shadow DOM** - Core functionality
6. **Add occlusion guard** - Reliability
7. **Add SPA route tracking** - Feature completeness
8. **Fix CI/CD gates** - Quality assurance
9. **Clean up placeholders** - Code quality
10. **Fix package configurations** - Installation

## Acceptance Criteria

Before proceeding to implementation:
- ✅ All placeholder code removed
- ✅ All bare except clauses replaced with proper error handling
- ✅ All configuration values match specification
- ✅ All core features implemented
- ✅ CI/CD enforces all quality gates
- ✅ Tests achieve ≥80% coverage
- ✅ Package installs and runs cleanly