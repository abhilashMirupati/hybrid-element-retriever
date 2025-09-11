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

def setup_system_python():
    """Install Python dependencies using system Python"""
    print("📦 Installing Python dependencies using system Python...")
    
    # Try normal installation first
    if run_command([sys.executable, "-m", "pip", "install", "--upgrade", "pip"]):
        if run_command([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]):
            print("✅ System Python dependencies installed successfully!")
            return True
    
    # If normal installation fails, try with --break-system-packages
    print("⚠️  Normal installation failed, trying with --break-system-packages...")
    print("💡 This is safe for development but not recommended for production.")
    
    if not run_command([sys.executable, "-m", "pip", "install", "--upgrade", "pip", "--break-system-packages"]):
        print("❌ Failed to upgrade pip even with --break-system-packages")
        print("\n🔧 Manual installation required:")
        print("   1. Install python3-venv: sudo apt install python3-venv")
        print("   2. Create venv: python3 -m venv venv")
        print("   3. Activate: source venv/bin/activate")
        print("   4. Install: pip install -r requirements.txt")
        return False
    
    if not run_command([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--break-system-packages"]):
        print("❌ Failed to install requirements even with --break-system-packages")
        print("\n🔧 Manual installation required:")
        print("   1. Install python3-venv: sudo apt install python3-venv")
        print("   2. Create venv: python3 -m venv venv")
        print("   3. Activate: source venv/bin/activate")
        print("   4. Install: pip install -r requirements.txt")
        return False
    
    print("✅ System Python dependencies installed successfully!")
    return True

def setup_python_deps():
    """Install Python dependencies"""
    print("\n📦 Installing Python dependencies...")
    
    # Check if virtual environment exists and is valid
    venv_path = Path("venv")
    if not venv_path.exists():
        print("Creating virtual environment...")
        try:
            if not run_command([sys.executable, "-m", "venv", "venv"]):
                print("\n❌ Virtual environment creation failed!")
                print("💡 This usually means python3-venv package is not installed.")
                print("   On Debian/Ubuntu systems, run:")
                print("   sudo apt install python3-venv")
                print("   On other systems, install the appropriate venv package.")
                print("\n🔄 Falling back to system Python installation...")
                # Clean up any partial venv directory
                import shutil
                if venv_path.exists():
                    shutil.rmtree(venv_path)
                return setup_system_python()
        except Exception as e:
            print(f"\n❌ Virtual environment creation failed: {e}")
            print("🔄 Falling back to system Python installation...")
            # Clean up any partial venv directory
            import shutil
            if venv_path.exists():
                shutil.rmtree(venv_path)
            return setup_system_python()
    else:
        # Check if existing venv is valid
        if platform.system().lower() == "windows":
            python_cmd = venv_path / "Scripts" / "python.exe"
        else:
            python_cmd = venv_path / "bin" / "python"
        
        # Test if the venv Python works
        try:
            result = subprocess.run([str(python_cmd), "-c", "import sys; print('OK')"], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                print("⚠️  Existing virtual environment appears broken, recreating...")
                import shutil
                shutil.rmtree(venv_path)
                return setup_system_python()
        except Exception:
            print("⚠️  Existing virtual environment appears broken, recreating...")
            import shutil
            shutil.rmtree(venv_path)
            return setup_system_python()
    
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
    
    # Determine python executable - check if venv exists, otherwise use system Python
    venv_path = Path("venv")
    if venv_path.exists():
        if platform.system().lower() == "windows":
            python_cmd = venv_path / "Scripts" / "python.exe"
        else:
            python_cmd = venv_path / "bin" / "python"
    else:
        # Use system Python
        python_cmd = sys.executable
    
    # Install Playwright
    if not run_command([str(python_cmd), "-m", "pip", "install", "playwright", "--break-system-packages"]):
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
    
    print(f"⚠️  Model installation script not found for {platform_name}")
    print("💡 Models will be downloaded automatically when first used.")
    print("   You can also download them manually by running:")
    print("   python -c \"from src.her.core.pipeline import HybridPipeline; HybridPipeline()\"")
    return True  # Don't fail the setup for missing model scripts

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
    
    print(f"⚠️  Database initialization script not found for {platform_name}")
    print("💡 Database will be created automatically when first used.")
    print("   You can also initialize it manually by running:")
    print("   python -c \"from src.her.core.pipeline import HybridPipeline; HybridPipeline()\"")
    return True  # Don't fail the setup for missing database scripts

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
    
    # Determine python executable - check if venv exists, otherwise use system Python
    venv_path = Path("venv")
    if venv_path.exists():
        if platform.system().lower() == "windows":
            python_cmd = venv_path / "Scripts" / "python.exe"
        else:
            python_cmd = venv_path / "bin" / "python"
    else:
        # Use system Python
        python_cmd = sys.executable
    
    # Run preflight check
    if not run_command([str(python_cmd), "scripts/testing/preflight.py"]):
        print("⚠️  Preflight check failed, but continuing...")
        print("💡 You can run the preflight check manually later:")
        print(f"   {python_cmd} scripts/testing/preflight.py")
    
    # Run essential validation
    if not run_command([str(python_cmd), "-m", "pytest", "tests/unit/core/test_embedder_dims.py", "-v"]):
        print("⚠️  Essential validation failed, but continuing...")
        print("💡 You can run the tests manually later:")
        print(f"   {python_cmd} -m pytest tests/ -v")
    
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
    print("   python -m pytest tests/ -v")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)