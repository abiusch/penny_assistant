#!/usr/bin/env python3
"""
Performance Logger for PennyGPT
Tracks timing and performance metrics for voice assistant conversations
"""

import csv
import time
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class ConversationMetrics:
    """Metrics for a single conversation turn."""
    timestamp: float
    session_id: str
    
    # Audio processing
    vad_time_ms: float
    stt_time_ms: float
    
    # LLM processing  
    llm_time_ms: float
    memory_context_length: int
    
    # TTS processing
    tts_time_ms: float
    tts_cache_hit: bool
    
    # Content metrics
    user_input_length: int
    response_length: int
    wake_word_detected: bool
    
    # End-to-end
    total_time_ms: float


class PerformanceLogger:
    """Logs performance metrics to CSV files with analysis capabilities."""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # CSV file paths
        self.csv_file = self.log_dir / "performance_log.csv"
        self.session_file = self.log_dir / "session_summary.csv"
        
        # Session tracking
        self.session_id = f"session_{int(time.time())}"
        self.session_start = time.time()
        self.conversation_count = 0
        
        # Initialize CSV files with headers
        self._init_csv_files()
        
    def _init_csv_files(self):
        """Initialize CSV files with headers if they don't exist."""
        if not self.csv_file.exists():
            with open(self.csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp', 'session_id', 'vad_time_ms', 'stt_time_ms',
                    'llm_time_ms', 'memory_context_length', 'tts_time_ms', 
                    'tts_cache_hit', 'user_input_length', 'response_length',
                    'wake_word_detected', 'total_time_ms'
                ])
                
        if not self.session_file.exists():
            with open(self.session_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'session_id', 'start_time', 'duration_minutes', 
                    'conversation_count', 'avg_response_time_ms', 
                    'cache_hit_rate', 'avg_stt_time_ms', 'avg_llm_time_ms'
                ])
    
    def log_conversation(self, metrics: ConversationMetrics) -> None:
        """Log a single conversation turn."""
        # Set session ID
        metrics.session_id = self.session_id
        self.conversation_count += 1
        
        # Append to CSV
        with open(self.csv_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                metrics.timestamp, metrics.session_id, metrics.vad_time_ms,
                metrics.stt_time_ms, metrics.llm_time_ms, metrics.memory_context_length,
                metrics.tts_time_ms, metrics.tts_cache_hit, metrics.user_input_length,
                metrics.response_length, metrics.wake_word_detected, metrics.total_time_ms
            ])
        
        # Real-time console output
        print(f"📊 Performance: STT {metrics.stt_time_ms:.0f}ms | "
              f"LLM {metrics.llm_time_ms:.0f}ms | "
              f"TTS {metrics.tts_time_ms:.0f}ms | "
              f"Total {metrics.total_time_ms:.0f}ms | "
              f"Cache {'HIT' if metrics.tts_cache_hit else 'MISS'}")
    
    def end_session(self) -> Dict[str, Any]:
        """End the current session and log summary."""
        session_duration = time.time() - self.session_start
        
        # Calculate session statistics
        stats = self._calculate_session_stats()
        
        # Log session summary
        with open(self.session_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                self.session_id, self.session_start, session_duration / 60,
                self.conversation_count, stats.get('avg_total_time', 0),
                stats.get('cache_hit_rate', 0), stats.get('avg_stt_time', 0),
                stats.get('avg_llm_time', 0)
            ])
        
        return {
            'session_id': self.session_id,
            'duration_minutes': session_duration / 60,
            'conversations': self.conversation_count,
            **stats
        }
    
    def _calculate_session_stats(self) -> Dict[str, Any]:
        """Calculate statistics for the current session."""
        if not self.csv_file.exists():
            return {}
        
        try:
            # Read current session data
            session_data = []
            with open(self.csv_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['session_id'] == self.session_id:
                        session_data.append(row)
            
            if not session_data:
                return {}
            
            # Calculate averages
            total_times = [float(row['total_time_ms']) for row in session_data]
            stt_times = [float(row['stt_time_ms']) for row in session_data]
            llm_times = [float(row['llm_time_ms']) for row in session_data]
            cache_hits = [row['tts_cache_hit'].lower() == 'true' for row in session_data]
            
            return {
                'avg_total_time': sum(total_times) / len(total_times),
                'avg_stt_time': sum(stt_times) / len(stt_times),
                'avg_llm_time': sum(llm_times) / len(llm_times),
                'cache_hit_rate': sum(cache_hits) / len(cache_hits) * 100,
                'fastest_response': min(total_times),
                'slowest_response': max(total_times)
            }
            
        except Exception as e:
            print(f"⚠️ Error calculating session stats: {e}")
            return {}
    
    def generate_report(self, last_n_sessions: int = 5) -> str:
        """Generate a human-readable performance report."""
        if not self.csv_file.exists():
            return "No performance data available."
        
        try:
            # Read recent data
            recent_data = []
            with open(self.csv_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    recent_data.append(row)
            
            if not recent_data:
                return "No performance data available."
            
            # Take last N conversations
            recent_data = recent_data[-20:]  # Last 20 conversations
            
            # Calculate metrics
            total_times = [float(row['total_time_ms']) for row in recent_data]
            stt_times = [float(row['stt_time_ms']) for row in recent_data]
            llm_times = [float(row['llm_time_ms']) for row in recent_data]
            tts_times = [float(row['tts_time_ms']) for row in recent_data]
            cache_hits = [row['tts_cache_hit'].lower() == 'true' for row in recent_data]
            
            # Generate report
            report = []
            report.append("📊 PennyGPT Performance Report")
            report.append("=" * 35)
            report.append(f"Recent Conversations: {len(recent_data)}")
            report.append(f"Avg Response Time: {sum(total_times)/len(total_times):.0f}ms")
            report.append(f"Fastest Response: {min(total_times):.0f}ms")
            report.append(f"Slowest Response: {max(total_times):.0f}ms")
            report.append("")
            report.append("⏱️ Component Breakdown:")
            report.append(f"  STT (Speech-to-Text): {sum(stt_times)/len(stt_times):.0f}ms avg")
            report.append(f"  LLM (AI Processing): {sum(llm_times)/len(llm_times):.0f}ms avg")
            report.append(f"  TTS (Text-to-Speech): {sum(tts_times)/len(tts_times):.0f}ms avg")
            report.append("")
            report.append(f"🎯 TTS Cache Hit Rate: {sum(cache_hits)/len(cache_hits)*100:.1f}%")
            report.append(f"📁 Log File: {self.csv_file}")
            
            return "\n".join(report)
            
        except Exception as e:
            return f"Error generating report: {e}"


# Convenience functions for easy integration
_logger_instance = None

def get_logger() -> PerformanceLogger:
    """Get or create the global performance logger instance."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = PerformanceLogger()
    return _logger_instance

def log_conversation(metrics: ConversationMetrics) -> None:
    """Convenience function to log a conversation."""
    get_logger().log_conversation(metrics)

def end_session() -> Dict[str, Any]:
    """Convenience function to end the current session."""
    return get_logger().end_session()

def generate_report() -> str:
    """Convenience function to generate a performance report."""
    return get_logger().generate_report()


if __name__ == "__main__":
    # Test the performance logger
    print("🧪 Testing Performance Logger...")
    
    logger = PerformanceLogger()
    
    # Simulate some conversation metrics
    test_metrics = ConversationMetrics(
        timestamp=time.time(),
        session_id="test_session",
        vad_time_ms=50.0,
        stt_time_ms=750.0,
        llm_time_ms=1200.0,
        memory_context_length=500,
        tts_time_ms=200.0,
        tts_cache_hit=False,
        user_input_length=25,
        response_length=150,
        wake_word_detected=True,
        total_time_ms=2200.0
    )
    
    logger.log_conversation(test_metrics)
    
    # Test report generation
    print("\n" + logger.generate_report())
    
    # End session
    session_stats = logger.end_session()
    print(f"\n🏁 Session ended: {session_stats}")
