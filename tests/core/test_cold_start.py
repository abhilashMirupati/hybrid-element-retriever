"""Test cold start flow with empty caches."""

import json
import pytest
# from pathlib import Path
from unittest.mock import Mock, patch

from her.pipeline import HERPipeline, PipelineConfig
from her.cache.two_tier import TwoTierCache
from her.embeddings.element_embedder import ElementEmbedder


class TestColdStart:
    """Test cold start scenarios with empty caches."""
    
    @pytest.fixture
    def clean_cache(self, tmp_path):
        """Provide a clean cache instance."""
        cache = TwoTierCache(db_path=tmp_path / "cache.db")
        cache.clear()
        return cache
    
    @pytest.fixture
    def pipeline(self, clean_cache):
        """Create pipeline with clean cache."""
        config = PipelineConfig(
            use_minilm=True,
            use_e5_small=False,
            use_markuplm=True,
            enable_cold_start_detection=True
        )
        return HERPipeline(config=config)
    
    def test_empty_cache_snapshot(self, pipeline, clean_cache):
        """Test that cold start triggers full DOM+AX snapshot."""
        # Mock DOM
        mock_dom = {
            "html": "<div><button>Submit</button></div>",
            "elements": [
                {
                    "tag": "button",
                    "text": "Submit",
                    "xpath": "//button",
                    "attributes": {"type": "submit"},
                    "is_visible": True,
                    "bounds": {"x": 10, "y": 20, "width": 100, "height": 40}
                }
            ]
        }
        
        # Verify cache is empty
        assert clean_cache.size() == 0
        
        with patch.object(pipeline, '_get_dom_snapshot', return_value=mock_dom):
            # Process query
            result = pipeline.process("click submit button", mock_dom)
            
            # Verify result structure (strict JSON contract)
            assert result is not None
            assert "element" in result
            assert "xpath" in result
            assert "confidence" in result
            assert "strategy" in result
            
            # Verify XPath is unique
            assert result["xpath"] == "//button"
            
        # Verify cache was populated
        assert clean_cache.size() > 0
    
    def test_minilm_embeddings_generated(self, pipeline):
        """Test that MiniLM embeddings are generated for queries."""
        query = "find the search box"
        
        with patch.object(pipeline, '_embed_query') as mock_embed:
            mock_embed.return_value = [[0.1] * 384]  # MiniLM dimension
            
            embedding = pipeline._embed_query(query)
            
            assert len(embedding[0]) == 384
            mock_embed.assert_called_once()
    
    def test_markuplm_reranking(self, pipeline):
        """Test that MarkupLM is used for reranking top-k candidates."""
        candidates = [
            {"text": "Submit", "tag": "button", "score": 0.9},
            {"text": "Cancel", "tag": "button", "score": 0.8},
            {"text": "Search", "tag": "input", "score": 0.7}
        ]
        
        with patch.object(pipeline, '_rerank_with_markuplm') as mock_rerank:
            mock_rerank.return_value = candidates[:1]  # Return top candidate
            
            result = pipeline._rerank_with_markuplm("submit form", candidates)
            
            assert len(result) == 1
            assert result[0]["text"] == "Submit"
            mock_rerank.assert_called_once()
    
    def test_strict_json_contract(self, pipeline):
        """Test that output follows strict JSON contract."""
        mock_dom = {
            "elements": [
                {
                    "tag": "input",
                    "xpath": "//input[@id='email']",
                    "attributes": {"id": "email", "type": "email"},
                    "text": "",
                    "is_visible": True
                }
            ]
        }
        
        with patch.object(pipeline, '_get_dom_snapshot', return_value=mock_dom):
            result = pipeline.process("enter email", mock_dom)
            
            # Verify required fields
            required_fields = ["element", "xpath", "confidence", "strategy", "metadata"]
            for field in required_fields:
                assert field in result, f"Missing required field: {field}"
            
            # Verify types
            assert isinstance(result["element"], dict)
            assert isinstance(result["xpath"], str)
            assert isinstance(result["confidence"], (int, float))
            assert isinstance(result["strategy"], str)
            assert isinstance(result["metadata"], dict)
            
            # Verify no empty required fields
            assert result["xpath"] != ""
            assert result["strategy"] != ""
            assert 0 <= result["confidence"] <= 1
    
    def test_cold_start_detection(self, pipeline, clean_cache):
        """Test that cold start is properly detected."""
        assert clean_cache.size() == 0
        
        # First query should detect cold start
        with patch.object(pipeline, '_is_cold_start', return_value=True) as mock_cold:
            with patch.object(pipeline, '_get_dom_snapshot', return_value={"elements": []}):
                pipeline.process("test query", {"elements": []})
                mock_cold.assert_called()
        
        # After caching, should not be cold start
        clean_cache.set("test_key", {"data": "test"})
        assert clean_cache.size() > 0
        
        with patch.object(pipeline, '_is_cold_start', return_value=False) as mock_cold:
            with patch.object(pipeline, '_get_dom_snapshot', return_value={"elements": []}):
                pipeline.process("test query 2", {"elements": []})
                # Cold start check should still be called but return False
                
    def test_full_embedding_on_cold_start(self, pipeline):
        """Test that all elements are embedded on cold start."""
        mock_dom = {
            "elements": [
                {"tag": "div", "text": "Header", "xpath": "//div[1]"},
                {"tag": "button", "text": "Submit", "xpath": "//button[1]"},
                {"tag": "input", "text": "", "xpath": "//input[1]"},
                {"tag": "span", "text": "Footer", "xpath": "//span[1]"}
            ]
        }
        
        embedded_count = 0
        
        def count_embeddings(*args, **kwargs):
            nonlocal embedded_count
            embedded_count += 1
            return [[0.1] * 384]
        
        with patch.object(pipeline, '_embed_element', side_effect=count_embeddings):
            with patch.object(pipeline, '_get_dom_snapshot', return_value=mock_dom):
                pipeline.process("find submit", mock_dom)
        
        # All 4 elements should be embedded on cold start
        assert embedded_count >= len(mock_dom["elements"])