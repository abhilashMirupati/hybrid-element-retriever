# Hybrid Element Retriever (HER) - Production Ready

[![CI](https://github.com/abhilashMirupati/hybrid-element-retriever/actions/workflows/ci.yml/badge.svg)](https://github.com/abhilashMirupati/hybrid-element-retriever/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/abhilashMirupati/hybrid-element-retriever/branch/main/graph/badge.svg)](https://codecov.io/gh/abhilashMirupati/hybrid-element-retriever)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**HER** is a production-ready system that converts natural language instructions into precise, unique, and resilient XPath/CSS locators for web automation. It combines semantic understanding with DOM analysis to reliably identify and interact with UI elements across complex web applications, including those with shadow DOM, iframes, SPAs, and dynamic content.

## 🚀 Key Features

- **Natural Language Processing**: Convert plain English steps into accurate locators
- **Multi-Model Architecture**: ONNX-optimized E5-small for query embeddings, MarkupLM-base for element understanding
- **Advanced DOM Handling**: Full CDP integration with shadow DOM piercing and iframe traversal
- **Self-Healing Locators**: Automatic recovery with fallback strategies and stateless re-snapshot
- **Performance Optimized**: Two-tier caching (LRU + SQLite), DOM delta detection, early-exit fusion
- **Production Hardened**: Overlay auto-dismissal, occlusion detection, SPA route tracking, post-action verification
- **Enterprise Ready**: Strict JSON outputs, comprehensive test coverage (80%+), Ubuntu + Windows CI/CD

## 📦 Installation

### Quick Start

```bash
# Install package
pip install hybrid-element-retriever[ml]

# Install Playwright browser
python -m playwright install chromium

# Install ONNX models
bash scripts/install_models.sh  # Linux/Mac
# or
powershell scripts/install_models.ps1  # Windows

# Verify installation
her --help
```

### Development Setup

```bash
# Clone repository
git clone https://github.com/abhilashMirupati/hybrid-element-retriever.git
cd hybrid-element-retriever

# Install with all dependencies
pip install -e ".[dev,ml,java]"

# Install Playwright
python -m playwright install chromium

# Install models (creates ONNX exports)
./scripts/install_models.sh

# Run tests with coverage
pytest tests --cov=src --cov-fail-under=80

# Build distributions
python -m build  # Python wheel/sdist
cd java && mvn package  # Java JAR
```

## 🎯 Usage

### Command Line Interface

```bash
# Execute action with natural language
her act "Click the Sign In button" --url https://example.com

# Query for elements (returns strict JSON)
her query "Find all input fields" --url https://example.com

# Manage cache
her cache --stats  # Show statistics
her cache --clear  # Clear all caches
```

### Python API

```python
from her.cli_api import HybridClient

# Initialize client
client = HybridClient(
    headless=True,           # Run browser headlessly
    timeout_ms=30000,        # Action timeout
    promotion_enabled=True   # Enable locator promotion
)

try:
    # Execute action - returns strict JSON with no empty fields
    result = client.act(
        "Enter 'user@example.com' in the email field",
        url="https://example.com"
    )
    
    if result['success']:
        print(f"✓ Action completed using: {result['used_locator']}")
        print(f"  Duration: {result['duration_ms']}ms")
        
        # Check if overlays were dismissed
        if 'dismissed_overlays' in result:
            print(f"  Auto-dismissed {len(result['dismissed_overlays'])} overlays")
    
    # Query for elements
    query_result = client.query(
        "Find all clickable buttons",
        url="https://example.com"
    )
    
    # Results are guaranteed to have no None/empty values
    for item in query_result[:3]:
        print(f"Confidence: {item['confidence']:.2f}")
        print(f"Selector: {item['selector']}")
        print(f"Element: {item['element']['tag']} - {item['element'].get('text', '')}")

finally:
    client.close()
```

### Java Integration

```java
import com.hybridclient.her.HybridClientJ;
import java.util.Map;

public class HERExample {
    public static void main(String[] args) {
        HybridClientJ client = new HybridClientJ();
        
        try {
            // Execute action
            Map<String, Object> result = client.act(
                "Click the login button",
                "https://example.com"
            );
            
            if ((Boolean) result.get("success")) {
                System.out.println("Action successful!");
                System.out.println("Locator: " + result.get("used_locator"));
            }
            
            // Query elements
            Map<String, Object> queryResult = client.query(
                "Find search box",
                "https://example.com"
            );
            
            System.out.println("Found element with confidence: " + 
                              queryResult.get("confidence"));
            
        } finally {
            client.shutdown();
        }
    }
}
```

## 🏗️ Architecture

### Core Components

- **Embeddings Module** (`src/her/embeddings/`)
  - ONNX model resolution with deterministic fallback
  - E5-small for query embeddings (384-dim)
  - MarkupLM-base for element embeddings (768-dim)
  - SHA256-based fallback when models unavailable

- **Bridge Module** (`src/her/bridge/`)
  - CDP integration for DOM/AX tree extraction
  - Shadow DOM piercing and iframe traversal
  - DOM hash computation for change detection
  - Wait-for-stable logic before snapshots

- **Ranking & Fusion** (`src/her/rank/`)
  - Semantic similarity scoring (α=1.0)
  - CSS robustness scoring (β=0.5)
  - Promotion boost scoring (γ=0.2)
  - Heuristic weighting for role/name/attributes

- **Locator Synthesis** (`src/her/locator/`)
  - Semantic-first locator generation
  - CSS selector fallback
  - Contextual XPath for disambiguation
  - Uniqueness verification per frame

- **Executor** (`src/her/executor/`)
  - Scroll-into-view and settle logic
  - Occlusion detection via elementFromPoint
  - Automatic overlay/banner dismissal
  - Post-action verification (value/URL/DOM changes)

- **Recovery & Self-Heal** (`src/her/recovery/`)
  - Fallback locator chains
  - Stateless DOM re-snapshot on failure
  - SQLite promotion persistence
  - Winner tracking and score adjustment

## 🧪 Testing

The test suite includes comprehensive real-world examples:

- **Login with Modal**: Modal popup handling, form interaction
- **SPA Route Changes**: DOM delta detection, re-indexing triggers
- **Shadow DOM Components**: Nested shadow root traversal
- **Iframe Forms**: Cross-frame element detection
- **Edge Cases**: Ambiguous elements, delayed loading, stale references

Run tests:
```bash
# All tests with coverage
pytest tests --cov=src --cov-fail-under=80

# Specific test categories
pytest tests/test_examples.py -v  # Real-world examples
pytest tests/test_embeddings.py   # Embedding tests
pytest tests/test_recovery.py     # Self-heal tests
```

## 🚢 CI/CD

GitHub Actions workflow with matrix testing:

- **OS**: Ubuntu + Windows
- **Python**: 3.9, 3.10, 3.11
- **Checks**:
  - `black --check` (formatting)
  - `flake8` (linting)
  - `mypy` (type checking)
  - `pytest --cov-fail-under=80` (tests + coverage)
  - `python -m build` (wheel + sdist)
  - `mvn package` (Java JAR)

## 📊 Performance

Target performance metrics:
- Simple DOM (<1000 elements): <200ms
- Complex DOM (>5000 elements): <800ms
- Cache hit rate: >70% after warm-up
- Locator uniqueness: 100% guaranteed
- Self-heal success rate: >85%

## 🔒 Security

- No credentials stored in code
- Secure iframe communication
- Input sanitization for XPath/CSS
- Rate limiting on cache operations
- Audit logging for all actions

## 📚 Documentation

- [SETUP_GUIDE.md](SETUP_GUIDE.md) - Detailed setup instructions
- [CHANGELOG.md](CHANGELOG.md) - Version history
- [RISKS.md](RISKS.md) - Risk assessment and mitigations
- [API Reference](docs/api.md) - Complete API documentation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Ensure all tests pass (`pytest tests`)
4. Verify formatting (`black src tests`)
5. Commit changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Hugging Face for E5 and MarkupLM models
- Playwright team for browser automation
- ONNX Runtime for inference optimization
- Py4J for Java-Python bridge

## 📞 Support

For issues, questions, or contributions:
- GitHub Issues: [Report bugs or request features](https://github.com/abhilashMirupati/hybrid-element-retriever/issues)
- Documentation: [Full documentation](https://github.com/abhilashMirupati/hybrid-element-retriever/wiki)

---

**Status**: ✅ Production Ready | **Version**: 1.0.0 | **Coverage**: 80%+