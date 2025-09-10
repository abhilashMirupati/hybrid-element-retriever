# HER Framework - Quick Setup Guide

## 🚀 **One-Command Setup (Recommended)**

### **Windows:**
```cmd
setup.bat
```

### **macOS/Linux:**
```bash
./setup.sh
```

### **All Platforms (Python):**
```bash
python setup.py
```

## 📋 **Manual Setup (If Needed)**

### **Step 1: Install Python Dependencies**
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### **Step 2: Install Playwright**
```bash
playwright install chromium
playwright install-deps
```

### **Step 3: Install Models**
```bash
# Windows:
.\scripts\install_models.ps1

# macOS/Linux:
./scripts/install_models.sh
```

### **Step 4: Initialize Database**
```bash
# Windows:
.\scripts\init_dbs.ps1

# macOS/Linux:
./scripts/init_dbs.sh
```

### **Step 5: Set Environment Variables**
```bash
# Windows PowerShell:
$env:HER_MODELS_DIR = (Resolve-Path 'src\her\models').Path
$env:HER_CACHE_DIR = (Resolve-Path '.\her_cache').Path

# macOS/Linux:
export HER_MODELS_DIR="$(pwd)/src/her/models"
export HER_CACHE_DIR="$(pwd)/.her_cache"
mkdir -p "$HER_CACHE_DIR"
```

### **Step 6: Verify Installation**
```bash
# Run preflight check
python scripts/preflight.py

# Run essential validation
python organized/tests/test_essential_validation.py
```

## ✅ **Verification**

After setup, you should see:
```
🚀 ESSENTIAL VALIDATION TEST
==================================================
🔍 Running comprehensive debug test...
✅ ESSENTIAL VALIDATION PASSED

📊 Test Output:
🔍 CDP MODE RESULTS:
   DOM_ONLY             | ✅ PASS | 2532 elements | 45.593s | Binding: 100.0%
   ACCESSIBILITY_ONLY   | ✅ PASS |  931 elements | 45.178s | Binding: 98.9%
   BOTH                 | ✅ PASS | 3459 elements | 45.541s | Binding: 99.7%

🧠 MODEL OPTIMIZATION RESULTS:
   Model Caching      | ✅ PASS | First: 38.262s | Second: 0.000s

🎉 ALL TESTS PASSED - FRAMEWORK IS PRODUCTION READY!
```

## 🆘 **Troubleshooting**

### **Common Issues:**

1. **Python not found:**
   - Install Python 3.10+ from python.org
   - Ensure Python is in your PATH

2. **Playwright installation fails:**
   - Run `playwright install-deps` for system dependencies
   - Check internet connection

3. **Model download fails:**
   - Check internet connection
   - Ensure sufficient disk space (5GB+)

4. **Permission denied (macOS/Linux):**
   - Run `chmod +x scripts/*.sh`
   - Check file permissions

### **Platform-Specific Issues:**

#### **Windows:**
- Use PowerShell instead of Command Prompt
- Run as Administrator if needed
- Check Windows Defender/antivirus settings

#### **macOS:**
- Install Xcode Command Line Tools: `xcode-select --install`
- Use Homebrew for Python: `brew install python@3.10`

#### **Linux:**
- Install build tools: `sudo apt install build-essential`
- Install Python dev packages: `sudo apt install python3-dev`

## 📊 **System Requirements**

- **OS**: Windows 10+, macOS 10.15+, Ubuntu 18.04+
- **Python**: 3.10 or higher
- **RAM**: 8GB (16GB recommended)
- **Storage**: 5GB free space
- **Internet**: Required for initial setup

## 🎯 **Quick Test Commands**

```bash
# Essential validation
python organized/tests/test_essential_validation.py

# Comprehensive debug test
python organized/debug/debug_comprehensive_testing.py

# All project tests
python run_all_tests.py
```

## 📚 **Documentation**

- **Full Setup Guide**: [SETUP_GUIDE.md](SETUP_GUIDE.md)
- **Project Organization**: [organized/PROJECT_ORGANIZATION.md](organized/PROJECT_ORGANIZATION.md)
- **Quick Reference**: [organized/QUICK_REFERENCE.md](organized/QUICK_REFERENCE.md)

---

**Ready to use HER Framework! 🎉**