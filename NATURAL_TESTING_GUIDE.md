# 🎯 Natural Language Testing Guide

Write tests in plain English! No technical knowledge required.

## 🚀 Quick Start

### 1. Run a Simple Test

```bash
python run_natural_test.py \
  --test "Verizon Phone Shopping" \
  --url "https://www.verizon.com/" \
  --steps "Click on Phones" "Click on Apple" "Click on iPhone"
```

### 2. Run Tests from File

```bash
# Run all natural language tests
python -m pytest tests/natural_language_test.py -v

# Run specific test
python -m pytest tests/natural_language_test.py::test_verizon_phone_shopping -v
```

## 📝 Writing Your Own Tests

### Method 1: Command Line

```bash
python run_natural_test.py \
  --test "Your Test Name" \
  --url "https://your-website.com/" \
  --steps \
    "Click on login button" \
    "Type your username" \
    "Type your password" \
    "Click on submit button" \
    "Verify dashboard loaded"
```

### Method 2: Python File

Create a file `my_test.py`:

```python
from src.her.testing.natural_test_runner import run_natural_test

def test_my_business_flow():
    steps = [
        "Go to my website",
        "Click on products",
        "Click on electronics",
        "Click on first product",
        "Click on add to cart",
        "Verify cart updated"
    ]
    
    result = run_natural_test(
        test_name="My Business Flow",
        steps=steps,
        start_url="https://my-website.com/",
        headless=True
    )
    
    assert result['success'], f"Test failed: {result['message']}"
```

## 🎯 Supported Actions

The framework understands these natural language actions:

### Navigation
- "Go to [website]"
- "Navigate to [URL]"
- "Visit [page]"

### Clicking
- "Click on [element]"
- "Tap [element]"
- "Press [button]"
- "Select [option]"
- "Choose [item]"

### Typing
- "Type [text]"
- "Enter [text]"
- "Input [text]"
- "Fill [field] with [text]"

### Waiting
- "Wait [X] seconds"
- "Pause for [X] minutes"
- "Sleep [X] seconds"

### Verification
- "Verify [condition]"
- "Check [condition]"
- "Confirm [condition]"
- "Ensure [condition]"

### Scrolling
- "Scroll down"
- "Scroll up"
- "Scroll to [element]"

## 🔧 Advanced Features

### Automatic Page Transitions
The framework automatically detects when you navigate to a new page and takes a fresh snapshot. No need to worry about page changes!

### Smart Element Finding
The framework uses AI to understand what you mean:
- "Click on login button" → finds any login button
- "Type in search box" → finds any search input
- "Click on first product" → finds the first product on the page

### Error Handling
If something goes wrong, the framework tells you exactly what happened and suggests fixes.

## 📊 Test Results

After running a test, you get detailed results:

```
📊 TEST RESULTS: Verizon Phone Shopping
============================================================
✅ Success: True
📝 Message: All steps completed successfully
📈 Steps: 5/5 successful
🌐 Final URL: https://www.verizon.com/phones/iphone

📋 Step Details:
   ✅ Step 1: navigate -> https://www.verizon.com/
   ✅ Step 2: click -> Phones
   ✅ Step 3: click -> Apple
   ✅ Step 4: click -> iPhone
   ✅ Step 5: verify -> iPhone product page
```

## 🎨 Examples

### E-commerce Shopping
```python
steps = [
    "Go to Amazon",
    "Click on search box",
    "Type wireless headphones",
    "Press Enter",
    "Click on first product",
    "Click on add to cart",
    "Verify item added to cart"
]
```

### Login Flow
```python
steps = [
    "Go to my website",
    "Click on login",
    "Type my email",
    "Type my password",
    "Click on sign in",
    "Verify dashboard loaded"
]
```

### Form Filling
```python
steps = [
    "Go to contact page",
    "Type my name",
    "Type my email",
    "Type my message",
    "Click on send button",
    "Verify thank you message"
]
```

## 🚨 Troubleshooting

### Test Fails to Find Element
- Try being more specific: "Click on login button" instead of "Click on button"
- Use common terms: "search box", "menu", "submit button"

### Page Not Loading
- Check your internet connection
- Try a different URL
- Add a wait step: "Wait 5 seconds"

### Test Runs Too Fast
- Add wait steps between actions
- Use "Wait 2 seconds" between clicks

## 🎉 That's It!

You now know how to write tests in plain English. The framework handles all the technical details automatically!

For more examples, check out `tests/natural_language_test.py`.