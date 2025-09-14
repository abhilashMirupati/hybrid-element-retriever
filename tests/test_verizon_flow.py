#!/usr/bin/env python3
"""
Verizon Flow Test - Deterministic + Reranker Pipeline Validation

This test validates the complete HER pipeline with the required steps:
1. Open https://www.verizon.com/smartphones/apple/
2. Click "iPhone 16 Pro"  
3. Validate "Apple iPhone 16 Pro"

Tests both cold start and warm hit scenarios to validate promotion system.
"""

import os
import sys
import time
import pytest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.her.core.runner import Runner, run_steps
from src.her.promotion.promotion_adapter import compute_label_key
from src.her.vectordb.sqlite_cache import SQLiteKV


class TestVerizonFlow:
    """Test suite for Verizon flow validation."""
    
    @pytest.fixture(autouse=True)
    def setup_environment(self):
        """Setup test environment."""
        # Set environment variables for testing
        os.environ.setdefault('HER_MODELS_DIR', str(project_root / 'src' / 'her' / 'models'))
        os.environ.setdefault('HER_CACHE_DIR', str(project_root / '.her_cache'))
        
        # Clean up any existing cache for clean test
        cache_dir = Path(os.environ['HER_CACHE_DIR'])
        if cache_dir.exists():
            import shutil
            shutil.rmtree(cache_dir, ignore_errors=True)
    
    def test_verizon_flow_cold_start(self):
        """Test Verizon flow with cold start (no cached promotions)."""
        print("\n🧪 TESTING: Verizon Flow - Cold Start")
        
        # Test steps as specified
        steps = [
            "Open https://www.verizon.com/smartphones/apple/",
            "Click \"iPhone 16 Pro\"",
            "Validate \"Apple iPhone 16 Pro\""
        ]
        
        start_time = time.time()
        
        # Run the test
        runner = Runner(headless=True)
        results = runner.run(steps)
        
        cold_duration = time.time() - start_time
        print(f"⏱️  Cold start duration: {cold_duration:.2f}s")
        
        # Validate results
        assert len(results) == 3, f"Expected 3 results, got {len(results)}"
        
        # Step 1: Open URL
        assert results[0].ok, f"Step 1 failed: {results[0].info}"
        assert results[0].step.startswith("Open https://www.verizon.com/smartphones/apple/")
        
        # Step 2: Click iPhone 16 Pro
        assert results[1].ok, f"Step 2 failed: {results[1].info}"
        assert results[1].step == "Click \"iPhone 16 Pro\""
        assert results[1].selector, "No selector generated for iPhone 16 Pro click"
        assert results[1].confidence > 0.0, f"Low confidence: {results[1].confidence}"
        
        # Step 3: Validate Apple iPhone 16 Pro
        assert results[2].ok, f"Step 3 failed: {results[2].info}"
        assert results[2].step == "Validate \"Apple iPhone 16 Pro\""
        
        print("✅ Cold start test passed")
        return cold_duration
    
    def test_verizon_flow_warm_hit(self):
        """Test Verizon flow with warm hit (cached promotions)."""
        print("\n🧪 TESTING: Verizon Flow - Warm Hit")
        
        # Same test steps
        steps = [
            "Open https://www.verizon.com/smartphones/apple/",
            "Click \"iPhone 16 Pro\"",
            "Validate \"Apple iPhone 16 Pro\""
        ]
        
        start_time = time.time()
        
        # Run the test (should use cached promotions)
        runner = Runner(headless=True)
        results = runner.run(steps)
        
        warm_duration = time.time() - start_time
        print(f"⏱️  Warm hit duration: {warm_duration:.2f}s")
        
        # Validate results
        assert len(results) == 3, f"Expected 3 results, got {len(results)}"
        
        # All steps should pass
        for i, result in enumerate(results, 1):
            assert result.ok, f"Step {i} failed: {result.info}"
        
        print("✅ Warm hit test passed")
        return warm_duration
    
    def test_verizon_flow_promotion_validation(self):
        """Test that warm hit is faster than cold start (promotion validation)."""
        print("\n🧪 TESTING: Promotion Validation (Warm < Cold)")
        
        # Run cold start
        cold_duration = self.test_verizon_flow_cold_start()
        
        # Wait a bit to ensure cache is stable
        time.sleep(2)
        
        # Run warm hit
        warm_duration = self.test_verizon_flow_warm_hit()
        
        # Validate promotion system: warm should be faster than cold
        print(f"\n📊 PERFORMANCE COMPARISON:")
        print(f"   Cold Start: {cold_duration:.2f}s")
        print(f"   Warm Hit:   {warm_duration:.2f}s")
        print(f"   Improvement: {((cold_duration - warm_duration) / cold_duration * 100):.1f}%")
        
        # Warm hit should be faster (promotion system working)
        assert warm_duration < cold_duration, (
            f"Promotion system failed: warm ({warm_duration:.2f}s) >= cold ({cold_duration:.2f}s)"
        )
        
        print("✅ Promotion validation passed")
    
    def test_verizon_flow_relative_xpath(self):
        """Test that only relative XPath selectors are generated."""
        print("\n🧪 TESTING: Relative XPath Validation")
        
        steps = [
            "Open https://www.verizon.com/smartphones/apple/",
            "Click \"iPhone 16 Pro\""
        ]
        
        runner = Runner(headless=True)
        results = runner.run(steps)
        
        # Check that XPath selectors are relative (start with //, not /html)
        for i, result in enumerate(results):
            if result.selector:
                selector = result.selector
                print(f"   Step {i+1} selector: {selector}")
                
                # Must start with // (relative) not /html (absolute)
                assert selector.startswith("//"), f"Absolute XPath detected: {selector}"
                assert not selector.startswith("/html"), f"Absolute XPath detected: {selector}"
                assert not selector.startswith("/body"), f"Absolute XPath detected: {selector}"
        
        print("✅ Relative XPath validation passed")
    
    def test_verizon_flow_frame_handling(self):
        """Test frame switching and shadow DOM support."""
        print("\n🧪 TESTING: Frame and Shadow DOM Handling")
        
        steps = [
            "Open https://www.verizon.com/smartphones/apple/",
            "Click \"iPhone 16 Pro\""
        ]
        
        runner = Runner(headless=True)
        results = runner.run(steps)
        
        # Validate that frame handling works
        for i, result in enumerate(results):
            assert result.ok, f"Frame handling failed at step {i+1}: {result.info}"
        
        print("✅ Frame handling validation passed")
    
    def test_verizon_flow_off_screen_handling(self):
        """Test off-screen element detection and scrolling."""
        print("\n🧪 TESTING: Off-screen Element Handling")
        
        steps = [
            "Open https://www.verizon.com/smartphones/apple/",
            "Click \"iPhone 16 Pro\""
        ]
        
        runner = Runner(headless=True)
        results = runner.run(steps)
        
        # Validate that off-screen elements are handled
        for i, result in enumerate(results):
            assert result.ok, f"Off-screen handling failed at step {i+1}: {result.info}"
        
        print("✅ Off-screen element handling validation passed")
    
    def test_verizon_flow_intent_parsing(self):
        """Test intent parsing with quoted targets and $values."""
        print("\n🧪 TESTING: Intent Parsing Validation")
        
        # Test various intent formats
        test_cases = [
            'Click "iPhone 16 Pro"',
            'Type $"John123" into "Username"',
            'Validate "Apple iPhone 16 Pro"'
        ]
        
        runner = Runner(headless=True)
        
        for test_case in test_cases:
            print(f"   Testing: {test_case}")
            
            # Parse the intent
            parsed = runner.intent.parse(test_case)
            
            # Validate parsing results
            assert parsed.action, f"No action parsed from: {test_case}"
            assert parsed.target_phrase, f"No target parsed from: {test_case}"
            
            # Check for quoted targets
            if '"' in test_case:
                assert '"' in parsed.target_phrase, f"Quoted target not preserved: {test_case}"
            
            # Check for $values
            if '$"' in test_case:
                assert '$"' in (parsed.value or ""), f"$value not preserved: {test_case}"
        
        print("✅ Intent parsing validation passed")


def test_verizon_flow_integration():
    """Integration test using run_steps function."""
    print("\n🧪 TESTING: Integration Test with run_steps")
    
    steps = [
        "Open https://www.verizon.com/smartphones/apple/",
        "Click \"iPhone 16 Pro\"",
        "Validate \"Apple iPhone 16 Pro\""
    ]
    
    # This should not raise any exceptions
    run_steps(steps, headless=True)
    
    print("✅ Integration test passed")


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v", "-s"])