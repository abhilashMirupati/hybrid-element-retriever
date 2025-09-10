# HER Framework - Cross-Platform Setup Guide

## 🚀 **Quick Start (All Platforms)**

### **Step 1: Clone Repository**
```bash
git clone <repository-url>
cd her-framework
```

### **Step 2: Install Python Dependencies**
```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### **Step 3: Install Playwright Browser**
```bash
# Install Playwright and Chromium
playwright install chromium

# Install system dependencies (if needed)
playwright install-deps
```

### **Step 4: Install Models**
```bash
# Windows PowerShell:
.\scripts\install_models.ps1

# macOS/Linux:
./scripts/install_models.sh
```

### **Step 5: Initialize Database**
```bash
# Windows PowerShell:
.\scripts\init_dbs.ps1

# macOS/Linux:
./scripts/init_dbs.sh
```

### **Step 6: Set Environment Variables**
```bash
# Windows PowerShell:
$env:HER_MODELS_DIR = (Resolve-Path 'src\her\models').Path
$env:HER_CACHE_DIR = (Resolve-Path '.\her_cache').Path

# macOS/Linux:
export HER_MODELS_DIR="$(pwd)/src/her/models"
export HER_CACHE_DIR="$(pwd)/.her_cache"
mkdir -p "$HER_CACHE_DIR"
```

### **Step 7: Verify Installation**
```bash
# Run preflight check
python scripts/preflight.py

# Run essential validation
python organized/tests/test_essential_validation.py
```

## 📋 **Detailed Platform-Specific Instructions**

### **Windows Setup**

#### **Prerequisites:**
- Python 3.10+ (download from python.org)
- PowerShell 5.1+ (included with Windows 10+)
- Git (download from git-scm.com)

#### **Step-by-Step:**
1. **Open PowerShell as Administrator**
2. **Install Python dependencies:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

3. **Install Playwright:**
   ```powershell
   playwright install chromium
   playwright install-deps
   ```

4. **Install models:**
   ```powershell
   .\scripts\install_models.ps1
   ```

5. **Initialize database:**
   ```powershell
   .\scripts\init_dbs.ps1
   ```

6. **Set environment variables:**
   ```powershell
   $env:HER_MODELS_DIR = (Resolve-Path 'src\her\models').Path
   $env:HER_CACHE_DIR = (Resolve-Path '.\her_cache').Path
   ```

### **macOS Setup**

#### **Prerequisites:**
- Python 3.10+ (via Homebrew: `brew install python@3.10`)
- Git (via Homebrew: `brew install git`)

#### **Step-by-Step:**
1. **Open Terminal**
2. **Install Python dependencies:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Install Playwright:**
   ```bash
   playwright install chromium
   playwright install-deps
   ```

4. **Install models:**
   ```bash
   chmod +x scripts/install_models.sh
   ./scripts/install_models.sh
   ```

5. **Initialize database:**
   ```bash
   chmod +x scripts/init_dbs.sh
   ./scripts/init_dbs.sh
   ```

6. **Set environment variables:**
   ```bash
   export HER_MODELS_DIR="$(pwd)/src/her/models"
   export HER_CACHE_DIR="$(pwd)/.her_cache"
   mkdir -p "$HER_CACHE_DIR"
   ```

### **Linux Setup**

#### **Prerequisites:**
- Python 3.10+ (via package manager)
- Git (via package manager)
- Build tools (for some dependencies)

#### **Ubuntu/Debian:**
```bash
# Install system dependencies
sudo apt update
sudo apt install python3.10 python3.10-venv python3-pip git build-essential

# Install Python dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Install Playwright
playwright install chromium
playwright install-deps

# Install models
chmod +x scripts/install_models.sh
./scripts/install_models.sh

# Initialize database
chmod +x scripts/init_dbs.sh
./scripts/init_dbs.sh

# Set environment variables
export HER_MODELS_DIR="$(pwd)/src/her/models"
export HER_CACHE_DIR="$(pwd)/.her_cache"
mkdir -p "$HER_CACHE_DIR"
```

#### **CentOS/RHEL/Fedora:**
```bash
# Install system dependencies
sudo yum install python3.10 python3-pip git gcc gcc-c++ make
# or for newer versions:
sudo dnf install python3.10 python3-pip git gcc gcc-c++ make

# Follow same steps as Ubuntu/Debian
```

## 🔧 **Troubleshooting**

### **Common Issues:**

#### **1. Python Version Issues**
```bash
# Check Python version
python --version
# Should be 3.10 or higher

# If using python3 command:
python3 --version
```

#### **2. Playwright Installation Issues**
```bash
# Reinstall Playwright
pip uninstall playwright
pip install playwright
playwright install chromium

# Install system dependencies
playwright install-deps
```

#### **3. Model Download Issues**
```bash
# Check internet connection
# Models are downloaded from Hugging Face Hub

# Retry model installation
# Windows:
.\scripts\install_models.ps1
# macOS/Linux:
./scripts/install_models.sh
```

#### **4. Permission Issues (macOS/Linux)**
```bash
# Make scripts executable
chmod +x scripts/*.sh

# Run with proper permissions
./scripts/install_models.sh
```

#### **5. Environment Variable Issues**
```bash
# Check if variables are set
echo $HER_MODELS_DIR
echo $HER_CACHE_DIR

# Windows PowerShell:
echo $env:HER_MODELS_DIR
echo $env:HER_CACHE_DIR
```

### **Verification Commands:**

#### **Check Installation:**
```bash
# Run preflight check
python scripts/preflight.py

# Expected output:
# PREFLIGHT_OK: Playwright & Chromium launchable, models present, SQLite DB accessible ✅
```

#### **Run Tests:**
```bash
# Essential validation
python organized/tests/test_essential_validation.py

# Comprehensive debug test
python organized/debug/debug_comprehensive_testing.py
```

## 📊 **System Requirements**

### **Minimum Requirements:**
- **OS**: Windows 10+, macOS 10.15+, Ubuntu 18.04+
- **Python**: 3.10 or higher
- **RAM**: 8GB (16GB recommended)
- **Storage**: 5GB free space (for models and cache)
- **Internet**: Required for initial model download

### **Recommended Requirements:**
- **OS**: Windows 11, macOS 12+, Ubuntu 20.04+
- **Python**: 3.11 or higher
- **RAM**: 16GB or more
- **Storage**: 10GB free space
- **CPU**: Multi-core processor

## 🎯 **Quick Verification**

After setup, run this command to verify everything works:

```bash
python organized/tests/test_essential_validation.py
```

**Expected output:**
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

## 🆘 **Getting Help**

If you encounter issues:

1. **Check the troubleshooting section above**
2. **Verify all prerequisites are installed**
3. **Run the preflight check**: `python scripts/preflight.py`
4. **Check environment variables are set correctly**
5. **Ensure you have sufficient disk space and RAM**

The framework is now ready for production use across all platforms! 🎉