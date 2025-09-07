"""Test caching functionality - SQLiteKV, promotions, and cache management."""

import pytest
import numpy as np
from pathlib import Path
import os
import sys
import tempfile
import shutil
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from her.vectordb.sqlite_cache import SQLiteKV
from her.promotion_adapter import compute_label_key, lookup_promotion, record_success, record_failure


class TestCache:
    """Test caching functionality."""
    
    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def sqlite_kv(self, temp_cache_dir):
        """Create SQLiteKV instance for testing."""
        cache_path = os.path.join(temp_cache_dir, "test_cache.db")
        return SQLiteKV(cache_path)
    
    def test_kv_operations(self, sqlite_kv):
        """Test basic key-value operations."""
        # Test put and get
        sqlite_kv.put("test_key", {"value": 42, "text": "hello"})
        result = sqlite_kv.get("test_key")
        
        assert result is not None, "Value should be stored"
        assert result["value"] == 42, "Value should be correct"
        assert result["text"] == "hello", "Text should be correct"
        
        # Test overwrite
        sqlite_kv.put("test_key", {"value": 100, "text": "world"})
        result = sqlite_kv.get("test_key")
        
        assert result["value"] == 100, "Value should be updated"
        assert result["text"] == "world", "Text should be updated"
        
        # Test non-existent key
        result = sqlite_kv.get("non_existent")
        assert result is None, "Non-existent key should return None"
    
    def test_embedding_operations(self, sqlite_kv):
        """Test embedding storage and retrieval."""
        # Test single embedding
        test_vector = [0.1, 0.2, 0.3, 0.4] * 192  # 768-d vector
        sqlite_kv.put_embedding("test_hash", test_vector, "test_model")
        
        retrieved = sqlite_kv.get_embedding("test_hash")
        assert retrieved is not None, "Embedding should be stored"
        assert len(retrieved) == 768, f"Expected 768-d, got {len(retrieved)}"
        assert retrieved == test_vector, "Retrieved vector should match stored"
        
        # Test batch operations
        test_vectors = {
            "hash1": [0.1] * 768,
            "hash2": [0.2] * 768,
            "hash3": [0.3] * 768,
        }
        
        sqlite_kv.batch_put_embeddings(test_vectors, "test_model")
        
        # Test batch retrieval
        retrieved_batch = sqlite_kv.batch_get_embeddings(["hash1", "hash2", "hash3", "hash4"])
        
        assert "hash1" in retrieved_batch, "hash1 should be retrieved"
        assert "hash2" in retrieved_batch, "hash2 should be retrieved"
        assert "hash3" in retrieved_batch, "hash3 should be retrieved"
        assert "hash4" not in retrieved_batch, "hash4 should not be retrieved"
        
        assert retrieved_batch["hash1"] == [0.1] * 768, "hash1 should match"
        assert retrieved_batch["hash2"] == [0.2] * 768, "hash2 should match"
        assert retrieved_batch["hash3"] == [0.3] * 768, "hash3 should match"
    
    def test_promotion_operations(self, sqlite_kv):
        """Test promotion tracking functionality."""
        page_sig = "test_page"
        frame_hash = "test_frame"
        label_key = "label:click|phones"
        selector = "//button[@data-testid='phones-btn']"
        
        # Test recording success
        record_success(sqlite_kv, page_sig, frame_hash, label_key, selector)
        
        # Test lookup
        result = lookup_promotion(sqlite_kv, page_sig, frame_hash, label_key)
        assert result == selector, f"Expected {selector}, got {result}"
        
        # Test recording failure
        record_failure(sqlite_kv, page_sig, frame_hash, label_key, selector)
        
        # Should still return the selector (most successful)
        result = lookup_promotion(sqlite_kv, page_sig, frame_hash, label_key)
        assert result == selector, f"Expected {selector}, got {result}"
        
        # Test with different selector
        selector2 = "//a[@href='/phones']"
        record_success(sqlite_kv, page_sig, frame_hash, label_key, selector2)
        record_success(sqlite_kv, page_sig, frame_hash, label_key, selector2)
        
        # Should now return selector2 (more successful)
        result = lookup_promotion(sqlite_kv, page_sig, frame_hash, label_key)
        assert result == selector2, f"Expected {selector2}, got {result}"
    
    def test_label_key_computation(self):
        """Test label key computation."""
        # Test basic computation
        tokens = ["click", "phones", "button"]
        key = compute_label_key(tokens)
        assert key == "label:button|click|phones", f"Expected 'label:button|click|phones', got {key}"
        
        # Test case insensitivity
        tokens = ["Click", "PHONES", "Button"]
        key = compute_label_key(tokens)
        assert key == "label:button|click|phones", f"Should be case insensitive, got {key}"
        
        # Test order independence
        tokens1 = ["click", "phones", "button"]
        tokens2 = ["button", "click", "phones"]
        key1 = compute_label_key(tokens1)
        key2 = compute_label_key(tokens2)
        assert key1 == key2, "Should be order independent"
        
        # Test empty tokens
        tokens = ["", "click", "  ", "phones"]
        key = compute_label_key(tokens)
        assert key == "label:click|phones", f"Should filter empty tokens, got {key}"
        
        # Test empty input
        tokens = []
        key = compute_label_key(tokens)
        assert key == "label:", f"Should handle empty input, got {key}"
    
    def test_cache_size_management(self, temp_cache_dir):
        """Test cache size management and cleanup."""
        # Create cache with small size limit
        cache_path = os.path.join(temp_cache_dir, "test_cache.db")
        kv = SQLiteKV(cache_path, max_size_mb=1)  # 1MB limit
        
        # Add some test data
        test_data = {}
        for i in range(100):
            key = f"test_key_{i}"
            # Create a vector that's about 3KB (768 * 4 bytes)
            vector = [float(i)] * 768
            test_data[key] = vector
            kv.put_embedding(key, vector, "test_model")
        
        # Verify data is stored
        for key in test_data:
            cached = kv.get_embedding(key)
            assert cached is not None, f"Embedding {key} should be cached"
        
        # Test vacuum functionality
        kv.vacuum_if_needed()
        
        # Data should still be there
        for key in test_data:
            cached = kv.get_embedding(key)
            assert cached is not None, f"Embedding {key} should still be cached after vacuum"
    
    def test_concurrent_access(self, temp_cache_dir):
        """Test concurrent access to cache."""
        import threading
        import time
        
        cache_path = os.path.join(temp_cache_dir, "test_cache.db")
        kv = SQLiteKV(cache_path)
        
        # Test data
        test_vectors = {}
        for i in range(50):
            test_vectors[f"key_{i}"] = [float(i)] * 768
        
        # Function to write data
        def write_data(start_idx, count):
            for i in range(start_idx, start_idx + count):
                key = f"key_{i}"
                vector = test_vectors[key]
                kv.put_embedding(key, vector, "test_model")
        
        # Function to read data
        def read_data(start_idx, count):
            for i in range(start_idx, start_idx + count):
                key = f"key_{i}"
                vector = kv.get_embedding(key)
                if vector is not None:
                    assert vector == test_vectors[key], f"Vector {key} should match"
        
        # Create threads
        threads = []
        
        # Writer threads
        for i in range(0, 50, 10):
            t = threading.Thread(target=write_data, args=(i, 10))
            threads.append(t)
        
        # Reader threads
        for i in range(0, 50, 10):
            t = threading.Thread(target=read_data, args=(i, 10))
            threads.append(t)
        
        # Start all threads
        for t in threads:
            t.start()
        
        # Wait for all threads to complete
        for t in threads:
            t.join()
        
        # Verify final state
        for key in test_vectors:
            cached = kv.get_embedding(key)
            assert cached is not None, f"Embedding {key} should be cached"
            assert cached == test_vectors[key], f"Vector {key} should match"
    
    def test_error_handling(self, sqlite_kv):
        """Test error handling in cache operations."""
        # Test invalid JSON in get
        # This is hard to test directly since we control the JSON encoding
        # But we can test edge cases
        
        # Test empty key
        result = sqlite_kv.get("")
        assert result is None, "Empty key should return None"
        
        # Test None key
        result = sqlite_kv.get(None)
        assert result is None, "None key should return None"
        
        # Test invalid embedding hash
        result = sqlite_kv.get_embedding("")
        assert result is None, "Empty hash should return None"
        
        result = sqlite_kv.get_embedding(None)
        assert result is None, "None hash should return None"
    
    def test_promotion_priority(self, sqlite_kv):
        """Test promotion priority based on success/failure counts."""
        page_sig = "test_page"
        frame_hash = "test_frame"
        label_key = "label:click|button"
        
        # Add multiple selectors with different success rates
        selector1 = "//button[@data-testid='btn1']"
        selector2 = "//button[@class='btn-primary']"
        selector3 = "//button[text()='Click']"
        
        # Selector1: 3 successes, 1 failure
        for _ in range(3):
            record_success(sqlite_kv, page_sig, frame_hash, label_key, selector1)
        record_failure(sqlite_kv, page_sig, frame_hash, label_key, selector1)
        
        # Selector2: 2 successes, 0 failures
        for _ in range(2):
            record_success(sqlite_kv, page_sig, frame_hash, label_key, selector2)
        
        # Selector3: 1 success, 2 failures
        record_success(sqlite_kv, page_sig, frame_hash, label_key, selector3)
        for _ in range(2):
            record_failure(sqlite_kv, page_sig, frame_hash, label_key, selector3)
        
        # Should return selector1 (highest success count)
        result = lookup_promotion(sqlite_kv, page_sig, frame_hash, label_key)
        assert result == selector1, f"Expected {selector1}, got {result}"
        
        # Add more successes to selector2
        for _ in range(2):
            record_success(sqlite_kv, page_sig, frame_hash, label_key, selector2)
        
        # Should now return selector2 (4 successes vs 3)
        result = lookup_promotion(sqlite_kv, page_sig, frame_hash, label_key)
        assert result == selector2, f"Expected {selector2}, got {result}"