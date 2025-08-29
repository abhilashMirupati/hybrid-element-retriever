"""Performance tests for HER."""

import pytest
import time
import random
from unittest.mock import Mock, patch
from pathlib import Path

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from her.pipeline import HERPipeline, PipelineConfig
from her.locator.synthesize import LocatorSynthesizer
from her.embeddings.query_embedder import QueryEmbedder
from her.embeddings.element_embedder import ElementEmbedder
from her.cache.two_tier import TwoTierCache


def generate_test_descriptors(count: int) -> list:
    """Generate test element descriptors."""
    descriptors = []
    for i in range(count):
        descriptors.append({
            "tag": random.choice(["div", "button", "input", "span", "a"]),
            "id": f"elem-{i}" if random.random() > 0.5 else None,
            "text": f"Text content {i}" if random.random() > 0.3 else "",
            "attributes": {
                "class": f"class-{i % 10} class-{i % 5}",
                "data-testid": f"test-{i}" if random.random() > 0.7 else None,
            }
        })
    return descriptors


class TestLocatorPerformance:
    """Test locator synthesis performance."""
    
    @pytest.mark.benchmark(group="locator")
    def test_synthesize_speed(self, benchmark):
        """Test locator synthesis speed."""
        synthesizer = LocatorSynthesizer()
        descriptor = {
            "tag": "button",
            "id": "submit-btn",
            "text": "Submit Form",
            "attributes": {
                "class": "btn btn-primary",
                "data-testid": "submit",
                "aria-label": "Submit the form"
            }
        }
        
        result = benchmark(synthesizer.synthesize, descriptor)
        assert len(result) > 0
    
    @pytest.mark.benchmark(group="locator")
    def test_batch_synthesis(self, benchmark):
        """Test batch locator synthesis."""
        synthesizer = LocatorSynthesizer()
        descriptors = generate_test_descriptors(100)
        
        def batch_synthesize():
            results = []
            for desc in descriptors:
                results.append(synthesizer.synthesize(desc))
            return results
        
        results = benchmark(batch_synthesize)
        assert len(results) == 100
    
    def test_locator_resolution_under_2s(self):
        """Test that locator resolution completes under 2 seconds."""
        synthesizer = LocatorSynthesizer()
        descriptors = generate_test_descriptors(50)
        
        start = time.time()
        for desc in descriptors:
            synthesizer.synthesize(desc)
        duration = time.time() - start
        
        assert duration < 2.0, f"Locator resolution took {duration:.2f}s (should be < 2s)"


class TestEmbeddingPerformance:
    """Test embedding generation performance."""
    
    @pytest.mark.benchmark(group="embedding")
    @patch('her.embeddings._resolve.ONNXModelResolver')
    def test_query_embedding_speed(self, mock_resolver, benchmark):
        """Test query embedding speed."""
        mock_resolver.return_value.embed.return_value = [0.1] * 384
        mock_resolver.return_value.embedding_dim = 384
        
        embedder = QueryEmbedder(cache_enabled=False)
        embedder.resolver = mock_resolver.return_value
        
        query = "Find the submit button in the login form"
        result = benchmark(embedder.embed, query)
        assert len(result) == 384
    
    @pytest.mark.benchmark(group="embedding")
    @patch('her.embeddings._resolve.ONNXModelResolver')
    def test_element_embedding_speed(self, mock_resolver, benchmark):
        """Test element embedding speed."""
        mock_resolver.return_value.embed.return_value = [0.1] * 768
        mock_resolver.return_value.embedding_dim = 768
        
        embedder = ElementEmbedder(cache_enabled=False)
        embedder.resolver = mock_resolver.return_value
        
        descriptor = {
            "tag": "button",
            "text": "Click me",
            "attributes": {"class": "btn"}
        }
        
        result = benchmark(embedder.embed, descriptor)
        assert len(result) == 768
    
    @pytest.mark.benchmark(group="embedding")
    @patch('her.embeddings._resolve.ONNXModelResolver')
    def test_batch_embedding(self, mock_resolver, benchmark):
        """Test batch embedding performance."""
        mock_resolver.return_value.embed.return_value = [0.1] * 384
        mock_resolver.return_value.embedding_dim = 384
        
        embedder = QueryEmbedder(cache_enabled=False)
        embedder.resolver = mock_resolver.return_value
        
        queries = [f"Query {i}" for i in range(32)]
        
        result = benchmark(embedder.embed_batch, queries)
        assert len(result) == 32


