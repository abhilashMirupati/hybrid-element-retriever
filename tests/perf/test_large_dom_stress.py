"""Test performance with large DOM trees."""

import time
import pytest
from her.pipeline import HERPipeline, PipelineConfig


class TestLargeDOMStress:
    """Test handling of large DOM trees with 10k+ nodes."""
    
    @pytest.fixture
    def large_dom(self):
        """Generate a large DOM with 10k+ nodes."""
        elements = []
        for i in range(10000):
            elements.append({
                "tag": "div" if i % 3 == 0 else "span" if i % 3 == 1 else "p",
                "text": f"Element {i}",
                "xpath": f"//div[@id='container']//*[{i+1}]",
                "attributes": {"id": f"elem_{i}", "class": f"item-{i % 100}"},
                "is_visible": i < 1000  # Only first 1000 visible
            })
        return {"elements": elements}
    
    @pytest.fixture
    def pipeline(self):
        """Create pipeline optimized for large DOMs."""
        config = PipelineConfig(
            max_elements_to_embed=1000,
            enable_incremental_updates=True,
            batch_size=100
        )
        return HERPipeline(config=config)
    
    @pytest.mark.slow
    def test_large_dom_no_timeout(self, pipeline, large_dom):
        """Test that large DOM doesn't cause timeout."""
        start = time.perf_counter()
        
        # Should complete within reasonable time
        result = pipeline.process("find element 500", large_dom)
        
        elapsed = time.perf_counter() - start
        
        assert result is not None
        assert elapsed < 30  # Should complete within 30 seconds
        print(f"Large DOM processing time: {elapsed:.2f}s")
    
    def test_partial_embedding_on_deltas(self, pipeline, large_dom):
        """Test that only deltas are embedded on updates."""
        # Process initial DOM
        pipeline.process("test", large_dom)
        
        # Add new elements (delta)
        new_elements = [
            {"tag": "button", "text": "New Button", "xpath": "//button[@id='new']"}
        ]
        updated_dom = {
            "elements": large_dom["elements"] + new_elements
        }
        
        embed_count = 0
        original_embed = pipeline._embed_element
        
        def count_embeds(element):
            nonlocal embed_count
            embed_count += 1
            return original_embed(element)
        
        pipeline._embed_element = count_embeds
        
        # Process updated DOM
        pipeline.process("find new button", updated_dom)
        
        # Should only embed the new elements
        assert embed_count <= len(new_elements) + 10  # Allow some overhead
    
    def test_memory_efficiency(self, pipeline, large_dom):
        """Test memory usage stays reasonable with large DOM."""
        import gc
        import sys
        
        gc.collect()
        initial_memory = sys.getsizeof(pipeline.cache)
        
        # Process large DOM
        pipeline.process("test query", large_dom)
        
        gc.collect()
        final_memory = sys.getsizeof(pipeline.cache)
        
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable
        assert memory_increase < 100 * 1024 * 1024  # Less than 100MB
    
    def test_query_performance_on_large_dom(self, pipeline, large_dom):
        """Test query performance scales well with DOM size."""
        queries = [
            "find element 100",
            "find element 5000",
            "find element 9999"
        ]
        
        times = []
        for query in queries:
            start = time.perf_counter()
            result = pipeline.process(query, large_dom)
            elapsed = time.perf_counter() - start
            times.append(elapsed)
            assert result is not None
        
        # Times should not increase dramatically
        assert max(times) < min(times) * 3  # No more than 3x difference
        
        print(f"Query times on 10k DOM: {[f'{t:.3f}s' for t in times]}")
    
    def test_batch_processing(self, pipeline, large_dom):
        """Test that elements are processed in batches."""
        batch_sizes = []
        
        original_process_batch = pipeline._process_element_batch
        
        def track_batch(batch):
            batch_sizes.append(len(batch))
            return original_process_batch(batch)
        
        pipeline._process_element_batch = track_batch
        
        pipeline.process("test", large_dom)
        
        # Should process in batches
        assert len(batch_sizes) > 1
        assert all(size <= pipeline.config.batch_size for size in batch_sizes[:-1])
    
    def test_visibility_filtering(self, pipeline, large_dom):
        """Test that invisible elements are filtered efficiently."""
        # Count visible elements
        visible_count = sum(1 for e in large_dom["elements"] if e.get("is_visible", True))
        
        processed_count = 0
        original_process = pipeline._process_element
        
        def count_processed(element):
            nonlocal processed_count
            if element.get("is_visible", True):
                processed_count += 1
            return original_process(element)
        
        pipeline._process_element = count_processed
        
        pipeline.process("find visible element", large_dom)
        
        # Should only process visible elements
        assert processed_count <= visible_count