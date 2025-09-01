#!/usr/bin/env python3
"""
Enhanced Metrics Collector with Memory Statistics  
Extends the original metrics collector to include memory system stats
"""

import asyncio
import json
import time
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import threading
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.dirname(__file__))

from health_monitor import PennyGPTHealthMonitor, HealthStatus
from memory_system import MemoryManager


@dataclass
class EnhancedSystemMetrics:
    """Enhanced system metrics including memory data."""
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
    
    # Memory system metrics
    total_conversations: int
    unique_sessions: int
    recent_conversations: int
    active_context_size: int
    user_preferences_count: int
    memory_db_size: int
    current_session_id: str


class EnhancedMetricsCollector:
    """Enhanced metrics collector with memory system integration."""
    
    def __init__(self, history_size: int = 100):
        self.history_size = history_size
        self.metrics_history: List[EnhancedSystemMetrics] = []
        self.health_monitor = PennyGPTHealthMonitor()
        self.memory_manager = MemoryManager()
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
        
    async def collect_enhanced_metrics(self) -> EnhancedSystemMetrics:
        """Collect enhanced metrics including memory system data."""
        try:
            # Get health metrics
            health_status = await self.health_monitor.check_all_components()
            
            # Extract response times
            lm_time = health_status.get('LM Studio', type('', (), {'response_time_ms': 0})).response_time_ms or 0
            llm_time = health_status.get('LLM Completion', type('', (), {'response_time_ms': 0})).response_time_ms or 0
            tts_time = health_status.get('TTS', type('', (), {'response_time_ms': 0})).response_time_ms or 0
            stt_time = health_status.get('STT', type('', (), {'response_time_ms': 0})).response_time_ms or 0
            audio_time = health_status.get('Audio Devices', type('', (), {'response_time_ms': 0})).response_time_ms or 0
            
            # Calculate overall health
            healthy_count = sum(1 for h in health_status.values() if h.status == HealthStatus.HEALTHY)
            total_count = len(health_status)
            
            if healthy_count == total_count:
                overall_health = "HEALTHY"
            elif healthy_count > total_count // 2:
                overall_health = "DEGRADED"
            else:
                overall_health = "UNHEALTHY"
            
            # Get memory statistics
            memory_stats = self.memory_manager.get_memory_stats()
            
            # Component statuses
            component_statuses = {
                name: health.status.value.upper()
                for name, health in health_status.items()
            }
            
            # Calculate cache hit rate
            total_cache_ops = self.cache_hits + self.cache_misses
            cache_hit_rate = (self.cache_hits / total_cache_ops * 100) if total_cache_ops > 0 else 0
            
            return EnhancedSystemMetrics(
                timestamp=time.time(),
                lm_studio_response_time=lm_time,
                llm_completion_time=llm_time,
                tts_response_time=tts_time,
                stt_response_time=stt_time,
                audio_check_time=audio_time,
                total_requests=self.total_requests,
                cache_hit_rate=cache_hit_rate,
                system_health=overall_health,
                component_statuses=component_statuses,
                total_conversations=memory_stats['total_conversation_turns'],
                unique_sessions=memory_stats['unique_sessions'],
                recent_conversations=memory_stats['recent_turns_7_days'],
                active_context_size=memory_stats['active_context_size'],
                user_preferences_count=memory_stats['user_preferences'],
                memory_db_size=memory_stats['memory_db_size'],
                current_session_id=memory_stats['current_session_id']
            )
            
        except Exception as e:
            print(f"Error collecting enhanced metrics: {e}")
            return EnhancedSystemMetrics(
                timestamp=time.time(),
                lm_studio_response_time=0,
                llm_completion_time=0,
                tts_response_time=0,
                stt_response_time=0,
                audio_check_time=0,
                total_requests=self.total_requests,
                cache_hit_rate=0,
                system_health="UNKNOWN",
                component_statuses={},
                total_conversations=0,
                unique_sessions=0,
                recent_conversations=0,
                active_context_size=0,
                user_preferences_count=0,
                memory_db_size=0,
                current_session_id="unknown"
            )
    
    async def collect_metrics_loop(self):
        """Main metrics collection loop."""
        while self.running:
            try:
                metrics = await self.collect_enhanced_metrics()
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
                print(f"Error in enhanced metrics collection loop: {e}")
                await asyncio.sleep(5)
    
    def get_enhanced_metrics_summary(self) -> Dict:
        """Get enhanced metrics summary including memory data."""
        latest = self.metrics_history[-1] if self.metrics_history else None
        if not latest:
            return {}
        
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
            'totals': {
                'requests': latest.total_requests,
                'cache_hit_rate': latest.cache_hit_rate
            },
            'memory': {
                'total_conversations': latest.total_conversations,
                'unique_sessions': latest.unique_sessions,
                'recent_conversations': latest.recent_conversations,
                'active_context_size': latest.active_context_size,
                'user_preferences_count': latest.user_preferences_count,
                'memory_db_size_mb': latest.memory_db_size / (1024 * 1024) if latest.memory_db_size else 0,
                'current_session_id': latest.current_session_id
            },
            'trends': [asdict(m) for m in self.metrics_history[-20:]]  # Last 20 points for charts
        }
    
    def start_collection(self):
        """Start enhanced metrics collection."""
        if self.running:
            return
            
        self.running = True
        print("🔄 Starting enhanced metrics collection with memory tracking...")
        
        # Start async loop in thread
        def run_async_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.collect_metrics_loop())
        
        self.collection_thread = threading.Thread(target=run_async_loop, daemon=True)
        self.collection_thread.start()
        print("✅ Enhanced metrics collection started")
    
    def stop_collection(self):
        """Stop metrics collection."""
        if not self.running:
            return
            
        self.running = False
        print("⏹️ Stopping enhanced metrics collection...")
        
        if self.collection_thread:
            self.collection_thread.join(timeout=5)
        
        print("✅ Enhanced metrics collection stopped")
    
    async def save_metrics(self):
        """Save enhanced metrics to file."""
        try:
            filename = self.data_dir / f"enhanced_metrics_{datetime.now().strftime('%Y%m%d')}.json"
            
            # Convert to serializable format
            metrics_data = {
                'timestamp': time.time(),
                'metrics': [asdict(m) for m in self.metrics_history[-50:]]  # Save last 50 points
            }
            
            with open(filename, 'w') as f:
                json.dump(metrics_data, f, indent=2)
                
        except Exception as e:
            print(f"Error saving enhanced metrics: {e}")


def main():
    """Test the enhanced metrics collector."""
    collector = EnhancedMetricsCollector()
    
    try:
        collector.start_collection()
        print("📊 Enhanced metrics collector running...")
        print("Press Ctrl+C to stop")
        
        # Keep main thread alive
        while True:
            time.sleep(5)
            
            # Print periodic status
            latest = collector.metrics_history[-1] if collector.metrics_history else None
            if latest:
                print(f"\r🏥 Health: {latest.system_health} | "
                      f"Memory: {latest.total_conversations} conversations, "
                      f"{latest.user_preferences_count} preferences | "
                      f"Session: {latest.current_session_id}", end="")
                
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping enhanced metrics collector...")
        collector.stop_collection()
        print("👋 Goodbye!")


if __name__ == "__main__":
    main()
