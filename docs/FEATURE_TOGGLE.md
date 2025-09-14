# HER Feature Toggle: Dual Retrieval Modes

This document describes the dual retrieval mode feature toggle implemented in HER, allowing users to choose between semantic search and exact DOM matching.

## Overview

HER now supports two distinct retrieval modes:

1. **Semantic Mode (Default)**: Uses MiniLM + MarkupLM embeddings for intelligent element matching
2. **No-Semantic Mode (Strict/BRD)**: Uses exact DOM attribute matching for precise, deterministic results

## Configuration

### Environment Variable
```bash
# Semantic mode (default)
export HER_USE_SEMANTIC_SEARCH=true

# No-semantic mode
export HER_USE_SEMANTIC_SEARCH=false
```

### CLI Flag
```bash
# Semantic mode (default)
her query "click submit button"

# No-semantic mode
her query "click submit button" --no-semantic
```

### Programmatic Configuration
```python
from src.her.config.settings import HERConfig
from src.her.core.config_service import ConfigService

# Semantic mode
config = HERConfig(use_semantic_search=True)
service = ConfigService(config)

# No-semantic mode
config = HERConfig(use_semantic_search=False)
service = ConfigService(config)
```

## Mode Details

### Semantic Mode (Default)

**Pipeline Flow:**
1. MiniLM shortlist (384-d) → FAISS vector search
2. MarkupLM rerank (768-d) → structural understanding
3. Heuristics → UI automation rules
4. XPath generation → final selector

**Characteristics:**
- Uses embeddings for semantic understanding
- Handles synonyms and related terms
- Good for general UI automation
- Requires model loading time
- Higher memory usage

**Use Cases:**
- General web automation
- Complex UI interactions
- When semantic understanding is needed
- Cross-language applications

### No-Semantic Mode (Strict/BRD)

**Pipeline Flow:**
1. DOM exact matching → attribute comparison
2. Rerank only if multiple matches → MarkupLM + heuristics
3. Accessibility fallback → icon-only elements
4. XPath generation → final selector

**Characteristics:**
- Direct attribute matching (innerText, aria-label, title, placeholder, id, name)
- Deterministic and predictable
- No model loading required
- Lower memory usage
- Faster for simple cases

**Use Cases:**
- Strict requirements (BRD compliance)
- Exact text matching needed
- Performance-critical applications
- When embeddings are not available

## Implementation Details

### Target Matcher

The no-semantic mode uses a dedicated `TargetMatcher` class that performs exact DOM matching:

```python
from src.her.locator.target_matcher import TargetMatcher

matcher = TargetMatcher(case_sensitive=False)

# Match elements against target
matches = matcher.match_elements(elements, "Submit Form")

# Extract quoted targets
target = matcher.extract_quoted_target('click "Submit"')  # Returns "Submit"
```

**Supported Attributes (in priority order):**
1. `innerText` - Element text content
2. `aria-label` - Accessibility label
3. `title` - Title attribute
4. `placeholder` - Placeholder text
5. `id` - Element ID
6. `name` - Form element name
7. `value` - Form element value
8. `data-testid` - Test ID
9. `data-test-id` - Alternative test ID

### Accessibility Fallback

When DOM matching fails, the system falls back to accessibility tree matching:

```python
from src.her.locator.target_matcher import AccessibilityFallbackMatcher

ax_matcher = AccessibilityFallbackMatcher(case_sensitive=False)

# Match accessibility elements
ax_matches = ax_matcher.match_accessibility_elements(ax_elements, "Close dialog")
```

### Pipeline Branching

The pipeline automatically branches based on configuration:

```python
# In HybridPipeline.query()
config_service = get_config_service()
use_semantic = config_service.should_use_semantic_search()

if use_semantic:
    return self._query_semantic_mode(...)
else:
    return self._query_no_semantic_mode(...)
```

### Promotion Cache Separation

Promotion cache keys are separated by mode to prevent conflicts:

