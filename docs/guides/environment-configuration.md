# HER Framework Environment Configuration

This document explains how to configure the HER framework using environment variables.

## Quick Start

1. **Copy the example configuration:**
   ```bash
   cp .env.example .env
   ```

2. **Edit the configuration:**
   ```bash
   nano .env  # or your preferred editor
   ```

3. **Use the framework:**
   ```python
   import her  # Environment variables are loaded automatically
   ```

## Environment Variable Categories

### Core Directory Configuration

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `HER_MODELS_DIR` | Path to ML models directory | `./src/her/models` | `/path/to/models` |
| `HER_CACHE_DIR` | Path to cache directory | `./.her_cache` | `/path/to/cache` |

### Framework Behavior

| Variable | Description | Default | Values |
|----------|-------------|---------|--------|
| `HER_STRICT` | Enable strict mode (fail-fast) | `1` | `1` (enabled) \| `0` (disabled) |
| `HER_PERF_OPT` | Enable performance optimization | `1` | `1` (enabled) \| `0` (disabled) |
| `HER_FORCE_AX` | Force accessibility extraction | `1` | `1` (enabled) \| `0` (disabled) |
| `HER_ALL_ELEMENTS` | Select all elements for MiniLM | `1` | `1` (enabled) \| `0` (disabled) |
| `HER_DISABLE_HEURISTICS` | Disable heuristics (MarkupLM-only) | `false` | `true` \| `false` |

### Canonical Descriptor Configuration

| Variable | Description | Default | Values |
|----------|-------------|---------|--------|
| `HER_CANONICAL_MODE` | Canonical descriptor building mode | `both` | `both` \| `dom_only` \| `accessibility_only` |
| `HER_DEBUG_CANONICAL` | Debug canonical building | `0` | `1` (enabled) \| `0` (disabled) |

### Hierarchy Configuration

| Variable | Description | Default | Values |
|----------|-------------|---------|--------|
| `HER_USE_HIERARCHY` | Enable hierarchical context | `false` | `true` \| `false` |
| `HER_USE_TWO_STAGE` | Enable two-stage MarkupLM | `false` | `true` \| `false` |
| `HER_DEBUG_HIERARCHY` | Enable hierarchy debugging | `false` | `true` \| `false` |

### Debugging and Testing

| Variable | Description | Default | Values |
|----------|-------------|---------|--------|
| `HER_DEBUG_CANDIDATES` | Debug candidate elements | `0` | `1` (enabled) \| `0` (disabled) |
| `HER_E2E` | Enable end-to-end testing | `0` | `1` (enabled) \| `0` (disabled) |
| `HER_DRY_RUN` | Enable dry run mode | `0` | `1` (enabled) \| `0` (disabled) |

## Usage Methods

### Method 1: Automatic Loading (Recommended)

Environment variables are automatically loaded when you import the HER framework:

```python
import her  # .env file is loaded automatically
from her.core.pipeline import HERPipeline
```

### Method 2: Manual Loading

You can manually load environment variables:

```python
# Load from .env file
import load_env
import her

# Or load from custom file
import load_env
load_env.load_env_file("custom.env")
import her
```

### Method 3: Shell Integration

Load environment variables in your shell:

```bash
# Source environment variables
eval "$(python load_env.py --export)"

# Or load from custom file
eval "$(python load_env.py custom.env --export)"
```

### Method 4: Traditional Export

Set environment variables manually:

```bash
export HER_MODELS_DIR="/path/to/models"
export HER_CACHE_DIR="/path/to/cache"
export HER_STRICT=1
```

## Configuration Examples

### Development Configuration

```bash
# .env for development
HER_MODELS_DIR=./src/her/models
HER_CACHE_DIR=./.her_cache
HER_STRICT=0
HER_DEBUG_CANONICAL=1
HER_DEBUG_CANDIDATES=1
HER_DEBUG_HIERARCHY=1
```

### Production Configuration

```bash
# .env for production
HER_MODELS_DIR=/opt/her/models
HER_CACHE_DIR=/var/cache/her
HER_STRICT=1
HER_PERF_OPT=1
HER_FORCE_AX=1
HER_ALL_ELEMENTS=1
```

### Testing Configuration

```bash
# .env for testing
HER_MODELS_DIR=./src/her/models
HER_CACHE_DIR=./test_cache
HER_E2E=1
HER_DRY_RUN=1
HER_STRICT=0
```

## Troubleshooting

### Environment Variables Not Loading

1. **Check file location:** Ensure `.env` file is in the project root
2. **Check file format:** Ensure no spaces around `=` signs
3. **Check permissions:** Ensure file is readable
4. **Manual loading:** Try `python load_env.py` to test

### Configuration Not Applied

1. **Import order:** Ensure `import her` happens before using HER modules
2. **Variable names:** Check for typos in variable names
3. **Value format:** Ensure values match expected format (see table above)

### Testing Configuration

Run the test script to verify your configuration:

```bash
python test_env.py
```

This will show all loaded environment variables and test the HER configuration.