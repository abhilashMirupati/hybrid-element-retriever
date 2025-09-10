#!/usr/bin/env python3
"""
Test script to verify environment variable loading from .env file.
"""

import os
import sys
from pathlib import Path

# Add src to path so we can import her modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_env_loading():
    """Test that environment variables are loaded correctly."""
    print("Testing environment variable loading...")
    
    # Import her module (this should trigger env loading)
    import her
    
    # Check some key environment variables
    env_vars_to_check = [
        "HER_MODELS_DIR",
        "HER_CACHE_DIR", 
        "HER_STRICT",
        "HER_PERF_OPT",
        "HER_FORCE_AX",
        "HER_ALL_ELEMENTS",
        "HER_CANONICAL_MODE",
        "HER_USE_HIERARCHY",
        "HER_USE_TWO_STAGE",
        "HER_DEBUG_HIERARCHY",
        "HER_DISABLE_HEURISTICS",
        "HER_DEBUG_CANONICAL",
        "HER_DEBUG_CANDIDATES",
        "HER_E2E",
        "HER_DRY_RUN"
    ]
    
    print("\nEnvironment variables loaded from .env file:")
    print("=" * 50)
    
    for var in env_vars_to_check:
        value = os.environ.get(var, "NOT SET")
        print(f"{var:25} = {value}")
    
    print("\nTesting HER configuration...")
    try:
        from her.config import get_config
        config = get_config()
        
        print(f"Canonical Mode: {config.get_canonical_mode().value}")
        print(f"Use DOM: {config.should_use_dom()}")
        print(f"Use Accessibility: {config.should_use_accessibility()}")
        print(f"Performance Optimized: {config.is_performance_optimized()}")
        print(f"Accessibility Mandatory: {config.is_accessibility_mandatory()}")
        print(f"Select All Elements: {config.should_select_all_elements()}")
        print(f"Use Hierarchy: {config.should_use_hierarchy()}")
        print(f"Use Two-Stage: {config.should_use_two_stage()}")
        print(f"Debug Hierarchy: {config.is_hierarchy_debug_enabled()}")
        print(f"Heuristics Disabled: {config.disable_heuristics}")
        
    except Exception as e:
        print(f"Error loading HER configuration: {e}")
    
    print("\nEnvironment variable loading test completed!")

if __name__ == "__main__":
    test_env_loading()