```python
# Semantic mode key
semantic_key = "label:submit|button"

# No-semantic mode key  
no_semantic_key = "no-semantic:label:submit|button"
```

## Testing

### Unit Tests
```bash
# Test target matcher
python3 tests/core/test_target_matcher.py

# Test no-semantic mode
python3 tests/core/test_no_semantic_mode.py
```

### Integration Tests
```bash
# Test both modes with Verizon flow
python3 -m pytest tests/test_verizon_flow.py -v
```

### Validation
```bash
# Run comprehensive validation
python3 validate_implementation.py
```

## Performance Comparison

| Aspect | Semantic Mode | No-Semantic Mode |
|--------|---------------|------------------|
| **Startup Time** | ~38s (model loading) | ~2s (no models) |
| **Memory Usage** | ~650MB (models) | ~50MB (minimal) |
| **Query Time** | 0.1-0.5s (embeddings) | 0.01-0.1s (direct) |
| **Accuracy** | High (semantic) | Very High (exact) |
| **Flexibility** | High (synonyms) | Low (exact only) |

## Migration Guide

### From Semantic to No-Semantic

1. **Update Configuration:**
   ```python
   # Old
   config = HERConfig()
   
   # New
   config = HERConfig(use_semantic_search=False)
   ```

2. **Update Queries:**
   ```python
   # Old (semantic)
   query = "click submit button"
   
   # New (no-semantic) - use quoted targets
   query = 'click "Submit"'
   ```

3. **Update Tests:**
   ```python
   # Add mode parameter to tests
   @pytest.mark.parametrize("use_semantic_search", [True, False])
   def test_verizon_flow(use_semantic_search):
       config = HERConfig(use_semantic_search=use_semantic_search)
       # ... test logic
   ```

### From No-Semantic to Semantic

1. **Update Configuration:**
   ```python
   # Old
   config = HERConfig(use_semantic_search=False)
   
   # New (default)
   config = HERConfig()  # or HERConfig(use_semantic_search=True)
   ```

2. **Update Queries:**
   ```python
   # Old (no-semantic) - quoted targets
   query = 'click "Submit"'
   
   # New (semantic) - natural language
   query = "click submit button"
   ```

## Troubleshooting

### Common Issues

1. **No matches found in no-semantic mode:**
   - Ensure target text is quoted: `'click "Submit"'`
   - Check element visibility and attributes
   - Verify accessibility fallback is working

2. **Semantic mode not working:**
   - Verify models are installed: `bash scripts/install_models.sh`
   - Check `HER_USE_SEMANTIC_SEARCH=true`
   - Ensure sufficient memory for models

3. **Performance issues:**
   - Use no-semantic mode for simple cases
   - Enable caching for repeated queries
   - Consider model optimization

### Debug Mode

Enable debug logging to see mode selection:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Will show mode selection in logs
pipeline = HybridPipeline()
```

## Future Enhancements

1. **Hybrid Mode**: Combine both approaches for optimal results
2. **Mode Auto-Selection**: Automatically choose mode based on query complexity
3. **Performance Metrics**: Track mode performance and suggest optimal choice
4. **Advanced Fallbacks**: More sophisticated fallback strategies

## API Reference

### TargetMatcher

```python
class TargetMatcher:
    def __init__(self, case_sensitive: bool = False)
    def match_elements(self, elements: List[Dict], target: str) -> List[MatchResult]
    def extract_quoted_target(self, target: str) -> Optional[str]
    def get_best_match(self, elements: List[Dict], target: str) -> Optional[MatchResult]
```

### MatchResult

```python
@dataclass
class MatchResult:
    element: Dict[str, Any]
    score: float
    match_type: str  # 'exact', 'partial', 'word'
    matched_attribute: str
    matched_value: str
    reasons: List[str]
```

### Configuration

```python
class HERConfig:
    use_semantic_search: bool = True  # Default to semantic mode
    
    def should_use_semantic_search(self) -> bool:
        return self.use_semantic_search
```