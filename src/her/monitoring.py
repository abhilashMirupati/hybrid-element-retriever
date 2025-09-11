"""
Monitoring and metrics for HER pipeline.
"""

import time
from typing import Dict, Any
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class Metrics:
    """Metrics collection for HER operations."""
    query_count: int = 0
    success_count: int = 0
    error_count: int = 0
    avg_processing_time: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "query_count": self.query_count,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "success_rate": self.success_count / max(self.query_count, 1),
            "avg_processing_time": self.avg_processing_time,
            "cache_hit_rate": self.cache_hits / max(self.cache_hits + self.cache_misses, 1)
        }

class MetricsCollector:
    """Collects and aggregates metrics."""
    
    def __init__(self):
        self.metrics = Metrics()
        self.timings = []
    
    def record_query(self, success: bool, processing_time: float, cache_hit: bool = False):
        """Record a query execution."""
        self.metrics.query_count += 1
        if success:
            self.metrics.success_count += 1
        else:
            self.metrics.error_count += 1
        
        self.timings.append(processing_time)
        self.metrics.avg_processing_time = sum(self.timings) / len(self.timings)
        
        if cache_hit:
            self.metrics.cache_hits += 1
        else:
            self.metrics.cache_misses += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        return self.metrics.to_dict()
    
    def reset(self):
        """Reset all metrics."""
        self.metrics = Metrics()
        self.timings = []

# Global metrics collector
metrics_collector = MetricsCollector()