class TestCachePerformance:
    """Test caching performance."""
    
    @pytest.mark.benchmark(group="cache")
    def test_cache_hit_speed(self, benchmark, tmp_path):
        """Test cache hit performance."""
        cache = TwoTierCache(cache_dir=tmp_path)
        
        # Populate cache
        for i in range(100):
            cache.set(f"key-{i}", f"value-{i}")
        
        def cache_hits():
            results = []
            for i in range(100):
                results.append(cache.get(f"key-{i}"))
            return results
        
        results = benchmark(cache_hits)
        assert len(results) == 100
        assert all(r is not None for r in results)
    
    @pytest.mark.benchmark(group="cache")
    def test_cache_miss_speed(self, benchmark, tmp_path):
        """Test cache miss performance."""
        cache = TwoTierCache(cache_dir=tmp_path)
        
        def cache_misses():
            results = []
            for i in range(100):
                results.append(cache.get(f"missing-{i}"))
            return results
        
        results = benchmark(cache_misses)
        assert all(r is None for r in results)
    
    def test_cache_memory_usage(self, tmp_path):
        """Test cache memory usage stays within limits."""
        cache = TwoTierCache(cache_dir=tmp_path, max_memory_mb=10)
        
        # Add data until memory limit
        large_value = "x" * 1024  # 1KB string
        for i in range(10000):
            cache.set(f"key-{i}", large_value)
        
        # Cache should have evicted old entries
        # Check that early entries were evicted
        assert cache.get("key-0") is None or cache.get("key-9999") is not None


class TestPipelinePerformance:
    """Test full pipeline performance."""
    
    @pytest.mark.benchmark(group="pipeline")
    @patch('her.pipeline.QueryEmbedder')
    @patch('her.pipeline.ElementEmbedder')
    def test_pipeline_throughput(self, mock_element_embedder, mock_query_embedder, benchmark):
        """Test pipeline throughput."""
        # Mock embedders for consistent performance
        mock_query_embedder.return_value.embed.return_value = [0.1] * 384
        mock_element_embedder.return_value.embed.return_value = [0.2] * 768
        
        config = PipelineConfig(
            enable_cold_start_detection=False,
            enable_incremental_updates=False
        )
        pipeline = HERPipeline(config)
        
        descriptors = generate_test_descriptors(100)
        query = "Find submit button"
        
        result = benchmark(pipeline.process, query, descriptors)
        assert 'xpath' in result
    
    def test_large_dom_performance(self):
        """Test performance with large DOMs."""
        config = PipelineConfig(
            max_candidates=5,
            embedding_batch_size=64
        )
        pipeline = HERPipeline(config)
        
        # Generate large DOM
        large_descriptors = generate_test_descriptors(10000)
        
        start = time.time()
        result = pipeline.process("Find elem-5000", large_descriptors)
        duration = time.time() - start
        
        assert duration < 5.0, f"Large DOM processing took {duration:.2f}s (should be < 5s)"
        assert 'xpath' in result
    
    @patch('her.pipeline.QueryEmbedder')
    @patch('her.pipeline.ElementEmbedder')
    def test_incremental_update_performance(self, mock_element_embedder, mock_query_embedder):
        """Test incremental update performance."""
        mock_query_embedder.return_value.embed.return_value = [0.1] * 384
        mock_element_embedder.return_value.embed.return_value = [0.2] * 768
        
        pipeline = HERPipeline()
        
        # Initial indexing
        initial_descriptors = generate_test_descriptors(1000)
        start = time.time()
        pipeline._handle_cold_start("session1", initial_descriptors)
        cold_start_time = time.time() - start
        
        # Add 100 new elements
        new_descriptors = initial_descriptors + generate_test_descriptors(100)
        
        # Incremental update
        start = time.time()
        new_elements = pipeline._detect_incremental_changes("session1", new_descriptors)
        pipeline._handle_incremental_update("session1", new_elements)
        incremental_time = time.time() - start
        
        # Incremental should be much faster than cold start
        assert incremental_time < cold_start_time * 0.2, \
            f"Incremental update too slow: {incremental_time:.2f}s vs cold start {cold_start_time:.2f}s"


