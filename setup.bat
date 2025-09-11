@echo off
REM HER Framework - Windows Setup Script
echo 🚀 HER Framework - Windows Setup
echo ================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

REM Run the Python setup script
python setup.py

if errorlevel 1 (
    echo ❌ Setup failed
    pause
    exit /b 1
)

echo.
echo ✅ Setup completed successfully!
echo.
echo Next steps:
echo 1. Activate virtual environment:
echo    venv\Scripts\activate
echo.
echo 2. Set environment variables:
echo    $env:HER_MODELS_DIR = (Resolve-Path 'src\her\models').Path
echo    $env:HER_CACHE_DIR = (Resolve-Path '.\her_cache').Path
echo.
echo 3. Run tests:
echo    python -m pytest tests/ -v
echo.
pause