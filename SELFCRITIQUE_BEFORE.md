# SELF-CRITIQUE BEFORE - HER Edge Case Implementation Status

## Edge-Case Matrix Status

### DOM Uniqueness
- ❌ Duplicates handling incomplete - `src/her/locator/synthesize.py` generates non-unique XPaths for duplicates
- ❌ Icon-only buttons not handled - No special logic in `src/her/descriptors/`
- ❌ Hashed IDs/classes not prioritized - `src/her/locator/synthesize.py` 
- ❌ data-testid/aria preference missing - Not prioritized in synthesis
- ❌ contenteditable support missing - Not in descriptor extraction
- ❌ SVG/canvas targeting missing - `src/her/bridge/snapshot.py` skips these

### Frames & Shadow DOM
- ❌ Nested iframes not handled - `src/her/resilience.py` has stub only
- ❌ Shadow roots not penetrated - No shadow DOM logic
- ❌ Cross-origin guard missing - No error handling for cross-origin
- ❌ frame_path not returned - Missing in verification results

### SPA Support
- ⚠️ Route listeners partially implemented - `src/her/session/enhanced_manager.py` has setup but not connected
- ❌ Hash-only navigation not detected properly
- ❌ Soft redirects not handled
- ❌ Reindex trigger incomplete

### Loading/Overlays
- ⚠️ Spinner detection exists but not integrated - `src/her/resilience.py`
- ❌ Cookie/newsletter modal auto-close not safe - Missing denylist
- ❌ Sticky header occlusion not handled
- ❌ In-flight animations not waited for

### Network/Timing
- ❌ Network idle window not enforced - `src/her/resilience.py` missing proper implementation
- ❌ Slow XHR tolerance missing
- ❌ CPU throttling not handled

### Scrolling/Visibility
- ❌ Offscreen elements not scrolled into view
- ❌ Virtualized lists not handled
- ❌ elementFromPoint occlusion not checked
- ❌ Overlapping layers not resolved

### Forms
- ⚠️ Basic form validation exists - `src/her/validators.py`
- ❌ Placeholder/label/aria-name hierarchy missing
- ❌ Masked inputs not verified properly
- ❌ Native/custom selects not differentiated
- ❌ Datepicker support missing
- ❌ File upload validation incomplete

### Auth Flows
- ❌ Login redirect handling missing
- ❌ MFA flow support missing
- ❌ Cookie/CSRF timing not handled

### i18n/a11y
- ⚠️ Basic unicode support - `src/her/validators.py`
- ❌ RTL layout not handled
- ❌ role/name vs text priority missing
- ❌ aria-expanded/pressed toggles not tracked

### Dynamic Churn
- ❌ Re-render detection missing
- ❌ Detached node recovery incomplete
- ❌ Stale handle retry missing proper implementation

### Caching/Snapshots
- ⚠️ Basic cache exists - `src/her/cache/two_tier.py`
- ❌ Cold start full embed not optimized
- ❌ Delta update for partial embed missing
- ❌ dom_hash per frame not implemented
- ❌ Promotion DB not implemented

### Strategy Fallbacks
- ⚠️ Basic fallback exists - `src/her/locator/synthesize.py`
- ❌ Proper semantic → CSS → XPath order not enforced
- ❌ Per-frame uniqueness missing
- ❌ Post-action verification incomplete

### CLI/API
- ⚠️ Basic JSON output exists - `src/her/cli_api.py`
- ❌ Strict schema validation missing
- ❌ waits/frame metadata not included
- ❌ Deterministic output not guaranteed

### Performance/Stability
- ❌ Bounded timeouts not consistent
- ⚠️ Basic retries exist but incomplete
- ❌ LRU/sqlite hit ratios not tracked
- ❌ ONNX vs hash-fallback parity not verified
- ❌ Coverage currently ~80%, needs ≥85%

## Mandatory Implementations Status

1. **Global waits** - ❌ Not implemented properly
2. **Spinner/overlay handling** - ❌ Missing safe lists and denylists
3. **SPA listeners & reindex** - ❌ Not injected or connected
4. **Partial embeddings** - ❌ No diff logic
5. **Frame-aware verification** - ❌ Missing frame metadata
6. **Post-action verification** - ❌ No self-heal or promotion DB
7. **Strict JSON contract** - ❌ Missing required fields

## Test Coverage
- ❌ None of the required test files exist
- ❌ Coverage below 85% threshold

## CI/Quality Gates
- ⚠️ Basic CI exists but incomplete - `.github/workflows/ci.yml`
- ❌ Windows matrix missing
- ❌ Model installation scripts missing
- ❌ Coverage gate not enforced

## Files to Create/Modify
- `src/her/actions.py` - NEW
- `src/her/session/snapshot.py` - MODIFY
- `src/her/vectordb/sqlite_cache.py` - MODIFY
- `src/her/embeddings/element_embedder.py` - MODIFY
- `src/her/locator/verify.py` - MODIFY
- `src/her/cli_api.py` - MODIFY
- All test files - NEW
- `.github/workflows/ci.yml` - MODIFY
- `scripts/install_models.sh` - NEW
- `scripts/install_models.ps1` - NEW