# 🚀 HER Framework - Complete Execution Guide

## 📋 **Quick Start (5 Minutes)**

### **1. Setup**
```bash
# Clone repository
git clone <repository-url>
cd her-framework

# Run automated setup
python setup.py

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### **2. Verify Installation**
```bash
# Check if everything is working
python -c "from her.core.runner import Runner; print('✅ HER Framework ready!')"

# Run basic tests
python -m pytest tests/unit/core/test_embedder_dims.py -v
```

### **3. Run Your First Automation**
```python
from her.core.runner import Runner

# Create runner
runner = Runner(headless=True)

# Run automation steps
steps = [
    "open https://example.com",
    "click on 'login' button",
    "type $username in 'username' field",
    "type $password in 'password' field",
    "click on 'submit' button"
]

results = runner.run(steps)
print(f"✅ Completed {len(results)} steps")
```

## 🧪 **Test Execution Guide**

### **Run All Tests**
```bash
# Complete test suite
pytest tests/ -v --tb=short

# With coverage report
pytest tests/ --cov=src/her --cov-report=html --cov-report=term
```

### **Run Specific Test Categories**

#### **Unit Tests**
```bash
# All unit tests
pytest tests/unit/ -v

# Specific unit test
pytest tests/unit/core/test_embedder_dims.py -v

# Cache tests
pytest tests/unit/core/test_cache.py -v
```

#### **Integration Tests**
```bash
# Integration tests
pytest tests/integration/ -v

# Full pipeline test
pytest tests/integration/test_integration.py -v
```

#### **End-to-End Tests**
```bash
# E2E tests (requires HER_E2E=1)
HER_E2E=1 pytest tests/e2e/ -v

# Verizon comprehensive test
HER_E2E=1 pytest tests/e2e/test_verizon_comprehensive.py -v
```

### **Test with Different Configurations**
```bash
# Test with hierarchy enabled
HER_USE_HIERARCHY=true pytest tests/ -v

# Test with two-stage processing
HER_USE_TWO_STAGE=true pytest tests/ -v

# Test with heuristics disabled
HER_DISABLE_HEURISTICS=true pytest tests/ -v
```

## 🔧 **Development Commands**

### **Code Quality**
```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/

# Run all quality checks
black src/ tests/ && flake8 src/ tests/ && mypy src/
```

### **Performance Testing**
```bash
# Run performance benchmarks
python -m pytest tests/ -v --durations=10

# Memory profiling
python -m memory_profiler scripts/performance_test.py

# Load testing
python scripts/load_test.py
```

## 🌐 **Web Interface Usage**

### **CLI Commands**
```bash
# Query elements
her query "click on phones button" --url "https://example.com"

# Execute action
her act "click on login button" --url "https://example.com"

# Get version
her version

# Clear cache
her cache --clear
```

### **Programmatic Usage**
```python
from her.core.runner import Runner
from her.core.pipeline import HybridPipeline

# Method 1: Using Runner (recommended)
runner = Runner(headless=True)
results = runner.run([
    "open https://example.com",
    "click on 'phones' button",
    "click on 'Apple' filter"
])

# Method 2: Using Pipeline directly
pipeline = HybridPipeline()
result = pipeline.query("click phones", elements)
```

## 📊 **Monitoring and Debugging**

### **Enable Debug Logging**
```bash
# Set debug environment
export HER_DEBUG=1
export HER_LOG_LEVEL=DEBUG

# Run with debug output
python your_script.py
```

### **View Metrics**
```python
from her.monitoring import metrics_collector

# Get current metrics
metrics = metrics_collector.get_metrics()
print(f"Success rate: {metrics['success_rate']:.2%}")
print(f"Average processing time: {metrics['avg_processing_time']:.3f}s")
```

### **Performance Profiling**
```python
import cProfile
from her.core.runner import Runner

# Profile execution
profiler = cProfile.Profile()
profiler.enable()

runner = Runner(headless=True)
runner.run(["open https://example.com", "click on 'test' button"])

