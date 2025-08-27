# 🚀 Hybrid Element Retriever (HER) - Complete Setup & Usage Guide

## 📋 Table of Contents
1. [What is HER?](#what-is-her)
2. [Quick Start](#quick-start)
3. [Detailed Installation](#detailed-installation)
4. [How It Works](#how-it-works)
5. [Usage Examples](#usage-examples)
6. [API Reference](#api-reference)
7. [Troubleshooting](#troubleshooting)
8. [Architecture Overview](#architecture-overview)

---

## 🎯 What is HER?

**Hybrid Element Retriever (HER)** is an intelligent web automation framework that converts natural language commands into precise UI actions. Instead of writing brittle XPath or CSS selectors, you simply describe what you want to do in plain English.

### Key Features:
- 🗣️ **Natural Language Input**: "Click the login button" instead of `//button[@id='login-btn']`
- 🔄 **Self-Healing Locators**: Automatically adapts when UI changes
- 🎯 **Smart Element Detection**: Combines multiple strategies to find the right element
- 📊 **Confidence Scoring**: Know how certain the system is about each element
- 🛡️ **Recovery Mechanisms**: Multiple fallback strategies when primary locator fails

### Perfect For:
- QA Engineers tired of maintaining brittle selectors
- Developers wanting to write more maintainable tests
- Teams looking to reduce test maintenance costs
- Anyone who wants to automate web interactions naturally

---

## ⚡ Quick Start

### Minimal Installation (5 minutes)

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/hybrid-element-retriever.git
cd hybrid-element-retriever

# 2. Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install minimal dependencies
pip install playwright numpy pydantic

# 4. Install Playwright browsers
python -m playwright install chromium

# 5. Run your first command!
python -m her.cli act --step "Click the search button" --url "https://google.com"
```

---

## 📦 Detailed Installation

### System Requirements

| Component | Requirement | Check Command |
|-----------|------------|---------------|
| Python | 3.9+ (3.10 recommended) | `python --version` |
| pip | Latest version | `pip --version` |
| Git | Any recent version | `git --version` |
| OS | Windows, macOS, Linux | - |
| RAM | 4GB minimum, 8GB recommended | - |
| Disk Space | 2GB for dependencies | - |

### Step 1: Environment Setup

#### Option A: Using Virtual Environment (Recommended)

```bash
# Create and activate virtual environment
python -m venv her_env

# Activate on Linux/Mac
source her_env/bin/activate

# Activate on Windows
her_env\Scripts\activate

# Verify activation (should show virtual env path)
which python  # Linux/Mac
where python  # Windows
```

#### Option B: Using Conda

```bash
# Create conda environment
conda create -n her python=3.10
conda activate her
```

### Step 2: Install Dependencies

#### Core Dependencies (Required)

```bash
# Install core packages
pip install playwright==1.39.0
pip install numpy==1.23.5
pip install pydantic==1.10.12

# Install Playwright browsers
python -m playwright install chromium
# Optional: Install all browsers
# python -m playwright install
```

#### ML Dependencies (Optional - for better accuracy)

```bash
# For embedding-based element matching
pip install onnxruntime==1.15.0
pip install faiss-cpu==1.7.3

# Download pre-trained models (optional)
chmod +x scripts/install_models.sh
./scripts/install_models.sh  # Linux/Mac

# On Windows
powershell -ExecutionPolicy Bypass -File scripts/install_models.ps1
```

#### Development Dependencies (For contributors)

```bash
pip install pytest pytest-cov black flake8 mypy
```

### Step 3: Verify Installation

```bash
# Test import
python -c "from her.cli_api import HybridClient; print('✅ Import successful')"

# Test Playwright
python -c "from playwright.sync_api import sync_playwright; print('✅ Playwright ready')"

# Run test suite
pytest tests/test_basic.py -v
```

---

## 🧠 How It Works

### The HER Pipeline

```
Natural Language Input → Intent Parsing → Element Detection → Action Execution
        ↓                      ↓                ↓                    ↓
   "Click login"          Extract action    Find candidates     Perform click
                          & target phrase    Score & rank      Verify success
```

### 1. **Natural Language Processing**
```python
Input: "Type 'john@example.com' into the email field"
   ↓
Parsed: {
    action: "type",
    target: "email field",
    args: "john@example.com"
}
```

### 2. **Element Detection Strategies**

| Strategy | Description | Example |
|----------|-------------|---------|
| **Semantic** | Meaning-based matching | "login" matches button with text "Sign In" |
| **Heuristic** | Rule-based scoring | Prefers buttons for "click" actions |
| **Accessibility** | ARIA attributes | Uses role="button" for button detection |
| **Visual** | Position & visibility | Ensures element is visible and clickable |

### 3. **Self-Healing Mechanism**

When a locator fails, HER automatically tries:
1. Relaxing exact matches to partial matches
2. Removing position indices
3. Using parent/child relationships
4. Trying alternative attributes
5. Re-indexing the page and retrying

---

## 💻 Usage Examples

### Basic Usage

#### Example 1: Simple Click Action

```python
from her.cli_api import HybridClient

# Initialize client
client = HybridClient(headless=False)  # Set headless=True for CI/CD

# Navigate and click
result = client.act(
    step="Click the login button",
    url="https://example.com"
)

# Check result
if result["status"] == "success":
    print(f"✅ Clicked using: {result['used_locator']}")
    print(f"Confidence: {result['confidence']}")
else:
    print(f"❌ Failed: {result['explanation']}")
```

#### Example 2: Form Filling

```python
# Fill a complete form
steps = [
    ("Type 'John Doe' into the name field", None),
    ("Type 'john@example.com' into the email input", None),
    ("Select 'United States' from the country dropdown", None),
    ("Click the submit button", None)
]

for step, args in steps:
    result = client.act(step)
    print(f"{step}: {'✅' if result['status'] == 'success' else '❌'}")
```

#### Example 3: Query Without Action

```python
# Find elements without performing actions
candidates = client.query(
    phrase="buttons with submit text",
    url="https://example.com"
)

for candidate in candidates[:3]:
    print(f"Found: {candidate['selector']}")
    print(f"Score: {candidate['score']:.2f}")
    print(f"Element: {candidate['element']['tag']} - {candidate['element']['text']}")
    print("---")
```

### Command Line Usage

#### Basic Commands

```bash
# Click action
her-act act --step "Click the search button" --url "https://google.com"

# Query elements
her-act query "input fields" --url "https://example.com"

# With custom timeout
her-act act --step "Wait for loading to complete" --url "https://app.com" --timeout 30000
```

#### Advanced CLI Usage

```bash
# Run in headless mode
her-act act --step "Click login" --url "https://example.com" --headless

# Export results to JSON
her-act query "all buttons" --url "https://example.com" > buttons.json

# Use in shell scripts
if her-act act --step "Click submit" --url "$URL"; then
    echo "Success"
else
    echo "Failed"
fi
```

### Integration Examples

#### Example 1: Pytest Integration

```python
# test_with_her.py
import pytest
from her.cli_api import HybridClient

@pytest.fixture
def her_client():
    client = HybridClient(headless=True)
    yield client
    client.close()

def test_login_flow(her_client):
    # Navigate to login page
    result = her_client.act(
        "Click the login link",
        url="https://example.com"
    )
    assert result["status"] == "success"
    
    # Fill credentials
    result = her_client.act("Type 'user@test.com' into email field")
    assert result["status"] == "success"
    
    result = her_client.act("Type 'password123' into password field")
    assert result["status"] == "success"
    
    # Submit
    result = her_client.act("Click the submit button")
    assert result["status"] == "success"
```

#### Example 2: Selenium Migration

```python
# Before (Selenium)
driver.find_element(By.XPATH, "//button[@class='btn-primary' and contains(text(), 'Submit')]").click()

# After (HER)
client.act("Click the submit button")
```

#### Example 3: CI/CD Pipeline

```yaml
# .github/workflows/test.yml
name: E2E Tests
on: [push]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      
      - name: Install HER
        run: |
          pip install -e .
          playwright install chromium
      
      - name: Run HER Tests
        run: |
          python -m her.cli act --step "Click login" --url "${{ secrets.APP_URL }}"
```

---

## 📖 API Reference

### HybridClient Class

```python
class HybridClient:
    def __init__(
        self,
        auto_index: bool = True,      # Auto-index pages
        headless: bool = True,         # Run browser in headless mode
        timeout_ms: int = 30000,       # Default timeout
        promotion_enabled: bool = True # Enable learning from successes
    )
```

#### Methods

##### `act(step: str, url: Optional[str] = None) -> Dict[str, Any]`

Execute an action from natural language.

**Parameters:**
- `step`: Natural language instruction (e.g., "Click the submit button")
- `url`: Optional URL to navigate to first

**Returns:**
```python
{
    "status": "success" | "failure",
    "method": "click" | "type" | "select" | ...,
    "confidence": 0.0-1.0,
    "dom_hash": "abc123...",
    "framePath": "main",
    "semantic_locator": "//button[...]",
    "used_locator": "//button[...]",
    "n_best": [
        {"locator": "...", "score": 0.9, "reasons": {...}}
    ],
    "overlay_events": ["Cookie banner dismissed"],
    "retries": {"attempts": 1, "final_method": "standard"},
    "explanation": "Click on 'submit button'",
    "duration_ms": 234
}
```

##### `query(phrase: str, url: Optional[str] = None) -> List[Dict[str, Any]]`

Find elements without performing actions.

**Parameters:**
- `phrase`: Search phrase (e.g., "input fields")
- `url`: Optional URL to navigate to first

**Returns:**
```python
[
    {
        "selector": "#email-input",
        "score": 0.95,
        "element": {
            "tag": "input",
            "text": "",
            "role": "textbox",
            "name": "email",
            "id": "email-input",
            "classes": ["form-control"]
        },
        "explanation": "High confidence match",
        "dom_hash": "xyz789..."
    }
]
```

### Supported Actions

| Action | Examples | Description |
|--------|----------|-------------|
| **click** | "Click the button", "Press submit" | Click an element |
| **type** | "Type 'text' into field" | Enter text |
| **select** | "Select 'Option' from dropdown" | Choose dropdown option |
| **hover** | "Hover over menu" | Mouse over element |
| **wait** | "Wait for spinner", "Wait 5 seconds" | Wait for condition |
| **clear** | "Clear the input" | Clear field content |
| **navigate** | "Go to homepage" | Navigate to URL |

---

## 🔧 Troubleshooting

### Common Issues and Solutions

#### Issue 1: Import Error

**Error:**
```
ModuleNotFoundError: No module named 'her'
```

**Solution:**
```bash
# Add src to Python path
export PYTHONPATH="${PYTHONPATH}:${PWD}/src"

# Or install in development mode
pip install -e .
```

#### Issue 2: Playwright Not Found

**Error:**
```
playwright._impl._api_types.Error: Executable doesn't exist
```

**Solution:**
```bash
# Install Playwright browsers
python -m playwright install chromium

# Or install all browsers
python -m playwright install
```

#### Issue 3: Element Not Found

**Error:**
```
No valid locator found
```

**Solutions:**
1. Check if page is fully loaded:
```python
client.act("Wait 3 seconds")  # Give page time to load
```

2. Use more specific descriptions:
```python
# Instead of: "Click button"
# Use: "Click the blue submit button at the bottom"
```

3. Check element visibility:
```python
# Query first to see available elements
candidates = client.query("buttons")
for c in candidates:
    print(c['element'])
```

#### Issue 4: Low Confidence Scores

**Solutions:**
1. Install ML models for better accuracy:
```bash
./scripts/install_models.sh
```

2. Use more descriptive phrases:
```python
# Poor: "Click it"
# Better: "Click the green 'Continue' button"
# Best: "Click the primary submit button in the login form"
```

### Performance Optimization

#### 1. Enable Caching
```python
# Embeddings are cached automatically
# Check cache stats
from her.embeddings.cache import EmbeddingCache
cache = EmbeddingCache()
print(cache.stats())
```

#### 2. Reuse Sessions
```python
# Keep client alive for multiple actions
client = HybridClient()
for step in steps:
    client.act(step)  # Reuses browser session
client.close()  # Close when done
```

#### 3. Parallel Execution
```python
from concurrent.futures import ThreadPoolExecutor

def run_test(url):
    client = HybridClient()
    result = client.act("Click login", url=url)
    client.close()
    return result

# Run tests in parallel
with ThreadPoolExecutor(max_workers=4) as executor:
    urls = ["https://site1.com", "https://site2.com"]
    results = executor.map(run_test, urls)
```

---

## 🏗️ Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────┐
│                    User Input (NL)                       │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                  Intent Parser                           │
│  • Extracts action, target, arguments                    │
│  • Confidence scoring                                    │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                Session Manager                           │
│  • Auto-indexing on first action                        │
│  • DOM change detection                                  │
│  • Cache management                                      │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              Element Detection                           │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐   │
│  │   Semantic   │ │  Heuristic   │ │  Promotion   │   │
│  │   Matching   │ │   Scoring    │ │   History    │   │
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘   │
│         └─────────────────┼─────────────────┘          │
│                           │                             │
│                    Fusion Ranking                       │
│                    (α·sem + β·heur + γ·prom)           │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              Locator Synthesis                           │
│  • Role-based (ARIA)                                    │
│  • CSS selectors                                        │
│  • XPath generation                                     │
│  • Uniqueness verification                              │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                Action Executor                           │
│  • Scroll into view                                     │
│  • Visibility check                                     │
│  • Overlay dismissal                                    │
│  • Retry with backoff                                   │
│  • Post-action verification                             │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              Recovery & Learning                         │
│  • Self-healing strategies                              │
│  • Promotion/demotion                                   │
│  • Persistent storage                                   │
└─────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Input Processing**: Natural language → Structured intent
2. **Page Analysis**: DOM + Accessibility tree → Element descriptors
3. **Candidate Generation**: Multiple strategies → Scored candidates
4. **Fusion**: Combine scores → Ranked list
5. **Execution**: Best candidate → Action → Verification
6. **Learning**: Success/failure → Update promotions

---

## 🚀 Advanced Features

### Custom Strategies

```python
from her.recovery.self_heal import SelfHealer, HealingStrategy

# Add custom healing strategy
healer = SelfHealer()
custom_strategy = HealingStrategy(
    name="custom_relaxation",
    description="Custom locator relaxation",
    transform_func=lambda loc: loc.replace("exact", "contains"),
    priority=1
)
healer.add_strategy(custom_strategy)
```

### Promotion System

```python
from her.recovery.promotion import PromotionStore

# Check what locators work best
store = PromotionStore()
best = store.get_best_locators(context="https://myapp.com")
for locator, score in best:
    print(f"{locator}: {score:.2f}")
```

### Debugging

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Get detailed execution info
result = client.act("Click submit", url="https://example.com")
print(json.dumps(result, indent=2))

# Check what elements were considered
for candidate in result["n_best"]:
    print(f"Candidate: {candidate['locator']}")
    print(f"Score: {candidate['score']}")
    print(f"Reasons: {candidate['reasons']}")
```

---

## 📚 Additional Resources

- **Architecture Details**: See `docs/ARCHITECTURE.md`
- **API Documentation**: See `docs/API.md`
- **Contributing Guide**: See `CONTRIBUTING.md`
- **Change Log**: See `CHANGELOG.md`

## 🤝 Getting Help

- **Issues**: [GitHub Issues](https://github.com/yourusername/her/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/her/discussions)
- **Email**: support@example.com

## 📄 License

MIT License - see LICENSE file for details.