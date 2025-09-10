#!/usr/bin/env python3
"""
Performance Monitor System
Toggleable performance monitoring that doesn't impact demo speed when disabled
"""

import time
import threading
from contextlib import contextmanager, nullcontext
from collections import defaultdict
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum

from integrated_config import is_monitoring_enabled, is_demo_mode


class OperationType(Enum):
    """Types of operations we monitor."""
    STT = "speech_to_text"
    LLM = "language_model"
    TTS = "text_to_speech"
    PERSONALITY_GENERATION = "personality_generation"
    ML_LEARNING = "ml_learning"
    STATE_TRANSITION = "state_transition"
    HUMOR_DETECTION = "humor_detection"
    TOTAL_PIPELINE = "total_pipeline"


@dataclass
class OperationMetric:
    """Single performance metric."""
    operation: str
    duration_ms: float
    timestamp: float
    success: bool = True
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class PerformanceMonitor:
    """Thread-safe performance monitoring with toggleable overhead."""
    
    def __init__(self, enabled: Optional[bool] = None):
        self.enabled = enabled if enabled is not None else is_monitoring_enabled()
        self.demo_mode = is_demo_mode()
        
        # Thread-safe storage
        self._lock = threading.Lock()
        self._metrics: List[OperationMetric] = []
        self._current_operations: Dict[str, float] = {}
        
        # Summary stats
        self._operation_counts = defaultdict(int)
        self._operation_times = defaultdict(list)
        
    def is_enabled(self) -> bool:
        """Check if monitoring is enabled."""
        return self.enabled and not self.demo_mode
    
    @contextmanager
    def time_operation(self, operation: Union[OperationType, str], metadata: Optional[Dict[str, Any]] = None):
        """
        Context manager for timing operations.
        Zero overhead when monitoring disabled.
        """
        if not self.is_enabled():
            yield
            return
        
        operation_name = operation.value if isinstance(operation, OperationType) else operation
        start_time = time.time()
        success = True
        error_message = None
        
        try:
            yield
        except Exception as e:
            success = False
            error_message = str(e)
            raise
        finally:
            if self.is_enabled():  # Double-check in case config changed
                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000
                
                metric = OperationMetric(
                    operation=operation_name,
                    duration_ms=duration_ms,
                    timestamp=start_time,
                    success=success,
                    error_message=error_message,
                    metadata=metadata
                )
                
                self._record_metric(metric)
    
    def _record_metric(self, metric: OperationMetric):
        """Thread-safe metric recording."""
        with self._lock:
            self._metrics.append(metric)
            self._operation_counts[metric.operation] += 1
            self._operation_times[metric.operation].append(metric.duration_ms)
            
            # Keep only recent metrics to prevent memory growth
            if len(self._metrics) > 1000:
                self._metrics = self._metrics[-500:]
    
    def record_instant_metric(self, operation: Union[OperationType, str], 
                            value: float, metadata: Optional[Dict[str, Any]] = None):
        """Record an instant metric (not timed)."""
        if not self.is_enabled():
            return
        
        operation_name = operation.value if isinstance(operation, OperationType) else operation
        metric = OperationMetric(
            operation=operation_name,
            duration_ms=value,
            timestamp=time.time(),
            metadata=metadata
        )
        self._record_metric(metric)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary statistics."""
        if not self.is_enabled():
            return {"monitoring_disabled": True}
        
        with self._lock:
            summary = {
                "total_operations": len(self._metrics),
                "operation_breakdown": dict(self._operation_counts),
                "averages_ms": {},
                "totals_ms": {},
                "recent_operations": []
            }
            
            # Calculate averages and totals
            for operation, times in self._operation_times.items():
                if times:
                    summary["averages_ms"][operation] = round(sum(times) / len(times), 2)
                    summary["totals_ms"][operation] = round(sum(times), 2)
            
            # Recent operations (last 10)
            recent_metrics = self._metrics[-10:] if self._metrics else []
            summary["recent_operations"] = [
                {
                    "operation": m.operation,
                    "duration_ms": round(m.duration_ms, 2),
                    "success": m.success,
                    "timestamp": m.timestamp
                }
                for m in recent_metrics
            ]
            
            return summary
    
    def get_pipeline_breakdown(self) -> Dict[str, float]:
        """Get breakdown of pipeline timing for optimization."""
        if not self.is_enabled():
            return {}
        
        with self._lock:
            pipeline_ops = [
                OperationType.STT.value,
                OperationType.PERSONALITY_GENERATION.value,
                OperationType.TTS.value
            ]
            
            breakdown = {}
            for op in pipeline_ops:
                times = self._operation_times.get(op, [])
                if times:
                    breakdown[op] = round(sum(times[-5:]) / len(times[-5:]), 2)  # Last 5 avg
            
            return breakdown
    
    def clear_metrics(self):
        """Clear all collected metrics."""
        with self._lock:
            self._metrics.clear()
            self._operation_counts.clear()
            self._operation_times.clear()
    
    def export_metrics(self) -> List[Dict[str, Any]]:
        """Export all metrics for analysis."""
        if not self.is_enabled():
            return []
        
        with self._lock:
            return [
                {
                    "operation": m.operation,
                    "duration_ms": m.duration_ms,
                    "timestamp": m.timestamp,
                    "success": m.success,
                    "error_message": m.error_message,
                    "metadata": m.metadata
                }
                for m in self._metrics
            ]


# Global monitor instance
_global_monitor: Optional[PerformanceMonitor] = None
_monitor_lock = threading.Lock()


def get_global_monitor() -> PerformanceMonitor:
    """Get or create global performance monitor instance."""
    global _global_monitor
    
    with _monitor_lock:
        if _global_monitor is None:
            _global_monitor = PerformanceMonitor()
        return _global_monitor


def reset_global_monitor():
    """Reset global monitor (useful for testing)."""
    global _global_monitor
    
    with _monitor_lock:
        _global_monitor = None


@contextmanager
def time_operation(operation: Union[OperationType, str], metadata: Optional[Dict[str, Any]] = None):
    """Convenience function for timing operations with global monitor."""
    monitor = get_global_monitor()
    with monitor.time_operation(operation, metadata):
        yield


def record_metric(operation: Union[OperationType, str], value: float, metadata: Optional[Dict[str, Any]] = None):
    """Convenience function for recording instant metrics."""
    monitor = get_global_monitor()
    monitor.record_instant_metric(operation, value, metadata)


def get_performance_summary() -> Dict[str, Any]:
    """Get current performance summary."""
    monitor = get_global_monitor()
    return monitor.get_summary()


def get_pipeline_breakdown() -> Dict[str, float]:
    """Get pipeline performance breakdown."""
    monitor = get_global_monitor()
    return monitor.get_pipeline_breakdown()


if __name__ == "__main__":
    print("Testing Performance Monitor System")
    print("=" * 40)
    
    # Test with monitoring enabled
    monitor = PerformanceMonitor(enabled=True)
    
    # Simulate some operations
    with monitor.time_operation(OperationType.STT, {"audio_length": 3.5}):
        time.sleep(0.1)  # Simulate STT processing
    
    with monitor.time_operation(OperationType.PERSONALITY_GENERATION, {"state": "mischievous"}):
        time.sleep(0.05)  # Simulate personality processing
    
    with monitor.time_operation(OperationType.TTS, {"text_length": 150}):
        time.sleep(0.2)  # Simulate TTS processing
    
    # Record an instant metric
    monitor.record_instant_metric(OperationType.ML_LEARNING, 45.2, {"success_score": 0.8})
    
    # Get summary
    summary = monitor.get_summary()
    print(f"Total operations: {summary['total_operations']}")
    print(f"Operation breakdown: {summary['operation_breakdown']}")
    print(f"Averages: {summary['averages_ms']}")
    
    # Test pipeline breakdown
    breakdown = monitor.get_pipeline_breakdown()
    print(f"Pipeline breakdown: {breakdown}")
    
    # Test disabled monitor (should have zero overhead)
    disabled_monitor = PerformanceMonitor(enabled=False)
    
    with disabled_monitor.time_operation(OperationType.STT):
        time.sleep(0.1)
    
    disabled_summary = disabled_monitor.get_summary()
    print(f"Disabled monitor summary: {disabled_summary}")
    
    print("\\nPerformance monitoring system ready!")
    print("Zero overhead when disabled, detailed metrics when enabled.")
