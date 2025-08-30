#!/usr/bin/env python3
"""Test that all HER modules can be imported."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

print("Testing HER imports...\n")

# Test core imports
try:
    import her
    print(f"1. Package import: ✅ PASS (version {her.__version__})")
except ImportError as e:
    print(f"1. Package import: ❌ FAIL - {e}")
    sys.exit(1)

# Test component imports
modules = [
    ("her.bridge.snapshot", "Snapshot"),
    ("her.executor.session", "Session"),
    ("her.embeddings._resolve", "ModelResolver"),
    ("her.embeddings.query_embedder", "QueryEmbedder"),
    ("her.embeddings.element_embedder", "ElementEmbedder"),
    ("her.vectordb.sqlite_cache", "VectorCache"),
    ("her.rank.fusion", "FusionRanker"),
    ("her.locator.synthesize", "LocatorSynthesizer"),
    ("her.locator.verify", "LocatorVerifier"),
    ("her.executor.actions", "ActionExecutor"),
    ("her.recovery.self_heal", "SelfHealer"),
    ("her.recovery.promotion", "PromotionManager"),
]

failed = []
for module_name, class_name in modules:
    try:
        module = __import__(module_name, fromlist=[class_name])
        if hasattr(module, class_name):
            print(f"2. {module_name}: ✅ PASS")
        else:
            print(f"2. {module_name}: ⚠️ WARNING - {class_name} not found")
            failed.append(module_name)
    except ImportError as e:
        # Check if it's just missing external dependencies
        if "playwright" in str(e) or "numpy" in str(e) or "scipy" in str(e):
            print(f"2. {module_name}: ⚠️ SKIP - Missing external dependency: {str(e).split('named')[1] if 'named' in str(e) else 'dependency'}")
        else:
            print(f"2. {module_name}: ❌ FAIL - {e}")
            failed.append(module_name)

# Test CLI imports
try:
    from her import cli_api
    print(f"3. CLI API import: ⚠️ SKIP - Missing external dependencies")
except ImportError as e:
    if "playwright" in str(e) or "numpy" in str(e):
        print(f"3. CLI API import: ⚠️ SKIP - Missing external dependencies")
    else:
        print(f"3. CLI API import: ❌ FAIL - {e}")
        failed.append("cli_api")

print("\n" + "="*50)
if failed:
    print(f"❌ {len(failed)} modules failed to import")
    print("Failed modules:", ", ".join(failed))
    sys.exit(1)
else:
    print("✅ All core modules can be imported!")
    print("Note: Some modules skipped due to missing external dependencies")
    print("Run 'pip install -e .[dev]' to install all dependencies")
    sys.exit(0)