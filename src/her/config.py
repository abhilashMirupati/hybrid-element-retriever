"""Configuration settings for HER framework."""

import os
from enum import Enum
from typing import Optional


class CanonicalMode(Enum):
    """Canonical descriptor building modes."""
    DOM_ONLY = "dom_only"           # Only DOM attributes
    ACCESSIBILITY_ONLY = "accessibility_only"  # Only accessibility tree attributes  
    BOTH = "both"                   # Both DOM + accessibility tree (default)


class HERConfig:
    """HER framework configuration."""
    
    def __init__(self):
        # Canonical descriptor building mode
        self.canonical_mode = self._get_canonical_mode()
        
        # Performance settings
        self.enable_performance_optimization = os.getenv("HER_PERF_OPT", "1") == "1"
        
        # Accessibility settings
        self.force_accessibility_extraction = os.getenv("HER_FORCE_AX", "1") == "1"
        
        # Element selection settings
        self.select_all_elements_for_minilm = os.getenv("HER_ALL_ELEMENTS", "1") == "1"
        
        # Debug settings
        self.debug_canonical_building = os.getenv("HER_DEBUG_CANONICAL", "0") == "1"
        
        # Hierarchy settings
        self.use_hierarchy = os.getenv("HER_USE_HIERARCHY", "false").lower() == "true"
        self.use_two_stage = os.getenv("HER_USE_TWO_STAGE", "false").lower() == "true"
        self.debug_hierarchy = os.getenv("HER_DEBUG_HIERARCHY", "false").lower() == "true"
    
    def _get_canonical_mode(self) -> CanonicalMode:
        """Get canonical descriptor building mode from environment."""
        mode = os.getenv("HER_CANONICAL_MODE", "both").lower()
        
        if mode == "dom_only":
            return CanonicalMode.DOM_ONLY
        elif mode == "accessibility_only":
            return CanonicalMode.ACCESSIBILITY_ONLY
        elif mode == "both":
            return CanonicalMode.BOTH
        else:
            print(f"⚠️  Unknown canonical mode '{mode}', defaulting to 'both'")
            return CanonicalMode.BOTH
    
    def get_canonical_mode(self) -> CanonicalMode:
        """Get current canonical descriptor building mode."""
        # Read environment variable dynamically each time
        return self._get_canonical_mode()
    
    def set_canonical_mode(self, mode: CanonicalMode) -> None:
        """Set canonical descriptor building mode."""
        self.canonical_mode = mode
        print(f"🔧 Canonical descriptor mode set to: {mode.value}")
    
    def should_use_dom(self) -> bool:
        """Check if DOM attributes should be included."""
        mode = self.get_canonical_mode()
        return mode in [CanonicalMode.DOM_ONLY, CanonicalMode.BOTH]
    
    def should_use_accessibility(self) -> bool:
        """Check if accessibility tree should be included."""
        mode = self.get_canonical_mode()
        return mode in [CanonicalMode.ACCESSIBILITY_ONLY, CanonicalMode.BOTH]
    
    def is_performance_optimized(self) -> bool:
        """Check if performance optimization is enabled."""
        return self.enable_performance_optimization
    
    def is_accessibility_mandatory(self) -> bool:
        """Check if accessibility extraction is mandatory."""
        return self.force_accessibility_extraction
    
    def should_select_all_elements(self) -> bool:
        """Check if all elements should be selected for MiniLM."""
        return self.select_all_elements_for_minilm
    
    def should_use_hierarchy(self) -> bool:
        """Check if hierarchical context should be used."""
        return self.use_hierarchy
    
    def should_use_two_stage(self) -> bool:
        """Check if two-stage MarkupLM processing should be used."""
        return self.use_two_stage
    
    def is_hierarchy_debug_enabled(self) -> bool:
        """Check if hierarchy debugging is enabled."""
        return self.debug_hierarchy


# Global configuration instance
config = HERConfig()


def get_config() -> HERConfig:
    """Get global configuration instance."""
    return config


def set_canonical_mode(mode: CanonicalMode) -> None:
    """Set canonical descriptor building mode globally."""
    config.set_canonical_mode(mode)


def print_config() -> None:
    """Print current configuration."""
    print(f"\n🔧 HER Configuration:")
    print(f"   Canonical Mode: {config.get_canonical_mode().value}")
    print(f"   Use DOM: {config.should_use_dom()}")
    print(f"   Use Accessibility: {config.should_use_accessibility()}")
    print(f"   Performance Optimized: {config.is_performance_optimized()}")
    print(f"   Accessibility Mandatory: {config.is_accessibility_mandatory()}")
    print(f"   Select All Elements: {config.should_select_all_elements()}")
    print(f"   Debug Canonical: {config.debug_canonical_building}")
    print(f"   Use Hierarchy: {config.should_use_hierarchy()}")
    print(f"   Use Two-Stage: {config.should_use_two_stage()}")
    print(f"   Debug Hierarchy: {config.is_hierarchy_debug_enabled()}")