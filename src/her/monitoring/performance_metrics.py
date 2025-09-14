"""
Performance Metrics and Monitoring for both semantic and no-semantic modes.

This module provides comprehensive performance tracking, metrics collection,
and monitoring capabilities while maintaining compatibility with both
retrieval modes.
"""

from __future__ import annotations

import logging
import time
import threading

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
from typing import List, Dict, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import json

log = logging.getLogger("her.performance_metrics")


class MetricType(Enum):
    """Types of performance metrics."""
    TIMING = "timing"
    MEMORY = "memory"
    CPU = "cpu"
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"


@dataclass
class MetricPoint:
    """Single metric data point."""
    timestamp: float
    value: float
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceSnapshot:
    """Snapshot of performance metrics at a point in time."""
    timestamp: float
    memory_mb: float
    cpu_percent: float
    active_threads: int
    mode: str  # 'semantic' or 'no-semantic'
    query_count: int
    cache_hits: int
    cache_misses: int


class PerformanceMetrics:
    """Performance metrics collector and monitor."""
    
    def __init__(self, max_history: int = 1000):
        """Initialize performance metrics.
        
        Args:
            max_history: Maximum number of metric points to keep in history
        """
        self.max_history = max_history
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.timers: Dict[str, List[float]] = defaultdict(list)
        self.lock = threading.Lock()
        self.start_time = time.time()
        
        # Mode-specific tracking
        self.semantic_metrics = defaultdict(lambda: deque(maxlen=max_history))
        self.no_semantic_metrics = defaultdict(lambda: deque(maxlen=max_history))
    
    def record_timing(self, metric_name: str, duration: float, 
                     mode: str = "unknown", tags: Dict[str, str] = None):
        """Record timing metric.
        
        Args:
            metric_name: Name of the metric
            duration: Duration in seconds
            mode: Mode ('semantic' or 'no-semantic')
            tags: Additional tags
        """
        if tags is None:
            tags = {}
        
        tags['mode'] = mode
        
        with self.lock:
            point = MetricPoint(
                timestamp=time.time(),
                value=duration,
                tags=tags
            )
            
            self.metrics[metric_name].append(point)
            
            # Store in mode-specific metrics
            if mode == 'semantic':
                self.semantic_metrics[metric_name].append(point)
            elif mode == 'no-semantic':
                self.no_semantic_metrics[metric_name].append(point)
            
            # Keep timing history
            self.timers[metric_name].append(duration)
            if len(self.timers[metric_name]) > self.max_history:
                self.timers[metric_name] = self.timers[metric_name][-self.max_history:]
    
    def record_counter(self, metric_name: str, increment: int = 1, 
                      mode: str = "unknown", tags: Dict[str, str] = None):
        """Record counter metric.
        
        Args:
            metric_name: Name of the metric
            increment: Increment value
            mode: Mode ('semantic' or 'no-semantic')
            tags: Additional tags
        """
        if tags is None:
            tags = {}
        
        tags['mode'] = mode
        
        with self.lock:
            self.counters[metric_name] += increment
            
            point = MetricPoint(
                timestamp=time.time(),
                value=self.counters[metric_name],
                tags=tags
            )
            
            self.metrics[metric_name].append(point)
    
    def record_gauge(self, metric_name: str, value: float, 
                    mode: str = "unknown", tags: Dict[str, str] = None):
        """Record gauge metric.
        
        Args:
            metric_name: Name of the metric
            value: Gauge value
            mode: Mode ('semantic' or 'no-semantic')
            tags: Additional tags
        """
        if tags is None:
            tags = {}
        
        tags['mode'] = mode
        
        with self.lock:
            self.gauges[metric_name] = value
            
            point = MetricPoint(
                timestamp=time.time(),
                value=value,
                tags=tags
            )
            
            self.metrics[metric_name].append(point)
    
    def record_memory_usage(self, mode: str = "unknown"):
        """Record current memory usage.
        
        Args:
            mode: Mode ('semantic' or 'no-semantic')
        """
        if not PSUTIL_AVAILABLE:
            log.warning("psutil not available, skipping memory usage recording")
            return
            
        try:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            self.record_gauge("memory_usage_mb", memory_mb, mode)
        except Exception as e:
            log.warning(f"Failed to record memory usage: {e}")
    
    def record_cpu_usage(self, mode: str = "unknown"):
        """Record current CPU usage.
        
        Args:
            mode: Mode ('semantic' or 'no-semantic')
        """
        if not PSUTIL_AVAILABLE:
            log.warning("psutil not available, skipping CPU usage recording")
            return
            
        try:
            cpu_percent = psutil.cpu_percent()
            self.record_gauge("cpu_usage_percent", cpu_percent, mode)
        except Exception as e:
            log.warning(f"Failed to record CPU usage: {e}")
    
    def get_timing_stats(self, metric_name: str, mode: str = None) -> Dict[str, float]:
        """Get timing statistics for a metric.
        
        Args:
            metric_name: Name of the metric
            mode: Mode filter ('semantic', 'no-semantic', or None for all)
            
        Returns:
            Dictionary with timing statistics
        """
        with self.lock:
            if mode:
                if mode == 'semantic':
                    values = [p.value for p in self.semantic_metrics[metric_name]]
                elif mode == 'no-semantic':
                    values = [p.value for p in self.no_semantic_metrics[metric_name]]
                else:
                    values = []
            else:
                values = [p.value for p in self.metrics[metric_name]]
            
            if not values:
                return {}
            
            return {
                'count': len(values),
                'min': min(values),
                'max': max(values),
                'mean': sum(values) / len(values),
                'median': sorted(values)[len(values) // 2],
                'p95': sorted(values)[int(len(values) * 0.95)],
                'p99': sorted(values)[int(len(values) * 0.99)]
            }
    
    def get_counter_value(self, metric_name: str) -> int:
        """Get current counter value.
        
        Args:
            metric_name: Name of the metric
            
        Returns:
            Current counter value
        """
        with self.lock:
            return self.counters[metric_name]
    
    def get_gauge_value(self, metric_name: str) -> float:
        """Get current gauge value.
        
        Args:
            metric_name: Name of the metric
            
        Returns:
            Current gauge value
        """
        with self.lock:
            return self.gauges[metric_name]
    
    def get_performance_snapshot(self, mode: str = "unknown") -> PerformanceSnapshot:
        """Get current performance snapshot.
        
        Args:
            mode: Current mode ('semantic' or 'no-semantic')
            
        Returns:
            Performance snapshot
        """
        if PSUTIL_AVAILABLE:
            try:
                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024
                cpu_percent = psutil.cpu_percent()
                active_threads = threading.active_count()
            except Exception:
                memory_mb = 0.0
                cpu_percent = 0.0
                active_threads = 0
        else:
            memory_mb = 0.0
            cpu_percent = 0.0
            active_threads = threading.active_count()
        
        return PerformanceSnapshot(
            timestamp=time.time(),
            memory_mb=memory_mb,
            cpu_percent=cpu_percent,
            active_threads=active_threads,
            mode=mode,
            query_count=self.get_counter_value("queries_total"),
            cache_hits=self.get_counter_value("cache_hits"),
            cache_misses=self.get_counter_value("cache_misses")
        )
    
    def get_mode_comparison(self) -> Dict[str, Any]:
        """Get performance comparison between modes.
        
        Returns:
            Dictionary with mode comparison data
        """
        comparison = {
            'semantic': {},
            'no-semantic': {},
            'summary': {}
        }
        
        # Compare key metrics
        key_metrics = [
            'query_duration', 'element_processing_time', 'memory_usage_mb',
            'cache_hit_rate', 'accuracy_score'
        ]
        
        for metric in key_metrics:
            semantic_stats = self.get_timing_stats(metric, 'semantic')
            no_semantic_stats = self.get_timing_stats(metric, 'no-semantic')
            
            comparison['semantic'][metric] = semantic_stats
            comparison['no-semantic'][metric] = no_semantic_stats
            
            # Calculate comparison
            if semantic_stats and no_semantic_stats:
                semantic_mean = semantic_stats.get('mean', 0)
                no_semantic_mean = no_semantic_stats.get('mean', 0)
                
                if no_semantic_mean > 0:
                    ratio = semantic_mean / no_semantic_mean
                    comparison['summary'][f'{metric}_ratio'] = ratio
                    comparison['summary'][f'{metric}_faster'] = 'semantic' if ratio < 1 else 'no-semantic'
        
        return comparison
    
    def export_metrics(self, filepath: str):
        """Export metrics to JSON file.
        
        Args:
            filepath: Path to export file
        """
        with self.lock:
            export_data = {
                'export_time': time.time(),
                'start_time': self.start_time,
                'counters': dict(self.counters),
                'gauges': dict(self.gauges),
                'timing_stats': {},
                'mode_comparison': self.get_mode_comparison()
            }
            
            # Export timing statistics for all metrics
            for metric_name in self.metrics:
                export_data['timing_stats'][metric_name] = self.get_timing_stats(metric_name)
            
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            log.info(f"Metrics exported to {filepath}")
    
    def reset_metrics(self):
        """Reset all metrics."""
        with self.lock:
            self.metrics.clear()
            self.counters.clear()
            self.gauges.clear()
            self.timers.clear()
            self.semantic_metrics.clear()
            self.no_semantic_metrics.clear()
            self.start_time = time.time()
            
            log.info("Metrics reset")


class PerformanceTimer:
    """Context manager for timing operations."""
    
    def __init__(self, metrics: PerformanceMetrics, metric_name: str, 
                 mode: str = "unknown", tags: Dict[str, str] = None):
        """Initialize performance timer.
        
        Args:
            metrics: Performance metrics instance
            metric_name: Name of the metric
            mode: Mode ('semantic' or 'no-semantic')
            tags: Additional tags
        """
        self.metrics = metrics
        self.metric_name = metric_name
        self.mode = mode
        self.tags = tags or {}
        self.start_time = None
    
    def __enter__(self):
        """Start timing."""
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timing and record metric."""
        if self.start_time:
            duration = time.time() - self.start_time
            self.metrics.record_timing(self.metric_name, duration, self.mode, self.tags)


# Global metrics instance
_global_metrics: Optional[PerformanceMetrics] = None


def get_metrics() -> PerformanceMetrics:
    """Get global metrics instance."""
    global _global_metrics
    if _global_metrics is None:
        _global_metrics = PerformanceMetrics()
    return _global_metrics


def record_query_timing(mode: str, duration: float, success: bool = True):
    """Record query timing metric.
    
    Args:
        mode: Mode ('semantic' or 'no-semantic')
        duration: Query duration in seconds
        success: Whether query was successful
    """
    metrics = get_metrics()
    metrics.record_timing("query_duration", duration, mode, {"success": str(success)})
    metrics.record_counter("queries_total", 1, mode)
    if success:
        metrics.record_counter("queries_successful", 1, mode)
    else:
        metrics.record_counter("queries_failed", 1, mode)


def record_cache_metrics(mode: str, hit: bool):
    """Record cache metrics.
    
    Args:
        mode: Mode ('semantic' or 'no-semantic')
        hit: Whether cache hit occurred
    """
    metrics = get_metrics()
    if hit:
        metrics.record_counter("cache_hits", 1, mode)
    else:
        metrics.record_counter("cache_misses", 1, mode)


def record_memory_usage(mode: str):
    """Record memory usage for mode.
    
    Args:
        mode: Mode ('semantic' or 'no-semantic')
    """
    metrics = get_metrics()
    metrics.record_memory_usage(mode)