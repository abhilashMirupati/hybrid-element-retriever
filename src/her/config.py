"""Configuration management for Hybrid Element Retriever."""

import os
from pathlib import Path

# Environment variables
HER_MODELS_DIR = os.environ.get("HER_MODELS_DIR")
HER_CACHE_DIR = os.environ.get("HER_CACHE_DIR")
HER_LOG_LEVEL = os.environ.get("HER_LOG_LEVEL", "INFO")

# Paths
PACKAGE_DIR = Path(__file__).parent
DEFAULT_MODELS_DIR = PACKAGE_DIR / "models"
HOME_MODELS_DIR = Path.home() / ".her" / "models"
DEFAULT_CACHE_DIR = Path.home() / ".cache" / "her"

# Model configurations
QUERY_MODEL_NAME = "e5-small"
QUERY_MODEL_HF_ID = "intfloat/e5-small"
ELEMENT_MODEL_NAME = "markuplm-base"
ELEMENT_MODEL_HF_ID = "microsoft/markuplm-base"

# Fusion weights (must sum to ~1.0 after normalization)
FUSION_ALPHA = 1.0  # Semantic similarity weight
FUSION_BETA = 0.5  # Heuristic score weight
FUSION_GAMMA = 0.2  # Promotion score weight

# Embedding dimensions
QUERY_EMBEDDING_DIM = 384
ELEMENT_EMBEDDING_DIM = 768
FALLBACK_EMBEDDING_DIM = 384

# Cache settings
MEMORY_CACHE_SIZE = 1000  # Number of embeddings to keep in memory
DISK_CACHE_SIZE_MB = 100  # Maximum disk cache size

# Timeouts (milliseconds)
DEFAULT_TIMEOUT_MS = 30000
DEFAULT_WAIT_MS = 100
DEFAULT_SETTLE_MS = 500

# Browser settings
DEFAULT_HEADLESS = True
DEFAULT_VIEWPORT = {"width": 1280, "height": 720}

# Session settings
AUTO_INDEX_THRESHOLD = 0.3  # DOM change threshold for auto re-indexing
MAX_INDEX_COUNT = 100  # Maximum indexes per session

# Locator settings
MAX_LOCATOR_LENGTH = 500  # Maximum characters in a locator string
LOCATOR_VERIFY_TIMEOUT_MS = 5000

# Recovery settings
MAX_HEAL_ATTEMPTS = 3
PROMOTION_THRESHOLD = 0.8  # Score threshold for promotion
DEMOTION_THRESHOLD = 0.3  # Score threshold for demotion


def get_models_dir() -> Path:
    """Get the models directory with proper fallback order.

    Order:
    1. HER_MODELS_DIR environment variable
    2. Package-bundled models directory
    3. User home directory ~/.her/models
    """
    if HER_MODELS_DIR:
        return Path(HER_MODELS_DIR)
    elif DEFAULT_MODELS_DIR.exists():
        return DEFAULT_MODELS_DIR
    else:
        HOME_MODELS_DIR.mkdir(parents=True, exist_ok=True)
        return HOME_MODELS_DIR


def get_cache_dir() -> Path:
    """Get the cache directory."""
    if HER_CACHE_DIR:
        cache_dir = Path(HER_CACHE_DIR)
    else:
        cache_dir = DEFAULT_CACHE_DIR

    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def get_embeddings_cache_dir() -> Path:
    """Get the embeddings cache directory."""
    cache_dir = get_cache_dir() / "embeddings"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def get_promotion_store_path() -> Path:
    """Get the promotion store database path."""
    return get_cache_dir() / "promotion.db"
