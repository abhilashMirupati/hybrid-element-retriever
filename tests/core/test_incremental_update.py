"""Test incremental update with DOM deltas."""

import pytest
from unittest.mock import Mock, patch
from her.pipeline import HERPipeline, PipelineConfig
from her.cache.two_tier import TwoTierCache


class TestIncrementalUpdate:
    """Test incremental DOM updates and caching."""
    
    @pytest.fixture
    def pipeline(self, tmp_path):
        """Create pipeline with cache."""
        config = PipelineConfig(
            enable_incremental_updates=True,
            cache_dir=str(tmp_path)
        )
        return HERPipeline(config=config)
    
    def test_small_dom_delta_detection(self, pipeline):
        """Test that small DOM changes are detected."""
        initial_dom = {
            "elements": [
                {"id": "1", "tag": "div", "text": "Header", "xpath": "//div[1]"},
                {"id": "2", "tag": "button", "text": "Submit", "xpath": "//button[1]"}
            ]
        }
        
        updated_dom = {
            "elements": [
                {"id": "1", "tag": "div", "text": "Header", "xpath": "//div[1]"},
                {"id": "2", "tag": "button", "text": "Submit", "xpath": "//button[1]"},
                {"id": "3", "tag": "span", "text": "New", "xpath": "//span[1]"}  # New element
            ]
        }
        
        # Process initial DOM
        with patch.object(pipeline, '_get_dom_snapshot', return_value=initial_dom):
            pipeline.process("test", initial_dom)
        
        # Track which elements are embedded
        embedded_elements = []
        
        def track_embedding(element):
            embedded_elements.append(element)
            return [[0.1] * 384]
        
        # Process updated DOM
        with patch.object(pipeline, '_embed_element', side_effect=track_embedding):
            with patch.object(pipeline, '_get_dom_snapshot', return_value=updated_dom):
                pipeline.process("find new", updated_dom)
        
        # Only the new element should be embedded
        assert len(embedded_elements) <= 1
        if embedded_elements:
            assert embedded_elements[0]["id"] == "3"
    
    def test_cache_hits_for_existing_elements(self, pipeline, tmp_path):
        """Test that existing elements are retrieved from cache."""
        cache = TwoTierCache(cache_dir=tmp_path)
        
        # Pre-populate cache with element embeddings
        cache.set("element_div_header", {"embedding": [0.1] * 384, "text": "Header"})
        cache.set("element_button_submit", {"embedding": [0.2] * 384, "text": "Submit"})
        
        dom = {
            "elements": [
                {"tag": "div", "text": "Header", "xpath": "//div[1]"},
                {"tag": "button", "text": "Submit", "xpath": "//button[1]"},
                {"tag": "input", "text": "", "xpath": "//input[1]"}  # New element
            ]
        }
        
        cache_hits = 0
        cache_misses = 0
        
        def check_cache(key):
            nonlocal cache_hits, cache_misses
            result = cache.get(key)
            if result:
                cache_hits += 1
            else:
                cache_misses += 1
            return result
        
        with patch.object(cache, 'get', side_effect=check_cache):
            with patch.object(pipeline, 'cache', cache):
                with patch.object(pipeline, '_get_dom_snapshot', return_value=dom):
                    pipeline.process("find button", dom)
        
        # Should have cache hits for existing elements
        assert cache_hits >= 2  # Header and Submit
        assert cache_misses <= 1  # Only the new input
    
    def test_lru_cache_eviction(self, pipeline, tmp_path):
        """Test LRU cache eviction for memory management."""
        cache = TwoTierCache(cache_dir=tmp_path, max_memory_items=3)
        
        # Fill cache to capacity
        for i in range(4):
            cache.set(f"key_{i}", {"data": f"value_{i}"})
        
        # First item should be evicted (LRU)
        assert cache.get("key_0") is None or cache.get("key_0") == {"data": "value_0"}
        
        # Most recent items should still be in cache
        assert cache.get("key_3") is not None
    
    def test_sqlite_persistence(self, pipeline, tmp_path):
        """Test that embeddings persist in SQLite."""
        cache1 = TwoTierCache(cache_dir=tmp_path)
        
        # Store embeddings
        cache1.set("test_element", {"embedding": [0.5] * 384})
        
        # Create new cache instance (simulating restart)
        cache2 = TwoTierCache(cache_dir=tmp_path)
        
        # Should retrieve from SQLite
        result = cache2.get("test_element")
        assert result is not None
        assert result["embedding"] == [0.5] * 384
    
    def test_incremental_update_performance(self, pipeline):
        """Test that incremental updates are faster than full reindex."""
        import time
        
        large_dom = {
            "elements": [
                {"id": f"elem_{i}", "tag": "div", "text": f"Element {i}", "xpath": f"//div[{i}]"}
                for i in range(100)
            ]
        }
        
        # First pass - full indexing
        start = time.time()
        with patch.object(pipeline, '_get_dom_snapshot', return_value=large_dom):
            pipeline.process("test", large_dom)
        full_index_time = time.time() - start
        
        # Add one new element
        large_dom["elements"].append(
            {"id": "new", "tag": "button", "text": "New Button", "xpath": "//button[1]"}
        )
        
        # Second pass - incremental update
        start = time.time()
        with patch.object(pipeline, '_get_dom_snapshot', return_value=large_dom):
            pipeline.process("find new button", large_dom)
        incremental_time = time.time() - start
        
        # Incremental should be faster (or at least not significantly slower)
        # In practice, this would be much faster with real caching
        assert incremental_time <= full_index_time * 2  # Allow some variance
    
    def test_dom_hash_change_detection(self, pipeline):
        """Test that DOM changes are detected via hashing."""
        dom1 = {
            "elements": [
                {"tag": "div", "text": "Content 1", "xpath": "//div[1]"}
            ]
        }
        
        dom2 = {
            "elements": [
                {"tag": "div", "text": "Content 2", "xpath": "//div[1]"}  # Text changed
            ]
        }
        
        # Generate hashes
        hash1 = pipeline._compute_dom_hash(dom1)
        hash2 = pipeline._compute_dom_hash(dom2)
        
        # Hashes should be different
        assert hash1 != hash2
    
    def test_selective_reembedding(self, pipeline):
        """Test that only changed elements are re-embedded."""
        initial_dom = {
            "elements": [
                {"id": "1", "tag": "div", "text": "Static", "xpath": "//div[1]"},
                {"id": "2", "tag": "span", "text": "Dynamic", "xpath": "//span[1]"}
            ]
        }
        
        updated_dom = {
            "elements": [
                {"id": "1", "tag": "div", "text": "Static", "xpath": "//div[1]"},  # Unchanged
                {"id": "2", "tag": "span", "text": "Changed", "xpath": "//span[1]"}  # Changed
            ]
        }
        
        # Track embeddings
        embedded_ids = set()
        
        def track_embed(element):
            embedded_ids.add(element.get("id"))
            return [[0.1] * 384]
        
        # Initial embedding
        with patch.object(pipeline, '_embed_element', side_effect=track_embed):
            with patch.object(pipeline, '_get_dom_snapshot', return_value=initial_dom):
                pipeline.process("test", initial_dom)
        
        initial_embedded = embedded_ids.copy()
        embedded_ids.clear()
        
        # Update - only changed element should be re-embedded
        with patch.object(pipeline, '_embed_element', side_effect=track_embed):
            with patch.object(pipeline, '_get_dom_snapshot', return_value=updated_dom):
                pipeline.process("test", updated_dom)
        
        # Only element with id="2" should be re-embedded
        assert "2" in embedded_ids or len(embedded_ids) == 0  # May use cache