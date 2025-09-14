"""
Enterprise Monitoring and Metrics for HER Framework

Provides comprehensive monitoring, metrics, and observability for enterprise SaaS deployment:
- Performance metrics tracking
- Accuracy monitoring
- Error rate analysis
- Resource usage monitoring
- SLA compliance tracking
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict, deque
import threading

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for a single operation."""
    
    # Timing metrics
    total_time_ms: float
    parse_time_ms: float
    snapshot_time_ms: float
    matching_time_ms: float
    reranking_time_ms: float
    xpath_time_ms: float
    execution_time_ms: float
    
    # Accuracy metrics
    confidence_score: float
    used_promotion: bool
    promotion_hit: bool
    
    # Resource metrics
    memory_usage_mb: float
    cpu_usage_percent: float
    
    # Success metrics
    success: bool
    error_type: Optional[str] = None


@dataclass
class SLAThresholds:
    """SLA thresholds for enterprise monitoring."""
    
    # Performance thresholds
    max_total_time_ms: float = 5000.0  # 5 seconds
    max_parse_time_ms: float = 100.0   # 100ms
    max_snapshot_time_ms: float = 2000.0  # 2 seconds
    max_execution_time_ms: float = 3000.0  # 3 seconds
    
    # Accuracy thresholds
    min_confidence_score: float = 0.7  # 70%
    min_success_rate: float = 0.95     # 95%
    
    # Resource thresholds
    max_memory_usage_mb: float = 1000.0  # 1GB
    max_cpu_usage_percent: float = 80.0  # 80%


