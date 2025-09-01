#!/usr/bin/env python3
"""
PennyGPT Health Monitor
Checks system components and provides diagnostics
"""

import asyncio
import requests
import time
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from src.adapters.llm.openai_compat import OpenAICompatLLM
from src.adapters.tts.google_tts_adapter import GoogleTTS
from src.adapters.stt.whisper_adapter import WhisperSTT
from src.core.llm_router import load_config


class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded" 
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ComponentHealth:
    name: str
    status: HealthStatus
    response_time_ms: Optional[float]
    error: Optional[str] = None
    details: Optional[Dict] = None


class PennyGPTHealthMonitor:
    """Monitor health of all PennyGPT components."""
    
    def __init__(self, config_path: str = "penny_config.json"):
        self.config = load_config()  # load_config() doesn't take arguments
        self.components = {}
        
    async def check_lm_studio_health(self) -> ComponentHealth:
        """Check LM Studio connection and model availability."""
        llm_config = self.config.get('llm', {})
        base_url = llm_config.get('base_url', 'http://localhost:1234/v1')
        
        start_time = time.time()
        
        try:
            # Check models endpoint
            response = requests.get(f"{base_url}/models", timeout=2)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                models = response.json().get('data', [])
                model_name = llm_config.get('model', 'unknown')
                
                # Check if configured model is available
                available_models = [m.get('id', '') for m in models]
                model_available = model_name in available_models
                
                if model_available:
                    return ComponentHealth(
                        name="LM Studio",
                        status=HealthStatus.HEALTHY,
                        response_time_ms=response_time,
                        details={
                            "available_models": available_models,
                            "configured_model": model_name,
                            "model_available": True
                        }
                    )
                else:
                    return ComponentHealth(
                        name="LM Studio", 
                        status=HealthStatus.DEGRADED,
                        response_time_ms=response_time,
                        error=f"Configured model '{model_name}' not available",
                        details={
                            "available_models": available_models,
                            "configured_model": model_name,
                            "model_available": False
                        }
                    )
            else:
                return ComponentHealth(
                    name="LM Studio",
                    status=HealthStatus.UNHEALTHY,
                    response_time_ms=response_time,
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                
        except requests.exceptions.ConnectionError:
            return ComponentHealth(
                name="LM Studio",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=None,
                error="Connection refused - LM Studio may not be running"
            )
        except requests.exceptions.Timeout:
            return ComponentHealth(
                name="LM Studio",
                status=HealthStatus.DEGRADED,
                response_time_ms=2000,  # Timeout value
                error="Request timed out - LM Studio may be overloaded"
            )
        except Exception as e:
            return ComponentHealth(
                name="LM Studio",
                status=HealthStatus.UNKNOWN,
                response_time_ms=None,
                error=str(e)
            )
    
    async def check_llm_completion(self) -> ComponentHealth:
        """Test actual LLM completion functionality."""
        start_time = time.time()
        
        try:
            llm = OpenAICompatLLM(self.config)
            response = llm.complete("Say 'OK' if you can hear me", tone="neutral")
            response_time = (time.time() - start_time) * 1000
            
            if response and not response.startswith("[llm error]"):
                return ComponentHealth(
                    name="LLM Completion",
                    status=HealthStatus.HEALTHY,
                    response_time_ms=response_time,
                    details={"response_length": len(response)}
                )
            else:
                return ComponentHealth(
                    name="LLM Completion",
                    status=HealthStatus.UNHEALTHY,
                    response_time_ms=response_time,
                    error=f"Invalid response: {response[:100]}..."
                )
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ComponentHealth(
                name="LLM Completion",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                error=str(e)
            )
    
    async def check_tts_health(self) -> ComponentHealth:
        """Check TTS functionality."""
        start_time = time.time()
        
        try:
            tts = GoogleTTS(self.config)
            success = tts.speak("Health check", allow_barge_in=False)
            response_time = (time.time() - start_time) * 1000
            
            # Stop immediately to avoid actual audio playback during health check
            tts.stop()
            
            if success:
                return ComponentHealth(
                    name="TTS",
                    status=HealthStatus.HEALTHY,
                    response_time_ms=response_time,
                    details={
                        "cache_enabled": tts.cache_enabled,
                        "cache_size": len(tts.memory_cache)
                    }
                )
            else:
                return ComponentHealth(
                    name="TTS",
                    status=HealthStatus.DEGRADED,
                    response_time_ms=response_time,
                    error="TTS synthesis failed"
                )
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ComponentHealth(
                name="TTS",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                error=str(e)
            )
    
    async def check_stt_health(self) -> ComponentHealth:
        """Check STT model loading."""
        start_time = time.time()
        
        try:
            stt = WhisperSTT(self.config)
            response_time = (time.time() - start_time) * 1000
            
            if stt._model is not None:
                return ComponentHealth(
                    name="STT",
                    status=HealthStatus.HEALTHY,
                    response_time_ms=response_time,
                    details={"model_loaded": True, "model_name": stt.model_name}
                )
            else:
                return ComponentHealth(
                    name="STT",
                    status=HealthStatus.UNHEALTHY,
                    response_time_ms=response_time,
                    error="Whisper model failed to load"
                )
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ComponentHealth(
                name="STT",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                error=str(e)
            )
    
    async def check_audio_devices(self) -> ComponentHealth:
        """Check audio device availability."""
        start_time = time.time()
        
        try:
            import sounddevice as sd
            
            # Query audio devices
            devices = sd.query_devices()
            input_devices = [d for d in devices if d['max_input_channels'] > 0]
            output_devices = [d for d in devices if d['max_output_channels'] > 0]
            
            response_time = (time.time() - start_time) * 1000
            
            if input_devices and output_devices:
                default_input = sd.query_devices(kind='input')
                default_output = sd.query_devices(kind='output')
                
                return ComponentHealth(
                    name="Audio Devices",
                    status=HealthStatus.HEALTHY,
                    response_time_ms=response_time,
                    details={
                        "input_devices": len(input_devices),
                        "output_devices": len(output_devices),
                        "default_input": default_input['name'],
                        "default_output": default_output['name']
                    }
                )
            else:
                return ComponentHealth(
                    name="Audio Devices",
                    status=HealthStatus.UNHEALTHY,
                    response_time_ms=response_time,
                    error="No suitable audio devices found"
                )
                
        except ImportError:
            return ComponentHealth(
                name="Audio Devices",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=None,
                error="sounddevice library not available"
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ComponentHealth(
                name="Audio Devices",
                status=HealthStatus.UNKNOWN,
                response_time_ms=response_time,
                error=str(e)
            )
    
    async def check_all_components(self) -> Dict[str, ComponentHealth]:
        """Run health checks on all components."""
        print("🔍 Running PennyGPT health checks...\n")
        
        # Run checks concurrently where possible
        checks = [
            self.check_lm_studio_health(),
            self.check_tts_health(),
            self.check_stt_health(),
            self.check_audio_devices()
        ]
        
        results = await asyncio.gather(*checks, return_exceptions=True)
        
        health_status = {}
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                component_name = ["LM Studio", "TTS", "STT", "Audio Devices"][i]
                health_status[component_name] = ComponentHealth(
                    name=component_name,
                    status=HealthStatus.UNKNOWN,
                    response_time_ms=None,
                    error=str(result)
                )
            else:
                health_status[result.name] = result
        
        # Test LLM completion separately (needs LM Studio to be healthy first)
        if health_status.get("LM Studio", ComponentHealth("LM Studio", HealthStatus.UNHEALTHY, None)).status == HealthStatus.HEALTHY:
            try:
                completion_health = await self.check_llm_completion()
                health_status[completion_health.name] = completion_health
            except Exception as e:
                health_status["LLM Completion"] = ComponentHealth(
                    name="LLM Completion",
                    status=HealthStatus.UNKNOWN,
                    response_time_ms=None,
                    error=str(e)
                )
        
        return health_status
    
    def format_health_report(self, health_status: Dict[str, ComponentHealth]) -> str:
        """Format health status into a readable report."""
        report = []
        report.append("=" * 50)
        report.append("🏥 PennyGPT Health Report")
        report.append("=" * 50)
        
        # Overall status
        healthy_count = sum(1 for h in health_status.values() if h.status == HealthStatus.HEALTHY)
        total_count = len(health_status)
        
        if healthy_count == total_count:
            overall = "🟢 HEALTHY"
        elif healthy_count > total_count // 2:
            overall = "🟡 DEGRADED"
        else:
            overall = "🔴 UNHEALTHY"
        
        report.append(f"\nOverall Status: {overall} ({healthy_count}/{total_count} components healthy)")
        report.append("")
        
        # Component details
        for name, health in health_status.items():
            if health.status == HealthStatus.HEALTHY:
                icon = "✅"
            elif health.status == HealthStatus.DEGRADED:
                icon = "⚠️"
            elif health.status == HealthStatus.UNHEALTHY:
                icon = "❌"
            else:
                icon = "❓"
            
            report.append(f"{icon} {name}")
            report.append(f"   Status: {health.status.value.upper()}")
            
            if health.response_time_ms is not None:
                report.append(f"   Response Time: {health.response_time_ms:.1f}ms")
            
            if health.error:
                report.append(f"   Error: {health.error}")
            
            if health.details:
                for key, value in health.details.items():
                    report.append(f"   {key}: {value}")
            
            report.append("")
        
        # Recommendations
        report.append("💡 Recommendations:")
        
        if "LM Studio" in health_status and health_status["LM Studio"].status != HealthStatus.HEALTHY:
            report.append("   • Start LM Studio and ensure the local server is running on port 1234")
            report.append("   • Verify the correct model is loaded in LM Studio")
        
        if "TTS" in health_status and health_status["TTS"].status != HealthStatus.HEALTHY:
            report.append("   • Check internet connection for Google TTS")
            report.append("   • Verify audio output devices are available")
        
        if "STT" in health_status and health_status["STT"].status != HealthStatus.HEALTHY:
            report.append("   • Install required dependencies: pip install openai-whisper")
            report.append("   • Ensure sufficient disk space for Whisper models")
        
        if "Audio Devices" in health_status and health_status["Audio Devices"].status != HealthStatus.HEALTHY:
            report.append("   • Connect a microphone and speakers")
            report.append("   • Check system audio permissions")
        
        report.append("")
        report.append("=" * 50)
        
        return "\n".join(report)
    
    async def run_health_check(self) -> bool:
        """Run complete health check and display results."""
        health_status = await self.check_all_components()
        report = self.format_health_report(health_status)
        print(report)
        
        # Return True if system is mostly healthy
        healthy_count = sum(1 for h in health_status.values() if h.status == HealthStatus.HEALTHY)
        return healthy_count >= len(health_status) // 2


async def main():
    """Main health check entry point."""
    monitor = PennyGPTHealthMonitor()
    is_healthy = await monitor.run_health_check()
    
    if is_healthy:
        print("🚀 PennyGPT is ready to run!")
        return 0
    else:
        print("⚠️  PennyGPT has issues that should be resolved before running.")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))
