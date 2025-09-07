"""Test delta embedding functionality - caching and incremental updates."""

import pytest
import numpy as np
from pathlib import Path
import os
import sys
import tempfile
import shutil

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from her.pipeline import HybridPipeline
from her.vectordb.sqlite_cache import SQLiteKV
from her.hashing import element_dom_hash


class TestDeltaEmbedding:
    """Test delta embedding and caching functionality."""
    
    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def sample_elements(self):
        """Sample elements for testing."""
        return [
            {
                "text": "click on phones",
                "tag": "button",
                "attributes": {"class": "btn-primary", "data-testid": "phones-btn"},
                "xpath": "//button[@data-testid='phones-btn']",
                "visible": True,
                "meta": {"frame_hash": "test_frame_1"}
            },
            {
                "text": "select apple filter",
                "tag": "a",
                "attributes": {"href": "/filter/apple", "class": "filter-link"},
                "xpath": "//a[@href='/filter/apple']",
                "visible": True,
                "meta": {"frame_hash": "test_frame_1"}
            },
            {
                "text": "open menu",
                "tag": "div",
                "attributes": {"role": "button", "onclick": "toggleMenu()"},
                "xpath": "//div[@role='button']",
                "visible": True,
                "meta": {"frame_hash": "test_frame_2"}
            }
        ]
    
    def test_embedding_caching(self, temp_cache_dir, sample_elements):
        """Test that embeddings are cached and reused."""
        # Skip if models not available
        model_path = Path("src/her/models/e5-small-onnx")
        markup_path = Path("src/her/models/markuplm-base")
        if not model_path.exists() or not markup_path.exists():
            pytest.skip("Models not found - run install_models.sh first")
        
        # Create pipeline with temp cache
        pipeline = HybridPipeline(models_root=Path("src/her/models"))
        pipeline._db_path = os.path.join(temp_cache_dir, "test_embeddings.db")
        pipeline.kv = SQLiteKV(pipeline._db_path)
        
        # First embedding - should compute and cache
        elements1 = sample_elements[:2]
        E1, meta1 = pipeline._prepare_elements(elements1)
        
        assert E1.shape[0] == 2, f"Expected 2 elements, got {E1.shape[0]}"
        assert len(meta1) == 2, f"Expected 2 metadata entries, got {len(meta1)}"
        
        # Check that embeddings were cached
        for el in elements1:
            h = element_dom_hash(el)
            cached = pipeline.kv.get_embedding(h)
            assert cached is not None, f"Embedding for {h} should be cached"
            assert len(cached) == 768, f"Cached embedding should be 768-d, got {len(cached)}"
        
        # Second embedding with same elements - should use cache
        elements2 = sample_elements[:2]  # Same elements
        E2, meta2 = pipeline._prepare_elements(elements2)
        
        assert E2.shape[0] == 2, f"Expected 2 elements, got {E2.shape[0]}"
        assert len(meta2) == 2, f"Expected 2 metadata entries, got {len(meta2)}"
        
        # Should be identical (cached)
        assert np.allclose(E1, E2), "Cached embeddings should be identical"
    
    def test_incremental_embedding(self, temp_cache_dir, sample_elements):
        """Test incremental embedding with new elements."""
        # Skip if models not available
        model_path = Path("src/her/models/e5-small-onnx")
        markup_path = Path("src/her/models/markuplm-base")
        if not model_path.exists() or not markup_path.exists():
            pytest.skip("Models not found - run install_models.sh first")
        
        # Create pipeline with temp cache
        pipeline = HybridPipeline(models_root=Path("src/her/models"))
        pipeline._db_path = os.path.join(temp_cache_dir, "test_embeddings.db")
        pipeline.kv = SQLiteKV(pipeline._db_path)
        
        # First batch
        elements1 = sample_elements[:2]
        E1, meta1 = pipeline._prepare_elements(elements1)
        
        # Second batch with new element
        elements2 = sample_elements  # All 3 elements
        E2, meta2 = pipeline._prepare_elements(elements2)
        
        assert E2.shape[0] == 3, f"Expected 3 elements, got {E2.shape[0]}"
        assert len(meta2) == 3, f"Expected 3 metadata entries, got {len(meta2)}"
        
        # First two should be identical (cached)
        assert np.allclose(E1, E2[:2]), "First two elements should be identical (cached)"
        
        # Third element should be new
        assert not np.allclose(E1, E2[2:3]), "Third element should be different (new)"
    
    def test_cache_hit_rates(self, temp_cache_dir, sample_elements):
        """Test cache hit rates for different scenarios."""
        # Skip if models not available
        model_path = Path("src/her/models/e5-small-onnx")
        markup_path = Path("src/her/models/markuplm-base")
        if not model_path.exists() or not markup_path.exists():
            pytest.skip("Models not found - run install_models.sh first")
        
        # Create pipeline with temp cache
        pipeline = HybridPipeline(models_root=Path("src/her/models"))
        pipeline._db_path = os.path.join(temp_cache_dir, "test_embeddings.db")
        pipeline.kv = SQLiteKV(pipeline._db_path)
        
        # First run - all cache misses
        E1, meta1 = pipeline._prepare_elements(sample_elements)
        
        # Second run with same elements - all cache hits
        E2, meta2 = pipeline._prepare_elements(sample_elements)
        
        # Should be identical (all cached)
        assert np.allclose(E1, E2), "All embeddings should be cached and identical"
        
        # Third run with partial overlap - some cache hits
        partial_elements = sample_elements[:2] + [{
            "text": "new element",
            "tag": "span",
            "attributes": {"class": "new"},
            "xpath": "//span[@class='new']",
            "visible": True,
            "meta": {"frame_hash": "test_frame_3"}
        }]
        
        E3, meta3 = pipeline._prepare_elements(partial_elements)
        
        assert E3.shape[0] == 3, f"Expected 3 elements, got {E3.shape[0]}"
        
        # First two should be identical (cached)
        assert np.allclose(E1[:2], E3[:2]), "First two elements should be cached"
        
        # Third should be different (new)
        assert not np.allclose(E1, E3[2:3]), "Third element should be new"
    
    def test_embedding_consistency(self, temp_cache_dir, sample_elements):
        """Test that embeddings are consistent across runs."""
        # Skip if models not available
        model_path = Path("src/her/models/e5-small-onnx")
        markup_path = Path("src/her/models/markuplm-base")
        if not model_path.exists() or not markup_path.exists():
            pytest.skip("Models not found - run install_models.sh first")
        
        # Create two separate pipelines with same cache
        cache_path = os.path.join(temp_cache_dir, "test_embeddings.db")
        
        pipeline1 = HybridPipeline(models_root=Path("src/her/models"))
        pipeline1._db_path = cache_path
        pipeline1.kv = SQLiteKV(cache_path)
        
        pipeline2 = HybridPipeline(models_root=Path("src/her/models"))
        pipeline2._db_path = cache_path
        pipeline2.kv = SQLiteKV(cache_path)
        
        # First pipeline processes elements
        E1, meta1 = pipeline1._prepare_elements(sample_elements)
        
        # Second pipeline should get same results (from cache)
        E2, meta2 = pipeline2._prepare_elements(sample_elements)
        
        # Should be identical
        assert np.allclose(E1, E2), "Embeddings should be consistent across pipelines"
        assert len(meta1) == len(meta2), "Metadata should be consistent"
        
        # Check that all elements are cached
        for el in sample_elements:
            h = element_dom_hash(el)
            cached = pipeline2.kv.get_embedding(h)
            assert cached is not None, f"Embedding for {h} should be cached"
    
    def test_cache_cleanup(self, temp_cache_dir):
        """Test cache cleanup and size management."""
        # Create SQLiteKV with small size limit
        cache_path = os.path.join(temp_cache_dir, "test_embeddings.db")
        kv = SQLiteKV(cache_path, max_size_mb=1)  # 1MB limit
        
        # Add some test data
        test_data = {
            "test1": [0.1] * 768,
            "test2": [0.2] * 768,
            "test3": [0.3] * 768,
        }
        
        for key, vec in test_data.items():
            kv.put_embedding(key, vec, "test_model")
        
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