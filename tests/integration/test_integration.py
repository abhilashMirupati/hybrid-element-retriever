"""
Integration tests for HER pipeline.
Tests the full flow from input to execution.
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.her.core.runner import Runner
from src.her.core.pipeline import HybridPipeline
from src.her.parser.enhanced_intent import EnhancedIntentParser

class TestIntegration:
    """Integration test suite."""
    
    def test_runner_initialization(self):
        """Test that Runner initializes correctly."""
        runner = Runner(headless=True)
        assert runner is not None
        assert runner.headless is True
    
    def test_pipeline_initialization(self):
        """Test that Pipeline initializes correctly."""
        pipeline = HybridPipeline()
        assert pipeline is not None
    
    def test_intent_parser_initialization(self):
        """Test that IntentParser initializes correctly."""
        parser = EnhancedIntentParser()
        assert parser is not None
    
    def test_runner_with_dependency_injection(self):
        """Test Runner with dependency injection."""
        pipeline = HybridPipeline()
        parser = EnhancedIntentParser()
        
        runner = Runner(
            headless=True,
            intent_parser=parser,
            pipeline=pipeline
        )
        
        assert runner.pipeline is pipeline
        assert runner.intent is parser
    
    def test_runner_with_invalid_pipeline(self):
        """Test Runner with invalid pipeline raises error."""
        with pytest.raises(ValueError, match="Provided pipeline must have a 'query' method"):
            Runner(headless=True, pipeline="invalid_pipeline")
    
    def test_metrics_collection(self):
        """Test that metrics are collected properly."""
        from src.her.monitoring import metrics_collector
        
        # Reset metrics
        metrics_collector.reset()
        
        # Record some test metrics
        metrics_collector.record_query(success=True, processing_time=1.0, cache_hit=True)
        metrics_collector.record_query(success=False, processing_time=2.0, cache_hit=False)
        
        metrics = metrics_collector.get_metrics()
        
        assert metrics["query_count"] == 2
        assert metrics["success_count"] == 1
        assert metrics["error_count"] == 1
        assert metrics["success_rate"] == 0.5
        assert metrics["cache_hit_rate"] == 0.5