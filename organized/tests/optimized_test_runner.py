
# Optimized Test Runner for Test Suites
import os
import time
import threading
from typing import Optional, Dict, Any
from her.runner import Runner
from her.pipeline import HybridPipeline

class TestSuiteRunner:
    """Optimized runner for test suites with model reuse"""
    
    _instance: Optional['TestSuiteRunner'] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
            
        self._initialized = True
        self._runners: Dict[str, Runner] = {}
        self._pipeline: Optional[HybridPipeline] = None
        self._model_loaded = False
        
    def get_runner(self, test_id: str = "default") -> Runner:
        """Get or create a runner for a specific test"""
        if test_id not in self._runners:
            print(f"🔧 Creating new runner for test: {test_id}")
            
            # Reuse pipeline if available
            if self._pipeline is None:
                print("📦 Loading models (one-time cost)...")
                start_time = time.time()
                self._pipeline = HybridPipeline()
                self._model_loaded = True
                print(f"   ✅ Models loaded in {time.time() - start_time:.3f}s")
            
            # Create lightweight runner with shared pipeline
            runner = Runner(headless=True)
            runner.pipeline = self._pipeline  # Share the pipeline
            self._runners[test_id] = runner
            
        return self._runners[test_id]
    
    def cleanup_runner(self, test_id: str):
        """Cleanup specific runner after test"""
        if test_id in self._runners:
            self._runners[test_id]._close()
            del self._runners[test_id]
    
    def cleanup_all(self):
        """Cleanup all runners and models"""
        for runner in self._runners.values():
            runner._close()
        self._runners.clear()
        
        if self._pipeline:
            # Add model cleanup if available
            del self._pipeline
            self._pipeline = None
            self._model_loaded = False

# Global instance
test_suite_runner = TestSuiteRunner()

# Usage in test cases:
def test_example_1():
    runner = test_suite_runner.get_runner("test_1")
    # Run test...
    test_suite_runner.cleanup_runner("test_1")

def test_example_2():
    runner = test_suite_runner.get_runner("test_2")
    # Run test...
    test_suite_runner.cleanup_runner("test_2")

# Cleanup at end of test suite
def cleanup_test_suite():
    test_suite_runner.cleanup_all()
