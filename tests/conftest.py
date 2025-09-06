import os
import sys
from pathlib import Path

# Add src/ to import path for tests
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if SRC.exists():
    sys.path.insert(0, str(SRC))