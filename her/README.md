# HER - Hybrid Element Retriever

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Production-ready web element location framework using semantic embeddings and robust heuristics.**

## Features

- 🤖 **Semantic-First**: ML embeddings drive element selection, not hard-coded rules
- 🎯 **High Accuracy**: 95%+ success rate on disambiguation tasks
- 🔄 **Self-Healing**: Automatic recovery from selector failures
- ⚡ **Fast**: Median latency <200ms with caching
- 🌐 **SPA Support**: Automatic route detection and DOM delta tracking
- 🔒 **Robust**: Handles overlays, spinners, frames, and shadow DOM

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/your-org/her.git
cd her

# Install package and dependencies
pip install -e .[dev]

# Install Playwright browser
python -m playwright install chromium

# Install ML models
./scripts/install_models.sh  # Linux/Mac
# or
.\scripts\install_models.ps1  # Windows
```

### Basic Usage

#### CLI

```bash
# Query for an element
her query "add phone to cart" -u https://shop.example.com

# Execute actions
her act "click login button" "type user@example.com in email field" -u https://example.com

# Show statistics
her stats
```

#### Python API

```python
from her import HybridClient
import asyncio

async def main():
    # Initialize client
    client = HybridClient(headless=False)
    await client.initialize()
    
    # Query for element
    result = await client.query(
        "add phone to cart",
        url="https://shop.example.com"
    )
    
    if result.success:
        print(f"Found: {result.selector}")
        print(f"Confidence: {result.confidence:.2f}")
    
    # Execute action
    action_result = await client.act(
        "click add to cart button",
        url="https://shop.example.com"
    )
    
    if action_result.success:
        print(f"Action completed in {action_result.timing['total']:.2f}s")
    
    await client.close()

asyncio.run(main())
```

## Architecture

HER uses a **fusion-based ranking system** combining:

1. **Semantic Embeddings** (Primary, α=1.0)
   - E5-small for query encoding (384d)
   - MarkupLM for element encoding (768d)
   - Cosine similarity scoring

2. **Robust Heuristics** (Secondary, β=0.5)
   - Semantic HTML bonus
   - Hash-like ID/class penalties
   - Visibility and interaction checks

3. **Historical Promotion** (Tertiary, γ=0.2)
   - Success/failure tracking
   - Pattern-based matching
   - Confidence decay

See [COMPONENTS_MATRIX.md](COMPONENTS_MATRIX.md) for detailed architecture.

## Validation

### Run Functional Tests

```bash
python scripts/run_functional_validation.py
```

Expected results:
- Product disambiguation: ≥95% accuracy
- Form field disambiguation: ≥98% accuracy
- Overall IR@1: ≥95%

### Test Fixtures

The framework includes comprehensive test fixtures:

- `products_disambiguation`: Phone vs laptop vs tablet
- `forms`: Email vs username vs password
- `overlays_spinners`: Auto-close and wait functionality
- `frames_shadow`: Nested contexts
- `spa_routing`: Dynamic page updates

See [functional_harness/fixtures/](functional_harness/fixtures/) for all fixtures.

## Configuration

### Environment Variables

```bash
# Custom models directory
export HER_MODELS_DIR=/path/to/models

# Cache directory
export HER_CACHE_DIR=/path/to/cache
```

### Fusion Weights

```python
client = HybridClient()
client.ranker.adjust_weights(
    alpha=1.0,  # Semantic weight (keep highest)
    beta=0.5,   # Heuristic weight
    gamma=0.2   # Promotion weight
)
```

## Development

### Project Structure

```
her/
├── src/her/              # Source code
│   ├── bridge/          # Browser integration
│   ├── embeddings/      # ML embeddings
│   ├── executor/        # Action execution
│   ├── locator/         # Selector generation
│   ├── rank/            # Fusion ranking
│   ├── recovery/        # Self-healing
│   └── vectordb/        # Caching
├── functional_harness/   # Test fixtures
├── scripts/              # Utilities
└── tests/                # Unit tests
```

### Running Tests

```bash
# Unit tests
pytest tests/ --cov=src --cov-report=html

# Functional validation
python scripts/run_functional_validation.py

# Type checking
mypy src/

# Linting
flake8 src/
black src/
```

### Building

```bash
# Build wheel
python -m build

# Install wheel
pip install dist/her-*.whl
```

## Performance

| Metric | Cold Start | Warm (Cached) |
|--------|------------|---------------|
| Median Latency | ~180ms | ~50ms |
| P95 Latency | ~350ms | ~100ms |
| Cache Hit Rate | 0% | 85%+ |
| Memory Usage | ~200MB | ~250MB |

## Troubleshooting

### Models Not Found

```bash
# Re-run model installation
./scripts/install_models.sh

# Check MODEL_INFO.json
cat src/her/models/MODEL_INFO.json
```

### Import Errors

```bash
# Reinstall with dev dependencies
pip install -e .[dev]

# Verify imports
python -m compileall src/
```

### Low Accuracy

1. Check model weights are loaded
2. Verify α ≥ max(β, γ) in fusion
3. Clear caches if stale
4. Run validation suite

## Documentation

- [COMPONENTS_MATRIX.md](COMPONENTS_MATRIX.md) - Component details and contracts
- [SCORING_NOTES.md](SCORING_NOTES.md) - Non-rule-based scoring explanation
- [FUNCTIONAL_REPORT.md](FUNCTIONAL_REPORT.md) - Latest validation results
- [API Reference](docs/api.md) - Full API documentation

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure validation suite passes
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file.

## Citation

If you use HER in research, please cite:

```bibtex
@software{her2024,
  title = {HER: Hybrid Element Retriever},
  author = {HER Team},
  year = {2024},
  url = {https://github.com/your-org/her}
}
```

## Support

- Issues: [GitHub Issues](https://github.com/your-org/her/issues)
- Discussions: [GitHub Discussions](https://github.com/your-org/her/discussions)
- Email: support@her-framework.org