class EnterpriseMonitor:
    """Enterprise-grade monitoring and metrics collection."""
    
    def __init__(self, sla_thresholds: Optional[SLAThresholds] = None):
        self.sla_thresholds = sla_thresholds or SLAThresholds()
        
        # Metrics storage
        self.metrics_history: deque = deque(maxlen=10000)  # Keep last 10k operations
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.stage_timings: Dict[str, List[float]] = defaultdict(list)
        
        # Thread safety
        self._lock = threading.RLock()
        
        # SLA tracking
        self.sla_violations: Dict[str, int] = defaultdict(int)
        self.current_success_rate = 0.0
        self.current_avg_response_time = 0.0
    
    def record_operation(self, metrics: PerformanceMetrics) -> None:
        """Record performance metrics for an operation."""
        with self._lock:
            # Store metrics
            self.metrics_history.append(metrics)
            
            # Update error counts
            if not metrics.success and metrics.error_type:
                self.error_counts[metrics.error_type] += 1
            
            # Update stage timings
            self.stage_timings['parse'].append(metrics.parse_time_ms)
            self.stage_timings['snapshot'].append(metrics.snapshot_time_ms)
            self.stage_timings['matching'].append(metrics.matching_time_ms)
            self.stage_timings['reranking'].append(metrics.reranking_time_ms)
            self.stage_timings['xpath'].append(metrics.xpath_time_ms)
            self.stage_timings['execution'].append(metrics.execution_time_ms)
            
            # Check SLA violations
            self._check_sla_violations(metrics)
            
            # Update aggregated metrics
            self._update_aggregated_metrics()
    
    def _check_sla_violations(self, metrics: PerformanceMetrics) -> None:
        """Check for SLA violations."""
        violations = []
        
        # Performance violations
        if metrics.total_time_ms > self.sla_thresholds.max_total_time_ms:
            violations.append('total_time')
        if metrics.parse_time_ms > self.sla_thresholds.max_parse_time_ms:
            violations.append('parse_time')
        if metrics.snapshot_time_ms > self.sla_thresholds.max_snapshot_time_ms:
            violations.append('snapshot_time')
        if metrics.execution_time_ms > self.sla_thresholds.max_execution_time_ms:
            violations.append('execution_time')
        
        # Accuracy violations
        if metrics.confidence_score < self.sla_thresholds.min_confidence_score:
            violations.append('confidence_score')
        
        # Resource violations
        if metrics.memory_usage_mb > self.sla_thresholds.max_memory_usage_mb:
            violations.append('memory_usage')
        if metrics.cpu_usage_percent > self.sla_thresholds.max_cpu_usage_percent:
            violations.append('cpu_usage')
        
        # Record violations
        for violation in violations:
            self.sla_violations[violation] += 1
    
    def _update_aggregated_metrics(self) -> None:
        """Update aggregated metrics."""
        if not self.metrics_history:
            return
        
        # Calculate success rate
        successful_ops = sum(1 for m in self.metrics_history if m.success)
        self.current_success_rate = successful_ops / len(self.metrics_history)
        
        # Calculate average response time
        total_times = [m.total_time_ms for m in self.metrics_history]
        self.current_avg_response_time = sum(total_times) / len(total_times)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        with self._lock:
            if not self.metrics_history:
                return {"error": "No metrics available"}
            
            recent_metrics = list(self.metrics_history)[-100:]  # Last 100 operations
            
            # Calculate statistics
            total_times = [m.total_time_ms for m in recent_metrics]
            confidence_scores = [m.confidence_score for m in recent_metrics if m.confidence_score > 0]
            success_rates = [m.success for m in recent_metrics]
            
            summary = {
                "total_operations": len(self.metrics_history),
                "recent_operations": len(recent_metrics),
                "success_rate": sum(success_rates) / len(success_rates) if success_rates else 0.0,
                "avg_response_time_ms": sum(total_times) / len(total_times) if total_times else 0.0,
                "p95_response_time_ms": sorted(total_times)[int(len(total_times) * 0.95)] if total_times else 0.0,
                "avg_confidence": sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0,
                "promotion_hit_rate": sum(1 for m in recent_metrics if m.promotion_hit) / len(recent_metrics),
                "error_counts": dict(self.error_counts),
                "sla_violations": dict(self.sla_violations),
                "stage_performance": self._get_stage_performance()
            }
            
            return summary
    
    def _get_stage_performance(self) -> Dict[str, Dict[str, float]]:
        """Get performance metrics for each pipeline stage."""
        stage_perf = {}
        
        for stage, timings in self.stage_timings.items():
            if timings:
                stage_perf[stage] = {
                    "avg_ms": sum(timings) / len(timings),
                    "p95_ms": sorted(timings)[int(len(timings) * 0.95)],
                    "max_ms": max(timings),
                    "min_ms": min(timings),
                    "count": len(timings)
                }
        
        return stage_perf
    
    def get_sla_status(self) -> Dict[str, Any]:
        """Get SLA compliance status."""
        with self._lock:
            if not self.metrics_history:
                return {"status": "no_data"}
            
            recent_metrics = list(self.metrics_history)[-1000:]  # Last 1000 operations
            
            # Calculate SLA compliance
            total_ops = len(recent_metrics)
            successful_ops = sum(1 for m in recent_metrics if m.success)
            success_rate = successful_ops / total_ops if total_ops > 0 else 0.0
            
            # Check if success rate meets SLA
            sla_compliant = success_rate >= self.sla_thresholds.min_success_rate
            
            # Calculate average response time
            avg_response_time = sum(m.total_time_ms for m in recent_metrics) / total_ops if total_ops > 0 else 0.0
            
            return {
                "status": "compliant" if sla_compliant else "violation",
                "success_rate": success_rate,
                "required_success_rate": self.sla_thresholds.min_success_rate,
                "avg_response_time_ms": avg_response_time,
                "max_allowed_time_ms": self.sla_thresholds.max_total_time_ms,
                "violations": dict(self.sla_violations),
                "total_operations": total_ops
            }
    
    def get_health_check(self) -> Dict[str, Any]:
        """Get system health check status."""
        with self._lock:
            if not self.metrics_history:
                return {"status": "unhealthy", "reason": "no_metrics"}
            
            recent_metrics = list(self.metrics_history)[-100:]
            
            # Check various health indicators
            success_rate = sum(1 for m in recent_metrics if m.success) / len(recent_metrics)
            avg_response_time = sum(m.total_time_ms for m in recent_metrics) / len(recent_metrics)
            
            health_issues = []
            
            if success_rate < 0.9:  # 90% success rate threshold
                health_issues.append(f"low_success_rate_{success_rate:.2f}")
            
            if avg_response_time > 10000:  # 10 second threshold
                health_issues.append(f"high_response_time_{avg_response_time:.0f}ms")
            
            # Check for recent errors
            recent_errors = sum(1 for m in recent_metrics if not m.success)
            if recent_errors > len(recent_metrics) * 0.1:  # More than 10% errors
                health_issues.append(f"high_error_rate_{recent_errors}")
            
            status = "healthy" if not health_issues else "unhealthy"
            
            return {
                "status": status,
                "issues": health_issues,
                "success_rate": success_rate,
                "avg_response_time_ms": avg_response_time,
                "recent_operations": len(recent_metrics)
            }
    
    def reset_metrics(self) -> None:
        """Reset all metrics (for testing or maintenance)."""
        with self._lock:
            self.metrics_history.clear()
            self.error_counts.clear()
            self.stage_timings.clear()
            self.sla_violations.clear()
            self.current_success_rate = 0.0
            self.current_avg_response_time = 0.0


# Global monitor instance
_global_monitor: Optional[EnterpriseMonitor] = None


def get_global_monitor() -> EnterpriseMonitor:
    """Get the global monitor instance."""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = EnterpriseMonitor()
    return _global_monitor


def record_operation_metrics(metrics: PerformanceMetrics) -> None:
    """Record operation metrics to the global monitor."""
    monitor = get_global_monitor()
    monitor.record_operation(metrics)