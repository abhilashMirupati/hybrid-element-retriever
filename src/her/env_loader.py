"""
Environment variable loader for HER framework.

This module automatically loads environment variables from .env file
when imported. It should be imported before any other HER modules.
"""

import os
from pathlib import Path


def _load_env_file(env_file_path: str = ".env") -> None:
    """
    Load environment variables from .env file.
    
    Args:
        env_file_path: Path to the .env file
    """
    try:
        # Look for .env file in current directory, config directory, and parent directories
        current_dir = Path.cwd()
        env_path = None
        
        # Check current directory, config directory, and parent directories
        search_paths = [current_dir, current_dir / "config"] + list(current_dir.parents)
        for path in search_paths:
            potential_env = path / env_file_path
            if potential_env.exists():
                env_path = potential_env
                break
        
        if not env_path:
            return  # No .env file found, use system environment variables
    except Exception as e:
        # Silently fail if there are issues with path resolution
        return
    
    with open(env_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
                
            # Parse KEY=VALUE pairs
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                
                # Only set if not already set (respect existing environment)
                if key not in os.environ:
                    os.environ[key] = value


# Automatically load environment variables when this module is imported
_load_env_file()