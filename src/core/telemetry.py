"""Telemetry and monitoring for Penny Assistant."""

import time
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class Telemetry:
    """Main Telemetry class for monitoring."""
    
    def __init__(self):
        self.collector = TelemetryCollector()
    
    def log_event(self, event_type: str, data: Dict[str, Any] = None):
        """Log an event."""
        return self.collector.log_event(event_type, data)
    
    def log_performance(self, operation: str, duration: float):
        """Log performance metrics."""
        return self.collector.log_performance(operation, duration)

class TelemetryCollector:
    """Collects and logs telemetry data."""
    
    def __init__(self):
        self.metrics = {}
        self.start_time = time.time()
    
    def log_event(self, event_type: str, data: Dict[str, Any] = None):
        """Log an event with optional data."""
        timestamp = time.time()
        event = {
            'type': event_type,
            'timestamp': timestamp,
            'data': data or {}
        }
        logger.info(f"Telemetry: {event}")
    
    def log_performance(self, operation: str, duration: float):
        """Log performance metrics."""
        self.log_event('performance', {
            'operation': operation,
            'duration_ms': duration * 1000
        })
    
    def start_timer(self, operation: str):
        """Start timing an operation."""
        self.metrics[operation] = time.time()
    
    def end_timer(self, operation: str):
        """End timing an operation and log it."""
        if operation in self.metrics:
            duration = time.time() - self.metrics[operation]
            self.log_performance(operation, duration)
            del self.metrics[operation]

# Global telemetry instance
telemetry = TelemetryCollector()
