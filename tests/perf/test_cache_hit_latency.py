"""Test cache performance and latency."""

import time
import pytest
from statistics import median
from her.pipeline import HERPipeline, PipelineConfig
from her.cache.two_tier import TwoTierCache


class TestCacheHitLatency:
    """Test cold vs warm cache performance."""
    
    @pytest.fixture
    def pipeline(self, tmp_path):
        """Create pipeline with cache."""
        config = PipelineConfig(
            cache_dir=str(tmp_path),
            enable_cold_start_detection=True
        )
        return HERPipeline(config=config)
    
    def test_cold_vs_warm_timing(self, pipeline):
        """Test that warm cache is faster than cold."""
        dom = {
            "elements": [
                {"tag": f"div", "text": f"Element {i}", "xpath": f"//div[{i}]"}
                for i in range(50)
            ]
        }
        
        # Cold start timings
        cold_times = []
        for i in range(5):
            pipeline.cache.clear()  # Ensure cold start
            start = time.perf_counter()
            pipeline.process(f"find element {i}", dom)
            cold_times.append(time.perf_counter() - start)
        
        # Warm cache timings (reuse same queries)
        warm_times = []
        for i in range(5):
            start = time.perf_counter()
            pipeline.process(f"find element {i}", dom)
            warm_times.append(time.perf_counter() - start)
        
        cold_median = median(cold_times)
        warm_median = median(warm_times)
        
        print(f"\nCache Performance:")
        print(f"  Cold median: {cold_median*1000:.2f}ms")
        print(f"  Warm median: {warm_median*1000:.2f}ms")
        print(f"  Speedup: {cold_median/warm_median:.1f}x")
        
        # Warm should be at least 2x faster
        assert warm_median < cold_median / 2
    
    def test_cache_hit_ratio(self, pipeline):
        """Test cache hit ratio improves over time."""
        dom = {
            "elements": [
                {"tag": "button", "text": f"Button {i}", "xpath": f"//button[{i}]"}
                for i in range(20)
            ]
        }
        
        queries = [
            "click button 1",
            "click button 2", 
            "click button 1",  # Repeat
            "click button 3",
            "click button 2",  # Repeat
            "click button 1",  # Repeat
        ]
        
        hits = 0
        misses = 0
        
        original_get = pipeline.cache.get
        def tracked_get(key):
            nonlocal hits, misses
            result = original_get(key)
            if result:
                hits += 1
            else:
                misses += 1
            return result
        
        pipeline.cache.get = tracked_get
        
        for query in queries:
            pipeline.process(query, dom)
        
        hit_ratio = hits / (hits + misses) if (hits + misses) > 0 else 0
        
        print(f"\nCache Hit Ratio: {hit_ratio:.1%}")
        print(f"  Hits: {hits}, Misses: {misses}")
        
        # Should have good hit ratio for repeated queries
        assert hit_ratio >= 0.3  # At least 30% hits
    
    def test_embedding_cache_performance(self, pipeline):
        """Test embedding cache reduces computation."""
        elements = [
            {"tag": "div", "text": f"Text {i}", "xpath": f"//div[{i}]"}
            for i in range(100)
        ]
        
        embed_calls = 0
        original_embed = pipeline._embed_element
        
        def counted_embed(element):
            nonlocal embed_calls
            embed_calls += 1
            return original_embed(element)
        
        pipeline._embed_element = counted_embed
        
        # First pass - all elements embedded
        pipeline.process("find text", {"elements": elements})
        first_pass_embeds = embed_calls
        
        # Second pass - should use cache
        embed_calls = 0
        pipeline.process("find different text", {"elements": elements})
        second_pass_embeds = embed_calls
        
        print(f"\nEmbedding Cache:")
        print(f"  First pass: {first_pass_embeds} embeddings")
        print(f"  Second pass: {second_pass_embeds} embeddings")
        print(f"  Cache savings: {first_pass_embeds - second_pass_embeds} calls")
        
        # Second pass should have significantly fewer embeddings
        assert second_pass_embeds < first_pass_embeds / 2
    
    def test_latency_percentiles(self, pipeline):
        """Test latency percentiles for SLA compliance."""
        dom = {
            "elements": [
                {"tag": "input", "text": "", "xpath": f"//input[{i}]"}
                for i in range(30)
            ]
        }
        
        latencies = []
        for i in range(20):
            start = time.perf_counter()
            pipeline.process(f"find input {i % 10}", dom)
            latencies.append(time.perf_counter() - start)
        
        latencies.sort()
        p50 = latencies[len(latencies) // 2]
        p95 = latencies[int(len(latencies) * 0.95)]
        p99 = latencies[int(len(latencies) * 0.99)]
        
        print(f"\nLatency Percentiles:")
        print(f"  P50: {p50*1000:.2f}ms")
        print(f"  P95: {p95*1000:.2f}ms")  
        print(f"  P99: {p99*1000:.2f}ms")
        
        # Sub-2 second for P95
        assert p95 < 2.0
    
    def test_cache_memory_usage(self, pipeline):
        """Test cache memory usage stays bounded."""
# import sys
        # Fill cache with data
        for i in range(1000):
            key = f"test_key_{i}"
            value = {"data": f"value_{i}" * 100}  # ~1KB each
            pipeline.cache.set(key, value)
        
        # Check memory cache size is bounded
        memory_items = len(pipeline.cache.memory_cache)
        assert memory_items <= pipeline.cache.max_memory_items
        
        print(f"\nCache Memory Usage:")
        print(f"  Items in memory: {memory_items}")
        print(f"  Max allowed: {pipeline.cache.max_memory_items}")
    
    def test_sqlite_fallback_performance(self, pipeline):
        """Test SQLite fallback performance for evicted items."""
        # Fill memory cache to capacity
        for i in range(pipeline.cache.max_memory_items + 10):
            pipeline.cache.set(f"key_{i}", {"value": i})
        
        # Early items should be in SQLite only
        sqlite_times = []
        for i in range(5):
            start = time.perf_counter()
            result = pipeline.cache.get(f"key_{i}")
            sqlite_times.append(time.perf_counter() - start)
            assert result is not None  # Should still be retrievable
        
        # Recent items should be in memory
        memory_times = []
        for i in range(pipeline.cache.max_memory_items - 5, pipeline.cache.max_memory_items):
            start = time.perf_counter()
            result = pipeline.cache.get(f"key_{i}")
            memory_times.append(time.perf_counter() - start)
        
        sqlite_median = median(sqlite_times)
        memory_median = median(memory_times)
        
        print(f"\nCache Backend Performance:")
        print(f"  SQLite median: {sqlite_median*1000:.2f}ms")
        print(f"  Memory median: {memory_median*1000:.2f}ms")
        
        # Memory should be faster than SQLite
        assert memory_median < sqlite_median