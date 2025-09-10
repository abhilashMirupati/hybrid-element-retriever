#!/usr/bin/env python3
"""
Environment variable loader for HER framework.

This script loads environment variables from .env file and makes them available
to the HER framework. It can be used in two ways:

1. As a module: import load_env before importing her modules
2. As a script: python load_env.py to set environment variables in current shell

Usage:
    # Method 1: Import before using HER
    import load_env
    from her import pipeline
    
    # Method 2: Source environment variables
    eval "$(python load_env.py)"
"""

import os
import sys
from pathlib import Path


def load_env_file(env_file_path: str = ".env") -> dict:
    """
    Load environment variables from .env file.
    
    Args:
        env_file_path: Path to the .env file
        
    Returns:
        Dictionary of environment variables
    """
    env_vars = {}
    env_path = Path(env_file_path)
    
    if not env_path.exists():
        print(f"Warning: {env_file_path} not found. Using system environment variables only.")
        return env_vars
    
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
                
                env_vars[key] = value
            else:
                print(f"Warning: Invalid line {line_num} in {env_file_path}: {line}")
    
    return env_vars


def set_environment_variables(env_vars: dict) -> None:
    """Set environment variables in the current process."""
    for key, value in env_vars.items():
        # Only set if not already set (respect existing environment)
        if key not in os.environ:
            os.environ[key] = value


def export_environment_variables(env_vars: dict) -> None:
    """Print export statements for shell sourcing."""
    for key, value in env_vars.items():
        # Escape special characters for shell
        escaped_value = value.replace('"', '\\"').replace('$', '\\$')
        print(f'export {key}="{escaped_value}"')


def main():
    """Main function for command-line usage."""
    env_file = ".env"
    export_mode = False
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--export":
            export_mode = True
            if len(sys.argv) > 2:
                env_file = sys.argv[2]
        else:
            env_file = sys.argv[1]
    
    env_vars = load_env_file(env_file)
    
    if export_mode:
        # Export mode for shell sourcing
        export_environment_variables(env_vars)
    else:
        # Set environment variables in current process
        set_environment_variables(env_vars)
        print(f"Loaded {len(env_vars)} environment variables from {env_file}")


if __name__ == "__main__":
    main()