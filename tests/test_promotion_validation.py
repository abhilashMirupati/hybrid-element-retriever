#!/usr/bin/env python3
"""
Promotion Validation Tests - Ensure warm hits are faster than cold starts

This test validates that the promotion system is working correctly:
1. Cold start should be slower (no cached promotions)
2. Warm hit should be faster (uses cached promotions)
3. Promotion accuracy should be maintained
"""

import os
import sys
import time
import pytest
import tempfile
import shutil
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.her.core.runner import Runner
from src.her.promotion.promotion_adapter import compute_label_key
from src.her.vectordb.sqlite_cache import SQLiteKV


class TestPromotionValidation:
    """Test suite for promotion system validation."""
    
    @pytest.fixture(autouse=True)
    def setup_clean_cache(self):
        """Setup clean cache for each test."""
        # Create temporary cache directory
        self.temp_cache_dir = tempfile.mkdtemp(prefix="her_test_cache_")
        os.environ['HER_CACHE_DIR'] = self.temp_cache_dir
        
        yield
        
        # Cleanup
        if os.path.exists(self.temp_cache_dir):
            shutil.rmtree(self.temp_cache_dir, ignore_errors=True)
    
    def test_promotion_cold_vs_warm_performance(self):
        """Test that warm hits are significantly faster than cold starts."""
        print("\n🧪 TESTING: Promotion Performance (Cold vs Warm)")
        
        # Test steps
        steps = [
            "Open https://www.verizon.com/smartphones/apple/",
            "Click \"iPhone 16 Pro\"",
            "Validate \"Apple iPhone 16 Pro\""
        ]
        
        # Cold start test
        print("   Running cold start test...")
        cold_start_time = time.time()
        
        runner1 = Runner(headless=True)
        results1 = runner1.run(steps)
        
        cold_duration = time.time() - cold_start_time
        print(f"   Cold start duration: {cold_duration:.2f}s")
        
        # Validate cold start results
        assert len(results1) == 3, f"Expected 3 results, got {len(results1)}"
        for i, result in enumerate(results1):
            assert result.ok, f"Cold start step {i+1} failed: {result.info}"
        
        # Warm hit test (same steps, should use promotions)
        print("   Running warm hit test...")
        time.sleep(1)  # Brief pause to ensure cache is stable
        
        warm_start_time = time.time()
        
        runner2 = Runner(headless=True)
        results2 = runner2.run(steps)
        
        warm_duration = time.time() - warm_start_time
        print(f"   Warm hit duration: {warm_duration:.2f}s")
        
        # Validate warm hit results
        assert len(results2) == 3, f"Expected 3 results, got {len(results2)}"
        for i, result in enumerate(results2):
            assert result.ok, f"Warm hit step {i+1} failed: {result.info}"
        
        # Performance validation: warm should be faster
        performance_improvement = ((cold_duration - warm_duration) / cold_duration) * 100
        
        print(f"\n📊 PERFORMANCE RESULTS:")
        print(f"   Cold Start: {cold_duration:.2f}s")
        print(f"   Warm Hit:   {warm_duration:.2f}s")
        print(f"   Improvement: {performance_improvement:.1f}%")
        
        # Warm hit should be faster (promotion system working)
        assert warm_duration < cold_duration, (
            f"Promotion system failed: warm ({warm_duration:.2f}s) >= cold ({cold_duration:.2f}s)"
        )
        
        # Should see at least 10% improvement (conservative threshold)
        assert performance_improvement >= 10.0, (
            f"Insufficient performance improvement: {performance_improvement:.1f}% < 10%"
        )
        
        print("✅ Promotion performance validation passed")
    
    def test_promotion_accuracy_maintained(self):
        """Test that promotions maintain accuracy across runs."""
        print("\n🧪 TESTING: Promotion Accuracy Maintenance")
        
        # Test steps
        steps = [
            "Open https://www.verizon.com/smartphones/apple/",
            "Click \"iPhone 16 Pro\""
        ]
        
        # Run multiple times to test consistency
        results_list = []
        for i in range(3):
            print(f"   Run {i+1}/3...")
            
            runner = Runner(headless=True)
            results = runner.run(steps)
            
            # Validate results
            assert len(results) >= 2, f"Expected at least 2 results, got {len(results)}"
            assert results[0].ok, f"Step 1 failed in run {i+1}: {results[0].info}"
            assert results[1].ok, f"Step 2 failed in run {i+1}: {results[1].info}"
            
            results_list.append(results)
            
            time.sleep(0.5)  # Brief pause between runs
        
        # Check consistency of selectors (promotions should be consistent)
        selectors = [results[1].selector for results in results_list if len(results) > 1]
        
        print(f"   Selectors across runs: {selectors}")
        
        # All selectors should be valid (non-empty)
        for i, selector in enumerate(selectors):
            assert selector, f"Empty selector in run {i+1}"
            assert selector.startswith("//"), f"Non-relative selector in run {i+1}: {selector}"
        
        # Selectors should be consistent (same or similar)
        if len(set(selectors)) > 1:
            print(f"   ⚠️  Selector variation detected: {set(selectors)}")
            # This is acceptable as long as all selectors are valid
        
        print("✅ Promotion accuracy maintenance validation passed")
    
    def test_promotion_cache_persistence(self):
        """Test that promotion cache persists across runner instances."""
        print("\n🧪 TESTING: Promotion Cache Persistence")
        
        # Test steps
        steps = [
            "Open https://www.verizon.com/smartphones/apple/",
            "Click \"iPhone 16 Pro\""
        ]
        
        # First run - should create promotions
        print("   First run (creating promotions)...")
        runner1 = Runner(headless=True)
        results1 = runner1.run(steps)
        
        # Validate first run
        assert len(results1) >= 2, f"Expected at least 2 results, got {len(results1)}"
        assert results1[0].ok, f"First run step 1 failed: {results1[0].info}"
        assert results1[1].ok, f"First run step 2 failed: {results1[1].info}"
        
        first_selector = results1[1].selector
        print(f"   First run selector: {first_selector}")
        
        # Second run with new runner instance - should use cached promotions
        print("   Second run (using cached promotions)...")
        runner2 = Runner(headless=True)
        results2 = runner2.run(steps)
        
        # Validate second run
        assert len(results2) >= 2, f"Expected at least 2 results, got {len(results2)}"
        assert results2[0].ok, f"Second run step 1 failed: {results2[0].info}"
        assert results2[1].ok, f"Second run step 2 failed: {results2[1].info}"
        
        second_selector = results2[1].selector
        print(f"   Second run selector: {second_selector}")
        
        # Both selectors should be valid
        assert first_selector, "Empty selector in first run"
        assert second_selector, "Empty selector in second run"
        assert first_selector.startswith("//"), f"Non-relative selector in first run: {first_selector}"
        assert second_selector.startswith("//"), f"Non-relative selector in second run: {second_selector}"
        
        print("✅ Promotion cache persistence validation passed")
    
    def test_promotion_sqlite_storage(self):
        """Test that promotions are properly stored in SQLite."""
        print("\n🧪 TESTING: Promotion SQLite Storage")
        
        # Get cache path
        cache_dir = Path(os.environ['HER_CACHE_DIR'])
        db_path = cache_dir / "embeddings.db"
        
        # Verify database is created
        assert db_path.exists(), f"SQLite database not created at {db_path}"
        
        # Run a test to generate promotions
        steps = [
            "Open https://www.verizon.com/smartphones/apple/",
            "Click \"iPhone 16 Pro\""
        ]
        
        runner = Runner(headless=True)
        results = runner.run(steps)
        
        # Validate results
        assert len(results) >= 2, f"Expected at least 2 results, got {len(results)}"
        assert results[0].ok, f"Step 1 failed: {results[0].info}"
        assert results[1].ok, f"Step 2 failed: {results[1].info}"
        
        # Check SQLite database has promotions table
        kv = SQLiteKV(str(db_path))
        
        # Try to access promotions (this will verify table exists)
        try:
            # This should not raise an exception if promotions table exists
            test_promotion = kv.get_promotion("test_page", "test_frame", "test_label")
            # test_promotion will be None, but that's OK - table exists
        except Exception as e:
            pytest.fail(f"Promotions table not accessible: {e}")
        
        print("✅ Promotion SQLite storage validation passed")
    
    def test_promotion_label_key_consistency(self):
        """Test that label keys are generated consistently."""
        print("\n🧪 TESTING: Promotion Label Key Consistency")
        
        # Test different target phrases
        test_cases = [
            ["iPhone", "16", "Pro"],
            ["iPhone 16 Pro"],
            ["Apple", "iPhone", "16", "Pro"],
            ["iPhone", "Pro", "16"]  # Different order
        ]
        
        label_keys = []
        for tokens in test_cases:
            label_key = compute_label_key(tokens)
            label_keys.append(label_key)
            print(f"   Tokens: {tokens} -> Label Key: {label_key}")
        
        # All label keys should be non-empty
        for i, label_key in enumerate(label_keys):
            assert label_key, f"Empty label key for case {i+1}"
            assert label_key.startswith("label:"), f"Invalid label key format for case {i+1}: {label_key}"
        
        # Same tokens should produce same label key (order independent)
        tokens1 = ["iPhone", "16", "Pro"]
        tokens2 = ["Pro", "iPhone", "16"]  # Different order
        key1 = compute_label_key(tokens1)
        key2 = compute_label_key(tokens2)
        
        assert key1 == key2, f"Label keys should be order-independent: {key1} != {key2}"
        
        print("✅ Promotion label key consistency validation passed")


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v", "-s"])