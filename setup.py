#!/usr/bin/env python3
"""
HER Framework - Cross-Platform Setup Script
Automatically detects platform and runs appropriate setup commands
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def run_command(cmd, shell=False):
    """Run a command and return success status"""
    try:
        if shell:
            result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        else:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ {cmd}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {cmd}")
        print(f"   Error: {e.stderr}")
        return False

def detect_platform():
    """Detect the current platform"""
    system = platform.system().lower()
    if system == "windows":
        return "windows"
    elif system == "darwin":
        return "macos"
    elif system == "linux":
        return "linux"
    else:
        return "unknown"

def setup_python_deps():
    """Install Python dependencies"""
    print("\n📦 Installing Python dependencies...")
    
    # Check if virtual environment exists
    venv_path = Path("venv")
    if not venv_path.exists():
        print("Creating virtual environment...")
        if not run_command([sys.executable, "-m", "venv", "venv"]):
            return False
    
    # Determine activation script path
    if platform.system().lower() == "windows":
        activate_script = venv_path / "Scripts" / "activate.bat"
        pip_cmd = [str(venv_path / "Scripts" / "python.exe"), "-m", "pip"]
    else:
        activate_script = venv_path / "bin" / "activate"
        pip_cmd = [str(venv_path / "bin" / "python"), "-m", "pip"]
    
    # Install requirements
    if not run_command(pip_cmd + ["install", "--upgrade", "pip"]):
        return False
    
    if not run_command(pip_cmd + ["install", "-r", "requirements.txt"]):
        return False
    
    return True

def setup_playwright():
    """Install Playwright and browser"""
    print("\n🎭 Installing Playwright...")
    
    # Determine python executable
    if platform.system().lower() == "windows":
        python_cmd = Path("venv") / "Scripts" / "python.exe"
    else:
        python_cmd = Path("venv") / "bin" / "python"
    
    # Install Playwright
    if not run_command([str(python_cmd), "-m", "pip", "install", "playwright"]):
        return False
    
    # Install browser
    if not run_command([str(python_cmd), "-m", "playwright", "install", "chromium"]):
        return False
    
    # Install system dependencies
    if not run_command([str(python_cmd), "-m", "playwright", "install-deps"]):
        print("⚠️  System dependencies installation failed, but continuing...")
    
    return True

def setup_models():
    """Install models using platform-specific script"""
    print("\n🤖 Installing models...")
    
    platform_name = detect_platform()
    
    if platform_name == "windows":
        script_path = Path("scripts") / "install_models.ps1"
        if script_path.exists():
            return run_command(f"powershell -ExecutionPolicy Bypass -File {script_path}", shell=True)
    else:
        script_path = Path("scripts") / "install_models.sh"
        if script_path.exists():
            # Make executable
            os.chmod(script_path, 0o755)
            return run_command([str(script_path)])
    
    print(f"❌ Model installation script not found for {platform_name}")
    return False

def setup_database():
    """Initialize database using platform-specific script"""
    print("\n🗄️  Initializing database...")
    
    platform_name = detect_platform()
    
    if platform_name == "windows":
        script_path = Path("scripts") / "init_dbs.ps1"
        if script_path.exists():
            return run_command(f"powershell -ExecutionPolicy Bypass -File {script_path}", shell=True)
    else:
        script_path = Path("scripts") / "init_dbs.sh"
        if script_path.exists():
            # Make executable
            os.chmod(script_path, 0o755)
            return run_command([str(script_path)])
    
    print(f"❌ Database initialization script not found for {platform_name}")
    return False

def set_environment_variables():
    """Set environment variables"""
    print("\n🔧 Setting environment variables...")
    
    # Get current directory
    current_dir = Path.cwd()
    models_dir = current_dir / "src" / "her" / "models"
    cache_dir = current_dir / ".her_cache"
    
    # Create cache directory
    cache_dir.mkdir(exist_ok=True)
    
    # Set environment variables
    os.environ["HER_MODELS_DIR"] = str(models_dir)
    os.environ["HER_CACHE_DIR"] = str(cache_dir)
    
    print(f"   HER_MODELS_DIR = {models_dir}")
    print(f"   HER_CACHE_DIR = {cache_dir}")
    
    return True

def verify_installation():
    """Verify the installation"""
    print("\n✅ Verifying installation...")
    
    # Determine python executable
    if platform.system().lower() == "windows":
        python_cmd = Path("venv") / "Scripts" / "python.exe"
    else:
        python_cmd = Path("venv") / "bin" / "python"
    
    # Run preflight check
    if not run_command([str(python_cmd), "scripts/preflight.py"]):
        print("❌ Preflight check failed")
        return False
    
    # Run essential validation
    if not run_command([str(python_cmd), "organized/tests/test_essential_validation.py"]):
        print("❌ Essential validation failed")
        return False
    
    return True

def main():
    """Main setup function"""
    print("🚀 HER Framework - Cross-Platform Setup")
    print("=" * 50)
    
    platform_name = detect_platform()
    print(f"Detected platform: {platform_name}")
    
    if platform_name == "unknown":
        print("❌ Unsupported platform. Please use Windows, macOS, or Linux.")
        return False
    
    # Check Python version
    if sys.version_info < (3, 10):
        print("❌ Python 3.10 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    
    print(f"✅ Python version: {sys.version}")
    
    # Setup steps
    steps = [
        ("Python Dependencies", setup_python_deps),
        ("Playwright", setup_playwright),
        ("Models", setup_models),
        ("Database", setup_database),
        ("Environment Variables", set_environment_variables),
        ("Verification", verify_installation),
    ]
    
    for step_name, step_func in steps:
        print(f"\n{'='*20} {step_name} {'='*20}")
        if not step_func():
            print(f"❌ Setup failed at step: {step_name}")
            return False
    
    print("\n🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Activate virtual environment:")
    if platform_name == "windows":
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    print("2. Set environment variables in your shell:")
    if platform_name == "windows":
        print("   $env:HER_MODELS_DIR = (Resolve-Path 'src\\her\\models').Path")
        print("   $env:HER_CACHE_DIR = (Resolve-Path '.\\her_cache').Path")
    else:
        print("   export HER_MODELS_DIR=\"$(pwd)/src/her/models\"")
        print("   export HER_CACHE_DIR=\"$(pwd)/.her_cache\"")
    print("3. Run tests:")
    print("   python organized/tests/test_essential_validation.py")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)