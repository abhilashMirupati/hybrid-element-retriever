# 🎯 HER Quick Reference Guide

## 🚀 Installation in 30 Seconds

```bash
# Quick install (copy-paste all)
git clone <repo-url> && cd hybrid-element-retriever
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
pip install playwright numpy pydantic
python -m playwright install chromium
```

## 💡 Most Common Use Cases

### 1. Find Best XPath for Any Element

```python
from her.cli_api import HybridClient

client = HybridClient(headless=False)  # See browser for debugging

# Get best selector for any element
results = client.query("login button", url="https://example.com")

# Print the best XPath/CSS selector
best = results[0]
print(f"Best selector: {best['selector']}")
print(f"Confidence: {best['score']:.2%}")
```

### 2. One-Line Web Actions

```python
# Click
client.act("Click the submit button", url="https://example.com")

# Type
client.act("Type 'john@email.com' into the email field")

# Select
client.act("Select 'United States' from country dropdown")

# Wait
client.act("Wait until loading spinner disappears")
```

### 3. Command Line Usage

```bash
# Get XPath for element
python -m her.cli query "search box" --url "https://google.com"

# Perform action
python -m her.cli act --step "Click the I'm Feeling Lucky button" --url "https://google.com"
```

## 📊 Understanding Output

### Success Response
```json
{
  "status": "success",
  "used_locator": "//button[@type='submit']",  ← The XPath that worked
  "confidence": 0.92,                          ← How sure we are (92%)
  "n_best": [                                  ← Alternative selectors
    {"locator": "//button[@type='submit']", "score": 0.92},
    {"locator": "#submit-btn", "score": 0.85},
    {"locator": "button.primary", "score": 0.73}
  ]
}
```

## 🔍 Finding Elements - Cheat Sheet

| What You Want | What to Write | Example |
|--------------|---------------|---------|
| Button | "button with text X" | `"button with text Login"` |
| Input field | "X input/field" | `"email input field"` |
| Link | "X link" | `"home page link"` |
| Dropdown | "X dropdown/select" | `"country dropdown"` |
| Checkbox | "X checkbox" | `"remember me checkbox"` |
| Image | "X image" | `"profile image"` |
| Text | "text containing X" | `"text containing Welcome"` |

## 🛠️ Common Patterns

### Pattern 1: Login Flow
```python
client = HybridClient()
client.act("Click login link", url="https://app.com")
client.act("Type 'user@example.com' into email field")
client.act("Type 'password123' into password field")
client.act("Click the submit button")
```

### Pattern 2: Form Filling
```python
form_data = {
    "name field": "John Doe",
    "email input": "john@example.com",
    "phone number field": "555-1234",
    "message textarea": "This is my message"
}

for field, value in form_data.items():
    client.act(f"Type '{value}' into {field}")
client.act("Click submit")
```

### Pattern 3: Navigation
```python
# Navigate through a site
client.act("Click Products menu", url="https://shop.com")
client.act("Click Electronics category")
client.act("Click Laptops subcategory")
client.act("Click the first product")
```

## ⚡ Performance Tips

1. **Reuse Client**: Don't create new client for each action
```python
# ❌ Slow
for step in steps:
    client = HybridClient()
    client.act(step)
    
# ✅ Fast
client = HybridClient()
for step in steps:
    client.act(step)
```

2. **Be Specific**: More specific = faster + more accurate
```python
# ❌ Vague
"Click button"

# ✅ Specific
"Click the blue Submit button at the bottom of the form"
```

3. **Use Headless in Production**
```python
# Development (see browser)
client = HybridClient(headless=False)

# Production (faster)
client = HybridClient(headless=True)
```

## 🐛 Debugging

### See What HER Sees
```python
# List all buttons on page
buttons = client.query("all buttons", url="https://example.com")
for btn in buttons:
    print(f"- {btn['element']['text']}: {btn['selector']}")
```

### Enable Logging
```python
import logging
logging.basicConfig(level=logging.INFO)

# Now you'll see what HER is doing
client.act("Click submit")
# INFO: Parsed intent: Intent(action='click', target_phrase='submit')
# INFO: Found 3 candidates
# INFO: Using locator: //button[@type='submit']
```

### Take Screenshots on Failure
```python
result = client.act("Click non-existent button")
if result["status"] == "failure":
    # HER automatically retries and logs what went wrong
    print(f"Failed: {result['explanation']}")
    print(f"Tried locators: {result.get('retries')}")
```

## 🔧 Environment Variables

```bash
# Disable headless for debugging
export HER_HEADLESS=false

# Set custom timeout (ms)
export HER_TIMEOUT=60000

# Enable debug logging
export HER_DEBUG=true
```

## 📝 5-Minute Setup Script

Save as `setup_her.sh`:
```bash
#!/bin/bash
echo "🚀 Setting up HER..."

# Check Python
python --version || { echo "❌ Python not found"; exit 1; }

# Create venv
python -m venv her_env
source her_env/bin/activate

# Install dependencies
pip install playwright numpy pydantic

# Install browser
python -m playwright install chromium

# Test
python -c "from her.cli_api import HybridClient; print('✅ Setup complete!')"

echo "
Ready to use! Try:
  python -m her.cli query 'search button' --url 'https://google.com'
"
```

## 💬 Getting Help

```python
# See all available actions
from her.parser.intent import IntentParser
parser = IntentParser()
print("Supported actions:", [p[1] for p in parser.action_patterns])

# Check element detection strategies
from her.rank.heuristics import explain_heuristic_score
explanation = explain_heuristic_score(
    {"tag": "button", "text": "Submit"},
    "submit button",
    "click"
)
print(explanation)
```

## 🎓 Learn More

- Full Guide: See `SETUP_GUIDE.md`
- API Docs: See `docs/API.md`
- Examples: See `examples/` directory