"""
Configuration Service - Centralized configuration management
Provides a single point of access for all configuration needs.
"""

from typing import Optional
from ..config.settings import get_config, HERConfig


class ConfigService:
    """Centralized configuration service for HER framework."""
    
    def __init__(self, config: Optional[HERConfig] = None):
        """Initialize configuration service.
        
        Args:
            config: Optional configuration instance. If None, uses global config.
        """
        self._config = config or get_config()
    
    @property
    def config(self) -> HERConfig:
        """Get the current configuration."""
        return self._config
    
    def should_use_hierarchy(self) -> bool:
        """Check if hierarchy should be used."""
        return self._config.should_use_hierarchy()
    
    def should_use_two_stage(self) -> bool:
        """Check if two-stage processing should be used."""
        return self._config.should_use_two_stage()
    
    def should_disable_heuristics(self) -> bool:
        """Check if heuristics should be disabled."""
        return self._config.should_disable_heuristics()
    
    def should_use_dom(self) -> bool:
        """Check if DOM should be used."""
        return self._config.should_use_dom()
    
    def should_use_accessibility(self) -> bool:
        """Check if accessibility tree should be used."""
        return self._config.should_use_accessibility()
    
    def is_debug_enabled(self) -> bool:
        """Check if debug mode is enabled."""
        return self._config.debug
    
    def is_performance_optimized(self) -> bool:
        """Check if performance optimizations are enabled."""
        return self._config.is_performance_optimized()
    
    def get_max_elements(self) -> int:
        """Get maximum number of elements to process."""
        return self._config.max_elements
    
    def get_max_text_length(self) -> int:
        """Get maximum text length for processing."""
        return self._config.max_text_length
    
    def get_cache_size_mb(self) -> int:
        """Get cache size in MB."""
        return self._config.cache_size_mb
    
    def get_browser_timeout(self) -> int:
        """Get browser timeout in milliseconds."""
        return self._config.browser_timeout
    
    def is_headless(self) -> bool:
        """Check if browser should run in headless mode."""
        return self._config.headless
    
    def is_e2e_enabled(self) -> bool:
        """Check if E2E testing is enabled."""
        return self._config.e2e_enabled


# Global configuration service instance
_config_service: Optional[ConfigService] = None


def get_config_service() -> ConfigService:
    """Get the global configuration service instance."""
    global _config_service
    if _config_service is None:
        _config_service = ConfigService()
    return _config_service


def set_config_service(service: ConfigService) -> None:
    """Set the global configuration service instance."""
    global _config_service
    _config_service = service


def reset_config_service() -> None:
    """Reset the global configuration service instance."""
    global _config_service
    _config_service = None