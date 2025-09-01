#!/usr/bin/env python3
"""
PennyGPT Metrics Collector
Collects real-time performance metrics and serves them to the dashboard
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import threading
from pathlib import Path

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.dirname(__file__))

from health_monitor import PennyGPTHealthMonitor, HealthStatus


@dataclass
class MetricPoint:
    timestamp: float
    value: float
    component: str
    metric_type: str  # 'response_time', 'requests', 'cpu', etc.


@dataclass
class SystemMetrics:
    timestamp: float
    lm_studio_response_time: float
    llm_completion_time: float
    tts_response_time: float
    stt_response_time: float
    audio_check_time: float
    total_requests: int
    cache_hit_rate: float
    system_health: str
    component_statuses: Dict[str, str]


class MetricsCollector:
    """Collects and stores PennyGPT performance metrics."""
    
    def __init__(self, history_size: int = 100):
        self.history_size = history_size
        self.metrics_history: List[SystemMetrics] = []
        self.health_monitor = PennyGPTHealthMonitor()
        self.running = False
        self.collection_thread = None
        
        # Counters
        self.total_requests = 0
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Performance tracking
        self.response_times: Dict[str, List[float]] = {
            'lm_studio': [],
            'llm_completion': [],
            'tts': [],
            'stt': [],
            'audio': []
        }
        
        # Create data directory
        self.data_dir = Path('data/metrics')
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
    async def collect_health_metrics(self) -> SystemMetrics:
        """Collect current health metrics from all components."""
        try:
            health_status = await self.health_monitor.check_all_components()
            
            # Extract response times
            lm_time = health_status.get('LM Studio', type('', (), {'response_time_ms': 0})).response_time_ms or 0
            llm_time = health_status.get('LLM Completion', type('', (), {'response_time_ms': 0})).response_time_ms or 0
            tts_time = health_status.get('TTS', type('', (), {'response_time_ms': 0})).response_time_ms or 0
            stt_time = health_status.get('STT', type('', (), {'response_time_ms': 0})).response_time_ms or 0
            audio_time = health_status.get('Audio Devices', type('', (), {'response_time_ms': 0})).response_time_ms or 0
            
            # Update running averages
            self.response_times['lm_studio'].append(lm_time)
            self.response_times['llm_completion'].append(llm_time)
            self.response_times['tts'].append(tts_time)
            self.response_times['stt'].append(stt_time)
            self.response_times['audio'].append(audio_time)
            
            # Keep only recent data
            for key in self.response_times:
                if len(self.response_times[key]) > 20:
                    self.response_times[key] = self.response_times[key][-20:]
            
            # Calculate overall health
            healthy_count = sum(1 for h in health_status.values() if h.status == HealthStatus.HEALTHY)
            total_count = len(health_status)
            
            if healthy_count == total_count:
                overall_health = "HEALTHY"
            elif healthy_count > total_count // 2:
                overall_health = "DEGRADED"
            else:
                overall_health = "UNHEALTHY"
            
            # Component statuses
            component_statuses = {
                name: health.status.value.upper()
                for name, health in health_status.items()
            }
            
            # Calculate cache hit rate
            total_cache_ops = self.cache_hits + self.cache_misses
            cache_hit_rate = (self.cache_hits / total_cache_ops * 100) if total_cache_ops > 0 else 0
            
            return SystemMetrics(
                timestamp=time.time(),
                lm_studio_response_time=lm_time,
                llm_completion_time=llm_time,
                tts_response_time=tts_time,
                stt_response_time=stt_time,
                audio_check_time=audio_time,
                total_requests=self.total_requests,
                cache_hit_rate=cache_hit_rate,
                system_health=overall_health,
                component_statuses=component_statuses
            )
            
        except Exception as e:
            print(f"Error collecting metrics: {e}")
            return SystemMetrics(
                timestamp=time.time(),
                lm_studio_response_time=0,
                llm_completion_time=0,
                tts_response_time=0,
                stt_response_time=0,
                audio_check_time=0,
                total_requests=self.total_requests,
                cache_hit_rate=0,
                system_health="UNKNOWN",
                component_statuses={}
            )
    
    def record_request(self, component: str, response_time: float, cache_hit: bool = False):
        """Record a request for metrics tracking."""
        self.total_requests += 1
        
        if cache_hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
        
        # Add to response time history
        if component in self.response_times:
            self.response_times[component].append(response_time)
            if len(self.response_times[component]) > 20:
                self.response_times[component] = self.response_times[component][-20:]
    
    async def collect_metrics_loop(self):
        """Main metrics collection loop."""
        while self.running:
            try:
                metrics = await self.collect_health_metrics()
                self.metrics_history.append(metrics)
                
                # Keep only recent history
                if len(self.metrics_history) > self.history_size:
                    self.metrics_history = self.metrics_history[-self.history_size:]
                
                # Save to file periodically
                if len(self.metrics_history) % 10 == 0:
                    await self.save_metrics()
                
                # Wait before next collection
                await asyncio.sleep(10)  # Collect every 10 seconds
                
            except Exception as e:
                print(f"Error in metrics collection loop: {e}")
                await asyncio.sleep(5)
    
    async def save_metrics(self):
        """Save metrics to file."""
        try:
            filename = self.data_dir / f"metrics_{datetime.now().strftime('%Y%m%d')}.json"
            
            # Convert to serializable format
            metrics_data = {
                'timestamp': time.time(),
                'metrics': [asdict(m) for m in self.metrics_history[-50:]]  # Save last 50 points
            }
            
            with open(filename, 'w') as f:
                json.dump(metrics_data, f, indent=2)
                
        except Exception as e:
            print(f"Error saving metrics: {e}")
    
    def get_latest_metrics(self) -> Optional[SystemMetrics]:
        """Get the most recent metrics."""
        return self.metrics_history[-1] if self.metrics_history else None
    
    def get_metrics_summary(self) -> Dict:
        """Get a summary of current metrics for the dashboard."""
        latest = self.get_latest_metrics()
        if not latest:
            return {}
        
        # Calculate averages
        avg_response_times = {}
        for component, times in self.response_times.items():
            if times:
                avg_response_times[component] = sum(times) / len(times)
            else:
                avg_response_times[component] = 0
        
        return {
            'timestamp': latest.timestamp,
            'system_health': latest.system_health,
            'component_statuses': latest.component_statuses,
            'response_times': {
                'lm_studio': latest.lm_studio_response_time,
                'llm_completion': latest.llm_completion_time,
                'tts': latest.tts_response_time,
                'stt': latest.stt_response_time,
                'audio': latest.audio_check_time
            },
            'averages': avg_response_times,
            'totals': {
                'requests': latest.total_requests,
                'cache_hit_rate': latest.cache_hit_rate
            },
            'trends': [asdict(m) for m in self.metrics_history[-20:]]  # Last 20 points for charts
        }
    
    def start_collection(self):
        """Start metrics collection in background thread."""
        if self.running:
            return
            
        self.running = True
        print("🔄 Starting metrics collection...")
        
        # Start async loop in thread
        def run_async_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.collect_metrics_loop())
        
        self.collection_thread = threading.Thread(target=run_async_loop, daemon=True)
        self.collection_thread.start()
        print("✅ Metrics collection started")
    
    def stop_collection(self):
        """Stop metrics collection."""
        if not self.running:
            return
            
        self.running = False
        print("⏹️ Stopping metrics collection...")
        
        if self.collection_thread:
            self.collection_thread.join(timeout=5)
        
        # Save final metrics
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.save_metrics())
            loop.close()
        except Exception:
            pass
            
        print("✅ Metrics collection stopped")


def main():
    """Main entry point for standalone metrics collection."""
    collector = MetricsCollector()
    
    try:
        collector.start_collection()
        print("📊 Metrics collector running...")
        print("Press Ctrl+C to stop")
        
        # Keep main thread alive
        while True:
            time.sleep(5)
            
            # Print periodic status
            latest = collector.get_latest_metrics()
            if latest:
                print(f"\r🏥 Health: {latest.system_health} | "
                      f"Requests: {latest.total_requests} | "
                      f"Cache: {latest.cache_hit_rate:.1f}% hit rate", end="")
                
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping metrics collector...")
        collector.stop_collection()
        print("👋 Goodbye!")


if __name__ == "__main__":
    main()
