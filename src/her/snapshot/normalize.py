# Re-export whatever normalizer you currently rely on
from ..descriptors import normalize_descriptor as normalize  # adjust to your codebase

__all__ = ["normalize"]
