# archived duplicate of src/her/__init__.py
"""HER - Hybrid Element Retriever

Production-ready web element location framework using semantic embeddings and robust heuristics.
"""

__version__ = "1.0.0"
__author__ = "HER Team"

from her.cli_api import HybridClient
from her.executor.session import Session
from her.bridge.snapshot import Snapshot

__all__ = [
    "HybridClient",
    "Session", 
    "Snapshot",
    "__version__",
]