"""
Centralized configuration management for HER framework.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class CanonicalMode(Enum):
    """Canonical descriptor building modes."""
    DOM_ONLY = "dom_only"           # Only DOM attributes
    ACCESSIBILITY_ONLY = "accessibility_only"  # Only accessibility tree attributes  
    BOTH = "both"                   # Both DOM + accessibility tree (default)


@dataclass
class HERConfig:
    """Centralized configuration for HER framework."""
    
    # Core paths
    models_dir: Path = field(default_factory=lambda: Path(os.getenv("HER_MODELS_DIR", "src/her/models")))
    cache_dir: Path = field(default_factory=lambda: Path(os.getenv("HER_CACHE_DIR", ".her_cache")))
    
    # Debug settings
    debug_candidates: bool = field(default_factory=lambda: os.getenv("HER_DEBUG_CANDIDATES", "0") == "1")
    debug_canonical: bool = field(default_factory=lambda: os.getenv("HER_DEBUG_CANONICAL", "0") == "1")
    debug_hierarchy: bool = field(default_factory=lambda: os.getenv("HER_DEBUG_HIERARCHY", "0") == "1")
    debug: bool = field(default_factory=lambda: os.getenv("HER_DEBUG", "0") == "1")
    log_level: str = field(default_factory=lambda: os.getenv("HER_LOG_LEVEL", "INFO"))
    
    # Feature flags
    use_hierarchy: bool = field(default_factory=lambda: os.getenv("HER_USE_HIERARCHY", "false").lower() == "true")
    use_two_stage: bool = field(default_factory=lambda: os.getenv("HER_USE_TWO_STAGE", "false").lower() == "true")
    disable_heuristics: bool = field(default_factory=lambda: os.getenv("HER_DISABLE_HEURISTICS", "false").lower() == "true")
    use_semantic_search: bool = field(default_factory=lambda: os.getenv("HER_USE_SEMANTIC_SEARCH", "true").lower() == "true")
    
    # Performance settings
    max_text_length: int = field(default_factory=lambda: int(os.getenv("HER_MAX_TEXT_LENGTH", "1024")))
    max_elements: int = field(default_factory=lambda: int(os.getenv("HER_MAX_ELEMENTS", "1000")))
    cache_size_mb: int = field(default_factory=lambda: int(os.getenv("HER_CACHE_SIZE_MB", "100")))
    
    # Browser settings
    headless: bool = field(default_factory=lambda: os.getenv("HER_HEADLESS", "true").lower() == "true")
    browser_timeout: int = field(default_factory=lambda: int(os.getenv("HER_BROWSER_TIMEOUT", "30000")))
    
    # E2E testing
    e2e_enabled: bool = field(default_factory=lambda: os.getenv("HER_E2E", "0") == "1")
    
    # Canonical mode
    canonical_mode: CanonicalMode = field(default_factory=lambda: CanonicalMode.BOTH)
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate_paths()
        self._create_directories()
    
    def _validate_paths(self):
        """Validate that required paths are accessible."""
        # Only validate if models directory is explicitly set and exists
        if self.models_dir != Path("src/her/models") and not self.models_dir.exists():
            raise ValueError(f"Models directory does not exist: {self.models_dir}")
        
        # Cache directory will be created if it doesn't exist
        if not self.cache_dir.parent.exists():
            raise ValueError(f"Cache directory parent does not exist: {self.cache_dir.parent}")
    
    def _create_directories(self):
        """Create necessary directories."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'models_dir': str(self.models_dir),
            'cache_dir': str(self.cache_dir),
            'debug_candidates': self.debug_candidates,
            'debug_canonical': self.debug_canonical,
            'debug_hierarchy': self.debug_hierarchy,
            'debug': self.debug,
            'log_level': self.log_level,
            'use_hierarchy': self.use_hierarchy,
            'use_two_stage': self.use_two_stage,
            'disable_heuristics': self.disable_heuristics,
            'use_semantic_search': self.use_semantic_search,
            'max_text_length': self.max_text_length,
            'max_elements': self.max_elements,
            'cache_size_mb': self.cache_size_mb,
            'headless': self.headless,
            'browser_timeout': self.browser_timeout,
            'e2e_enabled': self.e2e_enabled,
            'canonical_mode': self.canonical_mode,
        }
    
    def get_canonical_mode(self) -> CanonicalMode:
        """Get canonical mode."""
        return self.canonical_mode
    
    def should_use_dom(self) -> bool:
        """Check if DOM should be used."""
        return self.canonical_mode in [CanonicalMode.DOM_ONLY, CanonicalMode.BOTH]
    
    def should_use_accessibility(self) -> bool:
        """Check if accessibility tree should be used."""
        return self.canonical_mode in [CanonicalMode.ACCESSIBILITY_ONLY, CanonicalMode.BOTH]
    
    def should_disable_heuristics(self) -> bool:
        """Check if heuristics should be disabled (MarkupLM-only mode)."""
        return self.disable_heuristics
    
    def is_performance_optimized(self) -> bool:
        """Check if performance optimizations are enabled."""
        return not self.debug and not self.debug_canonical
    
    def is_accessibility_mandatory(self) -> bool:
        """Check if accessibility is mandatory."""
        return self.canonical_mode == CanonicalMode.ACCESSIBILITY_ONLY
    
    def should_select_all_elements(self) -> bool:
        """Check if all elements should be selected."""
        return self.debug or self.debug_canonical
    
    def should_use_hierarchy(self) -> bool:
        """Check if hierarchy should be used."""
        return self.use_hierarchy
    
    def should_use_two_stage(self) -> bool:
        """Check if two-stage processing should be used."""
        return self.use_two_stage
    
    def should_use_semantic_search(self) -> bool:
        """Check if semantic search should be used (vs exact DOM matching)."""
        return self.use_semantic_search
    
    def is_hierarchy_debug_enabled(self) -> bool:
        """Check if hierarchy debug is enabled."""
        return self.debug_hierarchy
    
    @classmethod
    def from_env(cls) -> 'HERConfig':
        """Create configuration from environment variables."""
        return cls()
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'HERConfig':
        """Create configuration from dictionary."""
        return cls(**config_dict)


# Global configuration instance
_config: Optional[HERConfig] = None


def get_config() -> HERConfig:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = HERConfig.from_env()
    return _config


def set_config(config: HERConfig) -> None:
    """Set the global configuration instance."""
    global _config
    _config = config


def reset_config() -> None:
    """Reset the global configuration instance."""
    global _config
    _config = None


# Cache constants for backward compatibility
MEMORY_CACHE_SIZE = 1000
DISK_CACHE_SIZE_MB = 100

def get_cache_dir() -> Path:
    """Get cache directory from configuration."""
    return get_config().cache_dir