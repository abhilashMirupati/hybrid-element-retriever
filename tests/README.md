# HER Framework Tests

This directory contains all test files for the HER (Human-Emulated Reasoning) framework.

## Directory Structure

```
tests/
├── README.md                    # This file
├── natural_test_runner.py       # Natural language test runner (main CLI)
├── natural_language_test.py     # Example test steps
├── conftest.py                  # Pytest configuration
├── e2e/                         # End-to-end tests
│   └── test_verizon_comprehensive.py
├── integration/                 # Integration tests
│   └── test_integration.py
└── unit/                        # Unit tests
    └── core/
        ├── test_cache.py
        ├── test_delta_embedding.py
        ├── test_embedder_dims.py
        └── test_selector_synthesis.py
```

## Running Tests

### Natural Language Tests

From the project root:

```bash
# Using the launcher script
python run_test.py --help

# Or directly
python tests/natural_test_runner.py --help
```

### Command Line Usage

```bash
# Run with command line arguments
python run_test.py --test "Google Search" --url "https://www.google.com/" --steps "Go to Google" "Click search box" "Type Python"

# Run with inline configuration
python run_test.py --use-inline
```

### Inline Configuration

Edit `tests/natural_test_runner.py` and uncomment/modify the `TEST_CONFIG`:

```python
TEST_CONFIG = {
    "test_name": "My Test",
    "start_url": "https://example.com/",
    "steps": [
        "Click on button",
        "Type some text",
        "Press Enter"
    ],
    "headless": True
}
```

### Environment Configuration

Create a `.env` file in the project root:

```env
HER_MODELS_DIR=./src/her/models
HER_CACHE_DIR=./.her_cache
HER_HEADLESS=true
HER_TIMEOUT=15000
```

## Test Types

1. **Natural Language Tests**: Human-readable test steps using AI
2. **E2E Tests**: Full browser automation tests
3. **Integration Tests**: Component interaction tests
4. **Unit Tests**: Individual component tests

## Debugging

Use VS Code debug configuration:

```json
{
    "name": "Debug Natural Language Test",
    "type": "python",
    "request": "launch",
    "program": "tests/natural_test_runner.py",
    "args": ["--use-inline"],
    "env": {
        "HER_MODELS_DIR": "${workspaceFolder}/src/her/models",
        "HER_CACHE_DIR": "${workspaceFolder}/.her_cache"
    },
    "console": "integratedTerminal",
    "cwd": "${workspaceFolder}"
}
```