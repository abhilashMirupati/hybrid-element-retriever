# Contributing to HER (Hybrid Element Retriever)

Thank you for your interest in contributing to HER! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Style Guidelines](#style-guidelines)
- [Documentation](#documentation)

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct:
- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on constructive criticism
- Accept feedback gracefully

## Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/yourusername/her.git
   cd her
   ```
3. Add the upstream repository:
   ```bash
   git remote add upstream https://github.com/original/her.git
   ```

## Development Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -e .[dev,ml]
   python -m playwright install chromium
   ```

3. Install pre-commit hooks:
   ```bash
   pip install pre-commit
   pre-commit install
   ```

## Making Changes

### Branch Naming

- Feature branches: `feature/description`
- Bug fixes: `fix/description`
- Documentation: `docs/description`
- Performance: `perf/description`

### Development Workflow

1. Create a new branch:
   ```bash
   git checkout -b feature/your-feature
   ```

2. Make your changes following our style guidelines

3. Add tests for new functionality

4. Run tests locally:
   ```bash
   pytest tests/ -v
   ```

5. Check code quality:
   ```bash
   black src tests
   flake8 src tests
   mypy src
   ```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/test_specific.py

# Run with verbose output
pytest -v
```

### Writing Tests

- Place tests in the `tests/` directory
- Name test files with `test_` prefix
- Use descriptive test names
- Include docstrings explaining what each test does
- Test both success and failure cases

Example test:
```python
def test_intent_parser_click_action():
    """Test that IntentParser correctly parses click actions."""
    parser = IntentParser()
    intent = parser.parse("Click the submit button")
    assert intent.action == "click"
    assert intent.target_phrase == "the submit button"
```

## Submitting Changes

### Pull Request Process

1. Update your branch with latest upstream changes:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. Push your branch:
   ```bash
   git push origin feature/your-feature
   ```

3. Create a Pull Request on GitHub

4. Ensure all CI checks pass

5. Request review from maintainers

### Pull Request Checklist

- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation updated if needed
- [ ] Commit messages are clear
- [ ] PR description explains the changes
- [ ] No merge conflicts

## Style Guidelines

### Python Style

We follow PEP 8 with these additions:
- Line length: 88 characters (Black default)
- Use type hints where appropriate
- Add docstrings to all public functions/classes

### Code Formatting

We use Black for automatic formatting:
```bash
black src tests
```

### Linting

We use Flake8 for linting:
```bash
flake8 src tests
```

Configuration in `.flake8`:
```ini
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = .git,__pycache__,build,dist
```

### Type Checking

We use mypy for type checking:
```bash
mypy src
```

## Documentation

### Docstring Format

We use Google-style docstrings:

```python
def function_name(param1: str, param2: int) -> bool:
    """Brief description of function.
    
    Longer description if needed.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When invalid input provided
    """
```

### Updating Documentation

- Update README.md for user-facing changes
- Update docstrings for API changes
- Add examples for new features
- Update CHANGELOG.md

## Project Structure

```
her/
├── src/her/          # Source code
│   ├── parser/       # Natural language parsing
│   ├── executor/     # Action execution
│   ├── locator/      # Locator generation
│   ├── rank/         # Element ranking
│   ├── recovery/     # Self-healing
│   └── handlers/     # Complex scenarios
├── tests/            # Test files
├── examples/         # Usage examples
├── docs/             # Documentation
└── scripts/          # Utility scripts
```

## Common Tasks

### Adding a New Action Type

1. Update `IntentParser` in `src/her/parser/intent.py`
2. Add action handler in `src/her/executor/actions.py`
3. Update `HybridClient.act()` in `src/her/cli_api.py`
4. Add tests in `tests/test_parser.py`
5. Update documentation

### Adding a New Locator Strategy

1. Add strategy method to `LocatorSynthesizer` in `src/her/locator/synthesize.py`
2. Add verification in `src/her/locator/verify.py`
3. Add tests in `tests/test_locator.py`
4. Update documentation

### Improving Self-Healing

1. Add strategy class in `src/her/recovery/enhanced_self_heal.py`
2. Register strategy in `EnhancedSelfHeal._init_strategies()`
3. Add tests in `tests/test_recovery.py`
4. Document the strategy

## Getting Help

- Check existing issues on GitHub
- Read the documentation
- Ask questions in discussions
- Contact maintainers

## Recognition

Contributors will be recognized in:
- CHANGELOG.md for their contributions
- README.md contributors section
- GitHub contributors page

Thank you for contributing to HER!