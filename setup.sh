#!/bin/bash
# HER Framework - macOS/Linux Setup Script

echo "🚀 HER Framework - macOS/Linux Setup"
echo "===================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed or not in PATH"
    echo "Please install Python 3.10+ using your package manager"
    echo "  macOS: brew install python@3.10"
    echo "  Ubuntu/Debian: sudo apt install python3.10"
    echo "  CentOS/RHEL: sudo yum install python3.10"
    exit 1
fi

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
required_version="3.10"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.10 or higher is required"
    echo "   Current version: $python_version"
    exit 1
fi

echo "✅ Python version: $python_version"

# Run the Python setup script
python3 setup.py

if [ $? -ne 0 ]; then
    echo "❌ Setup failed"
    exit 1
fi

echo ""
echo "✅ Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Activate virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "2. Set environment variables:"
echo "   export HER_MODELS_DIR=\"\$(pwd)/src/her/models\""
echo "   export HER_CACHE_DIR=\"\$(pwd)/.her_cache\""
echo ""
echo "3. Run tests:"
echo "   python organized/tests/test_essential_validation.py"
echo ""