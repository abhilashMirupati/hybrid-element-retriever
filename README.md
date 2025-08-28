# Hybrid Element Retriever (HER) 🎯

[![CI](https://github.com/yourusername/her/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/her/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-80%25-brightgreen)](https://github.com/yourusername/her)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**HER** is a production-ready natural language web automation framework that converts plain English commands into robust XPath/CSS selectors with self-healing capabilities.

## ✨ Key Features

- 🗣️ **Natural Language Interface**: Write tests in plain English like "Click the login button"
- 🎯 **Automatic Locator Generation**: Creates multiple fallback XPath/CSS selectors automatically
- 🔧 **Self-Healing Locators**: Automatically adapts when UI changes, reducing test maintenance
- 🌐 **Modern Web Support**: Handles Shadow DOM, iframes, SPAs, overlays, and dynamic content
- 🚀 **Production Ready**: 80%+ test coverage, CI/CD pipeline, comprehensive documentation
- ☕ **Java Integration**: Py4J wrapper for Java/Selenium projects
- 🧠 **ML-Powered** (Optional): Semantic understanding with transformer models or deterministic fallback

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/her.git
cd her

# Install package with dependencies
pip install -e .[dev,ml]

# Install Playwright browser
python -m playwright install chromium

# (Optional) Install ML models for better accuracy
bash scripts/install_models.sh
```

### Basic Usage

#### Python API

```python
from her.cli_api import HybridClient

# Initialize client
client = HybridClient(headless=True)

# Execute natural language action
result = client.act(
    "Click the login button",
    url="https://example.com"
)
print(f"Success: {result['status']}")
print(f"Used locator: {result['locator']}")

# Query for elements without acting
elements = client.query(
    "email input field",
    url="https://example.com"
)
for elem in elements:
    print(f"Found: {elem['selector']} (confidence: {elem['score']:.1%})")

# Clean up
client.close()
```

#### Command Line Interface

```bash
# Execute an action
her act "Type john@example.com in the email field" --url https://example.com

# Query for elements
her query "submit button" --url https://example.com

# Clear cache
her cache --clear
```

## 🎯 How It Works

When you provide a command like **"Click the Send button"**, HER:

1. **Parses Intent**: Extracts action type and target description
2. **Captures Page State**: Gets DOM + Accessibility tree via Chrome DevTools Protocol
3. **Finds Elements**: Uses semantic search to identify matching elements
4. **Generates Locators**: Creates multiple XPath/CSS selectors with different strategies
5. **Verifies & Executes**: Ensures uniqueness and performs the action
6. **Self-Heals**: Falls back to alternatives if primary locator fails
7. **Learns**: Promotes successful locators for future use

## 📦 Project Structure

```
her/
├── src/her/
│   ├── cli.py              # CLI entry point
│   ├── cli_api.py          # Main Python API
│   ├── parser/             # Natural language parsing
│   ├── executor/           # Action execution
│   ├── locator/            # XPath/CSS generation
│   ├── rank/               # Element ranking & scoring
│   ├── embeddings/         # Semantic embeddings & cache
│   ├── session/            # Session & DOM management
│   └── recovery/           # Self-healing mechanisms
├── tests/                  # Comprehensive test suite (80%+ coverage)
├── examples/               # Usage examples and demos
├── java/                   # Java/Py4J wrapper
└── docs/                   # Additional documentation
```

## 🔧 Advanced Features

### Self-Healing Locators

HER automatically maintains your tests by:
- Generating 5-10 alternative locators per element
- Tracking success rates in SQLite database
- Promoting frequently successful locators
- Falling back gracefully when UI changes

### Modern Web Support

- **Shadow DOM**: Full piercing via CDP
- **IFrames**: Automatic frame traversal
- **SPAs**: Route change detection
- **Overlays**: Auto-dismissal of modals
- **Dynamic Content**: Wait strategies and retries

### Performance Optimization

- **Two-tier Caching**: In-memory LRU + persistent SQLite
- **Session Reuse**: Automatic DOM indexing
- **Lazy Loading**: On-demand model initialization
- **Batch Processing**: Efficient element processing

## 📊 Production Metrics

- **Test Coverage**: 80%+ (enforced in CI)
- **Platform Support**: Linux, Windows, macOS
- **Python Versions**: 3.9, 3.10, 3.11+
- **Browser Support**: Chromium (via Playwright)
- **Performance**: <100ms locator generation (cached)

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Install development dependencies
pip install -e .[dev]

# Run tests with coverage
pytest tests --cov=src --cov-report=term

# Format code
black src tests

# Lint code
flake8 src tests

# Type check
mypy src
```

## 📚 Documentation

- [Setup Guide](SETUP_GUIDE.md) - Detailed installation and configuration
- [API Reference](docs/api_reference.md) - Complete API documentation
- [Examples](examples/) - Sample code and use cases
- [Production Checklist](PRODUCTION_CHECKLIST.md) - Deployment guidelines

## 🎯 Use Cases

HER is perfect for:
- **Test Automation**: Write maintainable tests in plain English
- **Web Scraping**: Robust element selection that adapts to changes
- **RPA**: Automate web workflows with natural language
- **Accessibility Testing**: Leverages ARIA attributes and roles
- **Cross-browser Testing**: Unified API across browsers

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Playwright](https://playwright.dev/) for browser automation
- Uses [Transformers](https://huggingface.co/transformers) for semantic understanding
- Inspired by modern test automation best practices

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/her/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/her/discussions)
- **Email**: support@example.com

---

**Ready to revolutionize your web automation?** Get started with HER today! 🚀