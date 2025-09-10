# HER Project Reorganization Plan

## Current Issues Identified

### 1. Root Directory Clutter
- Mixed file types in root directory
- 6 different documentation files with overlapping content
- Scattered setup and configuration files

### 2. Documentation Disorganization
- Multiple README files with unclear purposes
- No clear documentation hierarchy
- Duplicate setup instructions

### 3. Script Organization Issues
- All scripts mixed in `/scripts` regardless of purpose
- Inconsistent naming conventions
- Missing categorization

### 4. Test Organization
- Mixed test structure
- Inconsistent naming patterns

## Proposed New Structure

```
/workspace/
├── README.md                          # Main project README
├── LICENSE
├── pyproject.toml
├── pytest.ini
├── requirements.txt
├── requirements-dev.txt
├── .env.example
├── .env
│
├── /docs/                             # All documentation
│   ├── README.md                      # Main documentation index
│   ├── SETUP.md                       # Consolidated setup guide
│   ├── API.md                         # API documentation
│   ├── CONTRIBUTING.md                # Contribution guidelines
│   ├── /guides/                       # Detailed guides
│   │   ├── environment-configuration.md
│   │   ├── hierarchy-enhancement.md
│   │   └── cross-platform-setup.md
│   └── /api/                          # API reference
│
├── /scripts/                          # Organized by purpose
│   ├── /setup/                        # Setup scripts
│   │   ├── install_models.sh
│   │   ├── install_models.ps1
│   │   ├── init_dbs.sh
│   │   └── init_dbs.ps1
│   ├── /maintenance/                  # Maintenance scripts
│   │   └── cleanup_repo.ps1
│   ├── /testing/                      # Test-related scripts
│   │   ├── preflight.py
│   │   └── smoke_run.py
│   └── /utilities/                    # Utility scripts
│       └── dom_extractor.js
│
├── /tests/                            # Organized test structure
│   ├── conftest.py
│   ├── /unit/                         # Unit tests
│   │   └── /core/
│   │       ├── test_cache.py
│   │       ├── test_delta_embedding.py
│   │       ├── test_embedder_dims.py
│   │       └── test_selector_synthesis.py
│   ├── /integration/                  # Integration tests
│   └── /e2e/                          # End-to-end tests
│       └── test_verizon_comprehensive.py
│
├── /src/                              # Source code
│   └── /her/                          # Main HER package
│       ├── __init__.py
│       ├── env_loader.py
│       ├── /core/                     # Core functionality
│       │   ├── config.py
│       │   ├── strict.py
│       │   ├── pipeline.py
│       │   ├── runner.py
│       │   ├── hashing.py
│       │   ├── compat.py
│       │   └── frames.py
│       ├── /cli/                      # CLI interface
│       │   ├── __init__.py
│       │   ├── main.py
│       │   ├── cli.py
│       │   └── cli_api.py
│       ├── /api/                      # API interface
│       │   └── (future API modules)
│       ├── /executor/                 # Execution engine
│       │   ├── __init__.py
│       │   ├── actions.py
│       │   ├── session.py
│       │   └── main.py               # (moved from executor_main.py)
│       ├── /embeddings/               # Embedding functionality
│       ├── /locator/                  # Element location
│       ├── /parser/                   # Intent parsing
│       ├── /descriptors/              # Descriptor handling
│       ├── /vectordb/                 # Vector database
│       ├── /cache/                    # Caching system
│       ├── /bridge/                   # Browser bridge
│       ├── /browser/                  # Browser interface
│       ├── /snapshot/                 # Snapshot handling
│       ├── /rank/                     # Ranking system
│       ├── /intent/                   # Intent handling
│       └── /promotion/                # Promotion system
│           └── promotion_adapter.py
│
├── /tools/                            # Development tools
│   ├── load_env.py
│   ├── test_env.py
│   └── setup.py
│
└── /config/                           # Configuration files
    ├── setup.cfg
    ├── .env.example
    └── .env
```

## File Movement Plan

### Phase 1: Documentation Consolidation
1. **Merge documentation files:**
   - `README_SETUP.md` + `SETUP_GUIDE.md` + `CROSS_PLATFORM_SETUP_SUMMARY.md` → `/docs/SETUP.md`
   - `HIERARCHY_ENHANCEMENT_PLAN.md` → `/docs/guides/hierarchy-enhancement.md`
   - `ENV_CONFIGURATION.md` → `/docs/guides/environment-configuration.md`

2. **Create documentation structure:**
   - Create `/docs/` directory
   - Move consolidated files
   - Update main `README.md` to reference new structure

### Phase 2: Script Organization
1. **Categorize scripts by purpose:**
   - Setup scripts → `/scripts/setup/`
   - Maintenance scripts → `/scripts/maintenance/`
   - Testing scripts → `/scripts/testing/`
   - Utility scripts → `/scripts/utilities/`

2. **Rename for consistency:**
   - Ensure consistent naming patterns
   - Add proper file extensions

### Phase 3: Test Reorganization
1. **Organize test structure:**
   - Unit tests → `/tests/unit/`
   - Integration tests → `/tests/integration/`
   - E2E tests → `/tests/e2e/`

2. **Rename test files:**
   - Ensure consistent naming patterns
   - Group related tests

### Phase 4: Source Code Cleanup
1. **Reorganize source structure:**
   - Move `executor_main.py` → `/src/her/executor/main.py`
   - Consolidate CLI files in `/src/her/cli/`
   - Create `/src/her/core/` for core functionality

2. **Update imports:**
   - Update all import statements
   - Ensure relative imports work correctly

### Phase 5: Configuration Cleanup
1. **Organize configuration:**
   - Move `.env` files to `/config/`
   - Keep `pyproject.toml` in root
   - Move `setup.cfg` to `/config/`

2. **Update references:**
   - Update all file references
   - Update documentation

## Benefits of Reorganization

1. **Clear Structure:** Easy to find files by purpose
2. **Better Documentation:** Consolidated and organized docs
3. **Improved Maintainability:** Logical grouping of related files
4. **Professional Appearance:** Clean, organized project structure
5. **Easier Onboarding:** New developers can navigate easily
6. **Scalability:** Structure supports future growth

## Implementation Notes

- All file movements will preserve git history
- Import statements will be updated automatically
- Documentation will be updated to reflect new structure
- No breaking changes to functionality
- Backward compatibility maintained where possible