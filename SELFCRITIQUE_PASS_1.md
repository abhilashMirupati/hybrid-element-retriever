# Self-Critique Pass 1

## Test Failures Analysis

### Critical Issues Found

#### 1. ❌ Import Errors - Pipeline Versions
**Files**: `test_final_component_analysis.py`, `test_intelligent_matching.py`  
**Error**: `ModuleNotFoundError: No module named 'her.pipeline_v2'`  
**Root Cause**: Archived `pipeline_v2.py` during reorganization  
**Fix**: Update imports to use `her.pipeline.HERPipeline`  

#### 2. ❌ Import Errors - Fusion Scorer
**Files**: `test_nlp_scoring.py`, `tests/retrieval/test_nlp_scoring.py`  
**Error**: `ImportError: cannot import name 'FusionScorer'`  
**Root Cause**: Class doesn't exist or wrong module  
**Fix**: Check actual class name in `her.rank.fusion` and update  

#### 3. ❌ Runtime Errors - Dict Attributes
**Files**: `test_all_fixes.py`, `test_complex_features.py`  
**Line**: `elem_str = str(result.element).lower()`  
**Error**: `AttributeError: 'dict' object has no attribute 'element'`  
**Root Cause**: Code outside test functions runs during collection  
**Fix**: Move code into test functions or use fixtures  

#### 4. ❌ Configuration Error - Benchmark Marker
**File**: `test_performance.py`  
**Error**: `'benchmark' not found in markers`  
**Root Cause**: Missing pytest marker configuration  
**Fix**: Add to pytest.ini or skip benchmark tests  

#### 5. ❌ Cache Parameter Error
**Files**: `tests/core/test_cold_start.py`, `test_incremental_update.py`  
**Error**: `TypeError: unexpected keyword argument 'cache_dir'`  
**Root Cause**: TwoTierCache uses `db_path` not `cache_dir`  
**Fix**: Update to use `db_path=tmp_path / "cache.db"`  

## Fixes to Implement

### Priority 1: Fix Imports
```python
# Replace in all affected files:
# OLD: from her.pipeline_v2 import HERPipelineV2
# NEW: from her.pipeline import HERPipeline as HERPipelineV2

# OLD: from her.scoring.fusion_scorer_v2 import FusionScorerV2  
# NEW: from her.rank.fusion_scorer import FusionScorer as FusionScorerV2

# OLD: from her.pipeline_production import ProductionPipeline
# NEW: from her.pipeline import HERPipeline as ProductionPipeline
```

### Priority 2: Fix Runtime Code
```python
# Move code from module level into test functions
# OLD (at module level):
result = pipeline.process(query)
elem_str = str(result.element).lower()

# NEW (inside test function):
def test_something():
    result = pipeline.process(query)
    elem_str = str(result["element"]).lower()  # Also fix dict access
```

### Priority 3: Fix Cache Usage
```python
# OLD: TwoTierCache(cache_dir=tmp_path)
# NEW: TwoTierCache(db_path=tmp_path / "cache.db")
```

### Priority 4: Add Pytest Markers
```ini
# In pytest.ini add:
markers =
    benchmark: mark test as benchmark test
    slow: mark test as slow
```

## Files Requiring Fixes

| File | Issue | Line | Fix Required |
|------|-------|------|--------------|
| `test_final_component_analysis.py` | Import pipeline_v2 | 14 | Update import |
| `test_intelligent_matching.py` | Import pipeline_v2 | 9 | Update import |
| `test_nlp_scoring.py` | Import fusion_scorer_v2 | 11 | Update import |
| `test_all_fixes.py` | Runtime code | 156 | Move to function |
| `test_complex_features.py` | Runtime code | Multiple | Move to function |
| `test_cli_api.py` | Import errors | Multiple | Fix imports |
| `tests/core/test_cold_start.py` | Cache params | 19 | Use db_path |
| `tests/retrieval/test_nlp_scoring.py` | Import FusionScorer | 5 | Check class name |

## Success Criteria

After fixes:
- ✅ All imports resolve correctly
- ✅ No runtime code outside functions
- ✅ Tests can be collected without errors
- ✅ Coverage >= 85%
- ✅ Performance tests run and report metrics
- ✅ NLP scoring accuracy >= 95%

## Next Steps

1. Implement all fixes listed above
2. Re-run test suite
3. Capture metrics
4. Create SELFCRITIQUE_PASS_2.md with results