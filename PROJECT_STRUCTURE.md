# 📁 Project Structure

## Clean, Standard Python Package Structure

```
hybrid-element-retriever/
│
├── 📚 Documentation
│   ├── README.md                 # Project overview
│   ├── SETUP_GUIDE.md           # Comprehensive setup guide
│   ├── QUICK_REFERENCE.md       # Quick start reference
│   ├── CHANGELOG.md             # Version history
│   ├── LICENSE                  # MIT license
│   └── docs/                    # Additional documentation
│       ├── ARCHITECTURE.md
│       └── DIAGRAMS.md
│
├── 🎯 Source Code
│   └── src/
│       └── her/                 # Main package
│           ├── __init__.py      # Package initialization
│           ├── cli.py           # CLI entry point
│           ├── cli_api.py       # Main API (HybridClient)
│           ├── config.py        # Configuration
│           ├── utils.py         # Utilities
│           ├── descriptors.py   # Data structures
│           ├── gateway_server.py # Java integration
│           │
│           ├── embeddings/      # Embedding module
│           │   ├── __init__.py
│           │   ├── _resolve.py  # ONNX resolver
│           │   ├── query_embedder.py
│           │   ├── element_embedder.py
│           │   └── cache.py     # LRU + SQLite cache
│           │
│           ├── bridge/          # Browser bridge
│           │   ├── __init__.py
│           │   ├── cdp_bridge.py # CDP integration
│           │   └── snapshot.py   # DOM/AX snapshot
│           │
│           ├── session/         # Session management
│           │   ├── __init__.py
│           │   └── manager.py   # Auto-indexing
│           │
│           ├── parser/          # NL parsing
│           │   ├── __init__.py
│           │   └── intent.py    # Intent extraction
│           │
│           ├── rank/            # Ranking system
│           │   ├── __init__.py
│           │   ├── heuristics.py # Heuristic scoring
│           │   └── fusion.py     # Fusion ranking
│           │
│           ├── locator/         # Locator generation
│           │   ├── __init__.py
│           │   ├── synthesize.py # Selector synthesis
│           │   └── verify.py     # Uniqueness check
│           │
│           ├── executor/        # Action execution
│           │   ├── __init__.py
│           │   └── actions.py   # Browser actions
│           │
│           ├── recovery/        # Self-healing
│           │   ├── __init__.py
│           │   ├── self_heal.py # Healing strategies
│           │   └── promotion.py # Promotion store
│           │
│           └── vectordb/        # Vector storage
│               ├── __init__.py
│               └── faiss_store.py
│
├── 🧪 Tests
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py          # Test configuration
│       ├── test_basic.py        # Basic tests
│       ├── test_embeddings.py   # Embedding tests
│       ├── test_bridge.py       # Bridge tests
│       ├── test_session.py      # Session tests
│       ├── test_parser.py       # Parser tests
│       ├── test_rank.py         # Ranking tests
│       ├── test_locator.py      # Locator tests
│       ├── test_executor.py     # Executor tests
│       ├── test_recovery.py     # Recovery tests
│       └── test_cli_api.py      # API tests
│
├── 📝 Examples
│   └── examples/
│       └── demo.py              # Interactive demo
│
├── 🔧 Scripts
│   └── scripts/
│       ├── install_models.sh    # Linux model installer
│       ├── install_models.ps1   # Windows model installer
│       └── verify_project.sh    # Project verification
│
├── ☕ Java Integration
│   └── java/
│       ├── pom.xml              # Maven config
│       └── src/main/java/com/example/her/
│           └── HybridClientJ.java
│
├── 🚀 CI/CD
│   └── .github/
│       └── workflows/
│           └── ci.yml           # GitHub Actions
│
├── ⚙️ Configuration Files
│   ├── setup.py                 # Package setup
│   ├── setup.cfg                # Setup configuration
│   ├── pyproject.toml          # Modern Python config
│   ├── requirements.txt         # Core dependencies
│   ├── requirements-dev.txt    # Dev dependencies
│   ├── pytest.ini              # Test configuration
│   └── .gitignore              # Git ignore rules
│
└── 📋 Project Management
    ├── REQ_CHECKLIST.md        # Requirements tracking
    ├── TODO_PLAN.md            # Implementation plan
    ├── RISKS.md                # Risk assessment
    └── PR_MERGE_CHECKLIST.md  # Merge checklist
```

## Package Size Summary

- **Source Code**: ~250 KB (31 Python files)
- **Tests**: ~100 KB (10 test files)
- **Documentation**: ~50 KB (5 main docs)
- **Total Package**: ~400 KB (very lightweight)

## Key Features of This Structure

### ✅ Standard Python Package
- Follows PEP standards
- `src/` layout prevents import conflicts
- Clean separation of concerns

### ✅ Comprehensive Testing
- Test files mirror source structure
- `conftest.py` for shared fixtures
- Easy to run: `pytest tests/`

### ✅ Documentation First
- User guides at root level
- Examples in dedicated folder
- Clear API documentation

### ✅ CI/CD Ready
- GitHub Actions configured
- Multiple Python version support
- Cross-platform (Linux/Windows)

### ✅ Clean & Minimal
- No unnecessary files
- Proper `.gitignore`
- No build artifacts in repo

## Quick Commands

```bash
# Install for development
pip install -e .

# Run tests
pytest tests/

# Run specific test
pytest tests/test_cli_api.py -v

# Format code
black src tests

# Lint code
flake8 src tests

# Build package
python -m build

# Run demo
python examples/demo.py
```

## What's NOT in the Repo

These are generated/downloaded and excluded via `.gitignore`:
- `__pycache__/` directories
- `.pytest_cache/`
- `*.pyc` files
- Virtual environments (`venv/`, `her_env/`)
- Build artifacts (`dist/`, `build/`, `*.egg-info/`)
- Coverage reports (`htmlcov/`, `.coverage`)
- IDE files (`.vscode/`, `.idea/`)
- ONNX model files (`*.onnx`, `*.pt`)
- Database files (`*.db`, `*.sqlite`)
- ZIP archives (`*.zip`)
- Log files (`*.log`)

## Import Examples

```python
# User imports (after installation)
from her import HybridClient
from her.cli_api import HybridClient

# Internal imports (within package)
from her.embeddings import QueryEmbedder
from her.rank.fusion import RankFusion
from her.recovery.self_heal import SelfHealer
```

This structure is:
- **Professional** - Follows Python packaging best practices
- **Clean** - No unnecessary files or folders
- **Scalable** - Easy to add new modules
- **Maintainable** - Clear organization
- **Standard** - Familiar to Python developers