profiler.disable()
profiler.dump_stats('her_profile.prof')
```

## 🔄 **Code Flow Examples**

### **1. Simple Element Click**
```python
# Input: "click on 'phones' button"
# Flow:
# 1. Parse intent → action="click", target="phones"
# 2. Snapshot page → capture DOM elements
# 3. Generate embeddings → MiniLM (384-d) + MarkupLM (768-d)
# 4. Hybrid search → find best matching element
# 5. Generate XPath → //button[contains(text(), 'phones')]
# 6. Execute action → Playwright click
```

### **2. Form Filling**
```python
# Input: "type $test123 in 'username' field"
# Flow:
# 1. Parse intent → action="type", target="username", value="test123"
# 2. Snapshot page → capture form elements
# 3. Find input field → //input[@name='username']
# 4. Clear and type → Playwright fill
# 5. Verify value → check input.value
```

### **3. Complex Navigation**
```python
# Input: "click on 'Apple' filter in 'phones' section"
# Flow:
# 1. Parse intent → action="click", target="Apple filter"
# 2. Snapshot page → capture all elements
# 3. Universal element detection → find filter elements
# 4. Hierarchical context → add section context
# 5. Hybrid search → prioritize filter elements
# 6. Generate selector → //button[@data-filter='Apple']
# 7. Execute action → click with retry logic
```

## 🚨 **Troubleshooting**

### **Common Issues**

#### **1. Model Not Found**
```bash
# Error: Model not found
# Solution: Install models
./scripts/install_models.sh  # Linux/Mac
# or
powershell -ExecutionPolicy Bypass -File scripts/install_models.ps1  # Windows
```

#### **2. Playwright Not Installed**
```bash
# Error: Playwright not available
# Solution: Install Playwright
pip install playwright
playwright install chromium
```

#### **3. Low Confidence Scores**
```python
# Issue: Low confidence in element selection
# Solution: Enable debug mode
import logging
logging.basicConfig(level=logging.DEBUG)

# Or check element detection
runner._detect_universal_elements(page)
```

#### **4. Memory Issues**
```python
# Issue: High memory usage
# Solution: Clean up resources
runner._close()  # Always close runner
Runner.cleanup_models()  # Clean up shared models
```

### **Debug Commands**
```bash
# Check dependencies
python tools/check_dependencies.py

# Test environment
python tools/test_env.py

# Load environment
python tools/load_env.py

# Preflight check
python scripts/testing/preflight.py

# Smoke test
python scripts/testing/smoke_run.py
```

## 📈 **Performance Optimization**

### **Memory Optimization**
```python
# Use headless mode for better performance
runner = Runner(headless=True)

# Clean up after each test
runner._close()

# Use shared pipeline (automatic)
# Models are shared across runner instances
```

### **Speed Optimization**
```python
# Enable caching
export HER_CACHE_DIR="/path/to/cache"

# Use hierarchy for better accuracy
export HER_USE_HIERARCHY=true

# Disable heuristics for pure ML approach
export HER_DISABLE_HEURISTICS=true
```

### **Batch Processing**
```python
# Process multiple queries efficiently
queries = ["click phones", "click apple", "click submit"]
for query in queries:
    result = pipeline.query(query, elements)
    # Process result
```

## 🎯 **Best Practices**

### **1. Error Handling**
```python
try:
    runner = Runner(headless=True)
    results = runner.run(steps)
    # Check results
    for result in results:
        if not result.ok:
            print(f"Step failed: {result.step}")
except Exception as e:
    print(f"Error: {e}")
finally:
    runner._close()
```

### **2. Configuration Management**
```python
# Use environment variables
import os
os.environ['HER_MODELS_DIR'] = '/path/to/models'
os.environ['HER_CACHE_DIR'] = '/path/to/cache'

# Or use config file
from her.core.config import get_config
config = get_config()
```

### **3. Testing Strategy**
```python
# Unit tests for individual components
# Integration tests for full pipeline
# E2E tests for real websites
# Performance tests for optimization
```

## 🏆 **Success Metrics**

### **Expected Performance**
- **Setup Time**: 2-3 minutes (first run)
- **Query Time**: 100-500ms per query
- **Success Rate**: 85-95% for common elements
- **Memory Usage**: 500MB-1GB with models

### **Quality Indicators**
- **Test Coverage**: 80%+ (target)
- **Code Quality**: 8.5/10 (current)
- **Documentation**: 90%+ (target)
- **Performance**: <500ms per query (target)

This guide provides everything you need to run, test, and optimize the HER framework effectively!