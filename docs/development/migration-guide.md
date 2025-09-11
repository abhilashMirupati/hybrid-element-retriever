# HER Project Migration Guide

## Overview
This guide helps users migrate from the old project structure to the new organized structure after the reorganization.

## What Changed

### File Locations
- **Environment files**: Moved from root to `config/`
- **Scripts**: Organized by purpose in `scripts/` subdirectories
- **Documentation**: Consolidated in `docs/` directory
- **Tools**: Moved to `tools/` directory
- **Tests**: Reorganized by type in `tests/` subdirectories

### Import Paths
- **Core modules**: Now in `her.core.*` instead of `her.*`
- **CLI modules**: Now in `her.cli.*` instead of `her.*`
- **Executor**: Now in `her.executor.*` instead of `her.*`

## Migration Steps

### 1. Update Environment Configuration

#### Old Way:
```bash
# .env file in root directory
export HER_MODELS_DIR="$(pwd)/src/her/models"
export HER_CACHE_DIR="$(pwd)/.her_cache"
```

#### New Way:
```bash
# Copy environment file to new location
cp config/.env.example config/.env

# Or use the new tools
python tools/load_env.py
```

### 2. Update Import Statements

#### Old Imports:
```python
from her.config import get_config
from her.strict import STRICT
from her.pipeline import HybridPipeline
from her.runner import Runner
from her.executor_main import Executor
from her.promotion_adapter import compute_label_key
```

#### New Imports:
```python
from her.core.config import get_config
from her.core.strict import STRICT
from her.core.pipeline import HybridPipeline
from her.core.runner import Runner
from her.executor.main import Executor
from her.promotion.promotion_adapter import compute_label_key
```

### 3. Update Script Paths

#### Old Script Locations:
```bash
python scripts/testing/preflight.py
python scripts/testing/smoke_run.py
python tools/load_env.py
python tools/test_env.py
```

#### New Script Locations:
```bash
python scripts/testing/preflight.py
python scripts/testing/smoke_run.py
python tools/load_env.py
python tools/test_env.py
```

### 4. Update Documentation References

#### Old Documentation:
- Multiple setup guides in root
- Scattered documentation files

#### New Documentation:
- Consolidated in `docs/` directory
- Clear hierarchy and organization

## Backward Compatibility

### What Still Works
- **Environment variables**: All existing env vars work
- **API**: Public API remains unchanged
- **Configuration**: Existing configuration methods work
- **Functionality**: All features work as before

### What Changed
- **File locations**: Files moved to new directories
- **Import paths**: Some imports need updating
- **Script locations**: Scripts moved to organized structure

## Troubleshooting

### Import Errors
If you get import errors after the reorganization:

1. **Check import paths**: Update to new module structure
2. **Verify dependencies**: Run `python tools/check_dependencies.py`
3. **Check environment**: Ensure `.env` file is in `config/` directory

### Script Errors
If scripts don't work in new locations:

1. **Update paths**: Scripts now have updated path calculations
2. **Check working directory**: Run from project root
3. **Verify imports**: Scripts should import correctly

### Configuration Issues
If configuration doesn't work:

1. **Check file location**: Ensure `.env` is in `config/` directory
2. **Verify environment loading**: Run `python tools/test_env.py`
3. **Check permissions**: Ensure files are readable

## Benefits of New Structure

### 1. **Better Organization**
- Files grouped by purpose
- Clear separation of concerns
- Professional appearance

### 2. **Easier Maintenance**
- Logical structure for updates
- Clear module hierarchy
- Better code organization

### 3. **Improved Development**
- Easy to find files
- Clear import paths
- Better development experience

### 4. **Scalability**
- Structure supports growth
- Easy to add new features
- Maintainable long-term

## Support

If you encounter issues during migration:

1. **Check this guide**: Most issues are covered here
2. **Run dependency check**: `python tools/check_dependencies.py`
3. **Test environment**: `python tools/test_env.py`
4. **Verify imports**: Check import statements

## Conclusion

The reorganization improves the project structure while maintaining full backward compatibility. The new organization makes the project more maintainable and professional while preserving all existing functionality.