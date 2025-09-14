# HER Framework Installation and Usage Guide

## Quick Start

### 1. Install Dependencies

```bash
# Install required packages
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### 2. Configure Environment

```bash
# Copy the example configuration
cp .env.example .env

# Edit configuration as needed
nano .env
```

### 3. Basic Usage

```bash
# Semantic mode (default)
her query "click submit button"

# No-semantic mode (explicit)
her query "click 'Submit' button" --no-semantic

# With URL
her query "enter 'John' in name field" --url https://example.com --no-semantic
```

## Configuration

### Environment Variables (.env file)

```bash
# Feature Flags
HER_USE_SEMANTIC_SEARCH=true          # Use semantic mode by default
HER_USE_HIERARCHY=true                # Enable hierarchy context (default ON)
HER_USE_TWO_STAGE=false               # Use two-stage MarkupLM
HER_DISABLE_HEURISTICS=false          # Disable heuristics

# No-Semantic Mode Settings
HER_NO_SEMANTIC_CASE_SENSITIVE=false  # Case-sensitive matching
HER_NO_SEMANTIC_MIN_SCORE=0.5         # Minimum match score
HER_NO_SEMANTIC_USE_AX_FALLBACK=true  # Use accessibility fallback

# Performance Settings
HER_MAX_TEXT_LENGTH=1024              # Maximum text length
HER_MAX_ELEMENTS=1000                 # Maximum elements to process
HER_CACHE_SIZE_MB=100                 # Cache size in MB

# Browser Settings
HER_HEADLESS=true                     # Run browser in headless mode
HER_BROWSER_TIMEOUT=30000             # Browser timeout in ms

# Debug Settings
HER_DEBUG=false                       # Enable debug logging
HER_LOG_LEVEL=INFO                    # Log level (DEBUG, INFO, WARNING, ERROR)
```

## Usage Examples

### Semantic Mode (Default)

```bash
# Natural language queries
her query "find the login button"
her query "look for something to submit the form"
her query "show me where I can enter my email"

# With specific URL
her query "click on the search button" --url https://google.com
```

### No-Semantic Mode (Explicit)

```bash
# Exact text matching with quotes
her query "click 'Submit' button" --no-semantic
her query "enter 'John' in name field" --no-semantic
her query "search for 'iPhone 15'" --no-semantic

# Intent-specific queries
her query "click 'Login' button" --no-semantic
her query "enter 'password123' in password field" --no-semantic
her query "select 'United States' from country dropdown" --no-semantic
her query "validate 'Welcome John' message" --no-semantic
```

### Programmatic Usage

```python
from src.her.cli.cli_api import HybridElementRetrieverClient

# Initialize client
client = HybridElementRetrieverClient()

# Semantic mode (default)
result = client.query("click submit button")
print(result)

# No-semantic mode
client.set_semantic_mode(False)
result = client.query("click 'Submit' button")
print(result)

# Switch back to semantic mode
client.set_semantic_mode(True)
result = client.query("find the login button")
print(result)
```

## Mode Selection Guide

### Use Semantic Mode When:

- **Natural Language Queries**: "find the login button"
- **Complex Web Applications**: Dynamic content with changing text
- **Exploratory Testing**: Unknown UI patterns
- **Multi-language Interfaces**: Cross-language synonym handling
- **Rich Interactive Components**: Complex UI elements

### Use No-Semantic Mode When:

- **Test Automation**: Exact text matching with quotes
- **Performance Critical**: Need fast execution
- **Resource Constrained**: Limited memory/CPU
- **Deterministic Results**: Predictable behavior needed
- **Form Interactions**: Intent-specific matching

## Performance Comparison

| Mode | Startup Time | Memory Usage | Query Time | Accuracy (Test Automation) |
|------|-------------|--------------|------------|---------------------------|
| **Semantic** | ~38s | ~650MB | 165-330ms | 85% |
| **No-Semantic** | ~2s | ~50MB | 9-24ms | 96% |

## Troubleshooting

### Common Issues

1. **ModuleNotFoundError: No module named 'dotenv'**
   ```bash
   pip install python-dotenv
   ```

2. **Playwright not found**
   ```bash
   playwright install chromium
   ```

3. **No elements found**
   - Check if URL is accessible
   - Verify element text matches exactly (for no-semantic mode)
   - Try semantic mode for complex queries

4. **Low accuracy in no-semantic mode**
   - Use quoted text: `"click 'Submit' button"`
   - Be more specific with intent: `"enter 'John' in name field"`
   - Check if element is visible and interactive

### Debug Mode

```bash
# Enable debug logging
export HER_DEBUG=true
export HER_LOG_LEVEL=DEBUG

# Run with debug output
her query "click submit button" --no-semantic
```

## Advanced Configuration

### Custom Model Paths

```bash
# Set custom model directory
export HER_MODELS_DIR=/path/to/models

# Set custom cache directory
export HER_CACHE_DIR=/path/to/cache
```

### Performance Tuning

```bash
# Optimize for speed
export HER_USE_TWO_STAGE=false
export HER_MAX_ELEMENTS=500

# Optimize for accuracy
export HER_USE_TWO_STAGE=true
export HER_MAX_ELEMENTS=2000
```

### No-Semantic Mode Tuning

```bash
# More strict matching
export HER_NO_SEMANTIC_CASE_SENSITIVE=true
export HER_NO_SEMANTIC_MIN_SCORE=0.8

# More lenient matching
export HER_NO_SEMANTIC_CASE_SENSITIVE=false
export HER_NO_SEMANTIC_MIN_SCORE=0.3
```

## API Reference

### HybridElementRetrieverClient

```python
class HybridElementRetrieverClient:
    def __init__(self, use_semantic_search: bool = True):
        """Initialize client with semantic mode preference."""
    
    def set_semantic_mode(self, use_semantic: bool) -> None:
        """Switch between semantic and no-semantic modes."""
    
    def query(self, text: str, url: Optional[str] = None) -> Dict[str, Any]:
        """Query for elements matching the given text."""
```

### Configuration

```python
from src.her.config.settings import get_config

config = get_config()
print(config.use_semantic_search)  # True/False
print(config.use_hierarchy)        # True/False
print(config.no_semantic_min_score)  # 0.5
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.