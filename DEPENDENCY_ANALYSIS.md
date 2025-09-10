# HER Project Dependency Analysis

## Core Dependencies

### Required Dependencies
- **numpy**: Used throughout for array operations and ML computations
- **torch**: Required for MarkupLM embeddings
- **transformers**: Required for MarkupLM model and tokenization
- **playwright**: Required for browser automation and testing

### Optional Dependencies
- **pandas**: May be used in some modules (not found in current scan)
- **scikit-learn**: May be used for ML operations (not found in current scan)

## Module Dependency Map

### Core Modules (src/her/core/)
- **config.py**: No external dependencies
- **strict.py**: playwright (optional)
- **pipeline.py**: numpy, torch, transformers
- **runner.py**: playwright (optional)
- **hashing.py**: No external dependencies
- **compat.py**: No external dependencies
- **frames.py**: numpy

### Executor Modules (src/her/executor/)
- **main.py**: playwright, numpy
- **actions.py**: No external dependencies
- **session.py**: numpy

### Embedding Modules (src/her/embeddings/)
- **element_embedder.py**: numpy
- **query_embedder.py**: numpy
- **markuplm_embedder.py**: numpy, torch, transformers
- **text_embedder.py**: numpy, transformers

### CLI Modules (src/her/cli/)
- **main.py**: numpy
- **cli.py**: No external dependencies
- **cli_api.py**: playwright (optional)

### Other Modules
- **vectordb/faiss_store.py**: numpy
- **bridge/cdp_bridge.py**: playwright (optional)
- **browser/snapshot.py**: playwright (optional)
- **locator/verify.py**: playwright (optional)

## Installation Requirements

### Minimum Requirements
```bash
pip install numpy torch transformers playwright
```

### Development Requirements
```bash
pip install numpy torch transformers playwright pytest
```

## Testing Strategy

### Without Dependencies
- Core config and strict modules can be tested
- Basic functionality works
- Graceful degradation for missing dependencies

### With Dependencies
- Full functionality available
- All modules can be imported
- Complete testing possible

## Recommendations

1. **Add dependency checks** in critical modules
2. **Implement graceful degradation** for optional dependencies
3. **Create requirements files** for different use cases
4. **Add dependency validation** in setup scripts