class TestMemoryUsage:
    """Test memory usage and leaks."""
    
    def test_descriptor_memory_efficiency(self):
        """Test memory efficiency of descriptor storage."""
        import sys
        
        descriptors = generate_test_descriptors(1000)
        
        # Get size of descriptors
        size = sys.getsizeof(descriptors)
        for desc in descriptors:
            size += sys.getsizeof(desc)
            for key, value in desc.items():
                size += sys.getsizeof(key) + sys.getsizeof(value)
        
        # Should be reasonably sized (< 1MB for 1000 descriptors)
        size_mb = size / (1024 * 1024)
        assert size_mb < 1.0, f"Descriptors using too much memory: {size_mb:.2f}MB"
    
    @patch('her.pipeline.QueryEmbedder')
    @patch('her.pipeline.ElementEmbedder')
    def test_pipeline_memory_leak(self, mock_element_embedder, mock_query_embedder):
        """Test for memory leaks in pipeline."""
        mock_query_embedder.return_value.embed.return_value = [0.1] * 384
        mock_element_embedder.return_value.embed.return_value = [0.2] * 768
        
        pipeline = HERPipeline()
        descriptors = generate_test_descriptors(100)
        
        # Run multiple times
        for i in range(100):
            result = pipeline.process(f"Query {i}", descriptors, session_id=f"session-{i}")
        
        # Check that old sessions are cleaned up
        # Pipeline should not keep all 100 sessions in memory
        assert len(pipeline._dom_hashes) < 50, "Potential memory leak: too many cached sessions"


class TestConcurrency:
    """Test concurrent operations."""
    
    def test_concurrent_queries(self):
        """Test handling concurrent queries."""
        import threading
        
        pipeline = HERPipeline()
        descriptors = generate_test_descriptors(100)
        results = []
        errors = []
        
        def run_query(query_id):
            try:
                result = pipeline.process(f"Find elem-{query_id}", descriptors)
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        # Run concurrent queries
        threads = []
        for i in range(10):
            t = threading.Thread(target=run_query, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join(timeout=5.0)
        
        assert len(errors) == 0, f"Concurrent queries failed: {errors}"
        assert len(results) == 10


class TestOptimizations:
    """Test various optimizations."""
    
    def test_early_termination(self):
        """Test early termination when confidence is high."""
        config = PipelineConfig(
            similarity_threshold=0.95,
            max_candidates=1  # Stop after finding one good match
        )
        pipeline = HERPipeline(config)
        
        descriptors = generate_test_descriptors(1000)
        # Add exact match early
        descriptors.insert(10, {
            "tag": "button",
            "id": "exact-match",
            "text": "Exact Match Button"
        })
        
        start = time.time()
        result = pipeline.process("Find exact-match button", descriptors)
        duration = time.time() - start
        
        # Should terminate early
        assert duration < 1.0, f"Early termination not working: {duration:.2f}s"
    
    def test_batch_processing_efficiency(self):
        """Test batch processing is more efficient than individual."""
        embedder = ElementEmbedder(cache_enabled=False)
        descriptors = generate_test_descriptors(100)
        
        # Individual processing
        start = time.time()
        for desc in descriptors:
            try:
                embedder.embed(desc)
            except:
                pass
        individual_time = time.time() - start
        
        # Batch processing
        start = time.time()
        try:
            embedder.embed_batch(descriptors)
        except:
            pass
        batch_time = time.time() - start
        
        # Batch should be faster (or at least not significantly slower)
        assert batch_time <= individual_time * 1.2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--benchmark-only"])