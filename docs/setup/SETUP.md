# HER Framework Setup Guide

## 🚀 Quick Start

### **One-Command Setup (Recommended)**

#### Windows:
```cmd
setup.bat
```

#### macOS/Linux:
```bash
./setup.sh
```

#### All Platforms (Python):
```bash
python setup.py
```

## 📋 Manual Setup

### **Step 1: Prerequisites**

- **Python 3.8+** installed
- **Git** for cloning repository
- **Virtual environment** (recommended)

### **Step 2: Clone and Setup**

```bash
# Clone repository
git clone <repository-url>
cd her-framework

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### **Step 3: Environment Configuration**

```bash
# Copy environment configuration
cp config/.env.example config/.env

# Edit configuration (optional)
nano config/.env

# Load environment variables
python tools/load_env.py
```

### **Step 4: Install Models**

```bash
# Install ML models
python scripts/setup/install_models.sh
# or
python scripts/setup/install_models.ps1
```

### **Step 5: Initialize Database**

```bash
# Initialize cache database
python scripts/setup/init_dbs.sh
# or
python scripts/setup/init_dbs.ps1
```

### **Step 6: Verify Installation**

```bash
# Check dependencies
python tools/check_dependencies.py

# Test environment
python tools/test_env.py

# Run smoke test
python scripts/testing/smoke_run.py
```

## 🔧 Configuration

### **Environment Variables**

See [Environment Configuration Guide](../guides/environment-configuration.md) for complete configuration options.

### **Key Variables**

```bash
# Required
HER_MODELS_DIR=./src/her/models
HER_CACHE_DIR=./.her_cache

# Optional
HER_STRICT=1
HER_PERF_OPT=1
HER_FORCE_AX=1
```

## 🐛 Troubleshooting

### **Common Issues**

1. **Missing Dependencies**
   ```bash
   python tools/check_dependencies.py
   ```

2. **Environment Not Loading**
   ```bash
   python tools/test_env.py
   ```

3. **Import Errors**
   - Ensure you're running from project root
   - Check Python path includes `src/` directory

4. **Permission Errors**
   - Ensure scripts are executable: `chmod +x *.sh`
   - Check file permissions

### **Platform-Specific Issues**

#### Windows
- Use PowerShell or Command Prompt
- Ensure Python is in PATH
- Use `.ps1` scripts for PowerShell

#### macOS/Linux
- Ensure scripts are executable
- Use `source` to activate virtual environment
- Check file permissions

## 📚 Next Steps

- [Environment Configuration](../guides/environment-configuration.md)
- [Dependency Analysis](../development/dependency-analysis.md)
- [Migration Guide](../development/migration-guide.md)

## 🆘 Support

If you encounter issues:

1. Check this guide first
2. Run dependency checker: `python tools/check_dependencies.py`
3. Test environment: `python tools/test_env.py`
4. Check logs for specific error messages