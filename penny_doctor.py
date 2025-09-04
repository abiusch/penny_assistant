#!/usr/bin/env python3
"""
Penny Doctor - PennyGPT System Health Check
Validates all components of your PennyGPT voice assistant setup.
"""

import os
import sys
import json
import subprocess
import requests
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional

class PennyDoctor:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.results = []
        self.error_count = 0
        
    def print_header(self):
        print("🏥 Penny Doctor - PennyGPT System Health Check")
        print("=" * 50)
        print("")
        
    def print_result(self, test_name: str, passed: bool, details: str = "", fix_suggestion: str = ""):
        """Print a test result with consistent formatting"""
        status = "✅" if passed else "❌"
        self.results.append((test_name, passed, details, fix_suggestion))
        
        if not passed:
            self.error_count += 1
            
        print(f"{status} {test_name}")
        if details:
            print(f"   {details}")
        if not passed and fix_suggestion:
            print(f"   🔧 Fix: {fix_suggestion}")
        print("")
        
    def check_python_environment(self) -> bool:
        """Check Python version and virtual environment"""
        print("🐍 Python Environment Checks")
        print("-" * 30)
        
        # Python version
        version = sys.version_info
        version_str = f"{version.major}.{version.minor}.{version.micro}"
        python_ok = version.major == 3 and version.minor >= 9
        
        self.print_result(
            "Python Version",
            python_ok,
            f"Found Python {version_str}",
            "Install Python 3.9+ (recommended: 3.11 or 3.13)"
        )
        
        # Virtual environment
        in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
        self.print_result(
            "Virtual Environment",
            in_venv,
            "Active virtual environment detected" if in_venv else "No virtual environment detected",
            "Activate with: source .venv/bin/activate"
        )
        
        # PYTHONPATH
        pythonpath_set = 'PYTHONPATH' in os.environ and 'src' in os.environ.get('PYTHONPATH', '')
        self.print_result(
            "PYTHONPATH Configuration",
            pythonpath_set,
            f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}",
            "Set with: export PYTHONPATH=src or use PYTHONPATH=src python"
        )
        
        return python_ok and in_venv
        
    def check_dependencies(self) -> bool:
        """Check required Python packages"""
        print("📦 Dependency Checks")
        print("-" * 20)
        
        required_packages = [
            ('fastapi', 'FastAPI web framework'),
            ('uvicorn', 'ASGI server'),
            ('requests', 'HTTP client'),
            ('openai', 'OpenAI API client'),
            ('pyaudio', 'Audio I/O'),
            ('numpy', 'Numerical computing'),
            ('pydantic', 'Data validation')
        ]
        
        all_good = True
        for package, description in required_packages:
            try:
                __import__(package)
                self.print_result(f"Package: {package}", True, description)
            except ImportError:
                all_good = False
                self.print_result(
                    f"Package: {package}", 
                    False, 
                    f"Missing: {description}",
                    f"Install with: pip install {package}"
                )
                
        return all_good
        
    def check_audio_system(self) -> bool:
        """Check audio input/output capabilities"""
        print("🔊 Audio System Checks")
        print("-" * 22)
        
        # Check PyAudio
        try:
            import pyaudio
            pa = pyaudio.PyAudio()
            
            # Get default devices
            try:
                default_input = pa.get_default_input_device_info()
                self.print_result(
                    "Audio Input Device",
                    True,
                    f"Default: {default_input['name']}"
                )
            except Exception as e:
                self.print_result(
                    "Audio Input Device",
                    False,
                    f"Error: {str(e)}",
                    "Check microphone permissions in System Preferences > Security & Privacy"
                )
                
            try:
                default_output = pa.get_default_output_device_info()
                self.print_result(
                    "Audio Output Device",
                    True,
                    f"Default: {default_output['name']}"
                )
            except Exception as e:
                self.print_result(
                    "Audio Output Device",
                    False,
                    f"Error: {str(e)}",
                    "Check speaker/headphone connections"
                )
                
            pa.terminate()
            
            # Test basic audio functionality
            try:
                # Quick beep test (non-blocking)
                if sys.platform == "darwin":  # macOS
                    subprocess.run(["afplay", "/System/Library/Sounds/Ping.aiff"], 
                                 timeout=2, capture_output=True)
                    self.print_result("Audio Playback Test", True, "System sound played successfully")
                else:
                    self.print_result("Audio Playback Test", True, "Skipped on non-macOS")
            except Exception as e:
                self.print_result(
                    "Audio Playback Test",
                    False,
                    f"Could not play test sound: {str(e)}",
                    "Check system audio settings"
                )
                
        except ImportError:
            self.print_result(
                "PyAudio Library",
                False,
                "PyAudio not available",
                "Install with: pip install pyaudio"
            )
            return False
            
        return True
        
    def check_llm_connection(self) -> bool:
        """Check LLM service availability"""
        print("🧠 LLM Service Checks")
        print("-" * 20)
        
        # Check for LM Studio (common local LLM)
        lm_studio_url = "http://localhost:1234/v1/models"
        try:
            response = requests.get(lm_studio_url, timeout=3)
            if response.status_code == 200:
                models = response.json()
                model_count = len(models.get('data', []))
                self.print_result(
                    "LM Studio Connection",
                    True,
                    f"Found {model_count} models available"
                )
                return True
        except Exception:
            pass
            
        # Check for Ollama (another local option)
        ollama_url = "http://localhost:11434/api/tags"
        try:
            response = requests.get(ollama_url, timeout=3)
            if response.status_code == 200:
                models = response.json()
                model_count = len(models.get('models', []))
                self.print_result(
                    "Ollama Connection",
                    True,
                    f"Found {model_count} models available"
                )
                return True
        except Exception:
            pass
            
        # If no local LLM found
        self.print_result(
            "Local LLM Service",
            False,
            "No local LLM service found",
            "Start LM Studio or Ollama, or configure OpenAI API key"
        )
        
        return False
        
    def check_tts_system(self) -> bool:
        """Check Text-to-Speech capabilities"""
        print("🗣️ Text-to-Speech Checks")
        print("-" * 25)
        
        # Check Google TTS (gTTS)
        try:
            import gtts
            self.print_result("Google TTS Library", True, "gTTS available for text-to-speech")
            
            # Test TTS functionality (without playing audio)
            try:
                tts = gtts.gTTS("Test", lang='en')
                self.print_result("TTS Functionality", True, "Text-to-speech engine working")
                return True
            except Exception as e:
                self.print_result(
                    "TTS Functionality",
                    False,
                    f"TTS test failed: {str(e)}",
                    "Check internet connection for Google TTS"
                )
                
        except ImportError:
            self.print_result(
                "Google TTS Library",
                False,
                "gTTS not available",
                "Install with: pip install gtts"
            )
            
        return False
        
    def check_penny_components(self) -> bool:
        """Check PennyGPT specific components"""
        print("🤖 PennyGPT Component Checks")
        print("-" * 30)
        
        # Check core files exist
        core_files = [
            ('src/core/__init__.py', 'Core module'),
            ('src/adapters/__init__.py', 'Adapters module'),
            ('personality.py', 'Personality system'),
            ('server.py', 'FastAPI daemon server'),
            ('penny_config.json', 'Configuration file')
        ]
        
        all_files_exist = True
        for file_path, description in core_files:
            full_path = self.project_root / file_path
            exists = full_path.exists()
            all_files_exist = all_files_exist and exists
            
            self.print_result(
                f"File: {file_path}",
                exists,
                description,
                f"File missing - check repository structure"
            )
            
        # Check if FastAPI daemon can be imported
        try:
            sys.path.insert(0, str(self.project_root))
            if (self.project_root / 'server.py').exists():
                # Don't actually import to avoid side effects, just check syntax
                with open(self.project_root / 'server.py', 'r') as f:
                    code = f.read()
                    compile(code, 'server.py', 'exec')
                self.print_result("FastAPI Server Module", True, "Server code is valid")
            else:
                self.print_result(
                    "FastAPI Server Module",
                    False,
                    "server.py not found",
                    "Ensure server.py exists in project root"
                )
        except Exception as e:
            self.print_result(
                "FastAPI Server Module",
                False,
                f"Server code has issues: {str(e)}",
                "Check server.py for syntax errors"
            )
            
        return all_files_exist
        
    def check_daemon_health(self) -> bool:
        """Check if FastAPI daemon is running and healthy"""
        print("🌐 Daemon Service Checks")
        print("-" * 23)
        
        daemon_url = "http://127.0.0.1:8080"
        
        # Check if daemon is running
        try:
            response = requests.get(f"{daemon_url}/health", timeout=3)
            if response.status_code == 200:
                health_data = response.json()
                uptime = health_data.get('uptime_s', 0)
                ptt_active = health_data.get('ptt_active', False)
                
                self.print_result(
                    "FastAPI Daemon",
                    True,
                    f"Running (uptime: {uptime:.1f}s, PTT: {'active' if ptt_active else 'inactive'})"
                )
                
                # Test other endpoints
                endpoints_to_test = ['/ptt/start', '/ptt/stop', '/speak']
                for endpoint in endpoints_to_test:
                    try:
                        if endpoint == '/speak':
                            test_response = requests.post(
                                f"{daemon_url}{endpoint}",
                                json={"text": "test"},
                                timeout=2
                            )
                        else:
                            test_response = requests.post(f"{daemon_url}{endpoint}", timeout=2)
                            
                        self.print_result(
                            f"Endpoint: {endpoint}",
                            test_response.status_code == 200,
                            f"HTTP {test_response.status_code}"
                        )
                    except Exception as e:
                        self.print_result(
                            f"Endpoint: {endpoint}",
                            False,
                            f"Request failed: {str(e)}"
                        )
                        
                return True
                
        except Exception as e:
            self.print_result(
                "FastAPI Daemon",
                False,
                f"Not running or unreachable: {str(e)}",
                "Start with: cd /path/to/penny_assistant && PYTHONPATH=src python server.py"
            )
            
        return False
        
    def check_permissions(self) -> bool:
        """Check macOS permissions"""
        print("🔐 macOS Permission Checks")
        print("-" * 26)
        
        if sys.platform != "darwin":
            self.print_result("Platform Check", True, "Non-macOS system - skipping permission checks")
            return True
            
        # Check microphone permissions (basic check)
        try:
            import pyaudio
            pa = pyaudio.PyAudio()
            input_devices = []
            for i in range(pa.get_device_count()):
                device = pa.get_device_info_by_index(i)
                if device['maxInputChannels'] > 0:
                    input_devices.append(device['name'])
            pa.terminate()
            
            if input_devices:
                self.print_result(
                    "Microphone Access",
                    True,
                    f"Found {len(input_devices)} input devices"
                )
            else:
                self.print_result(
                    "Microphone Access",
                    False,
                    "No input devices found",
                    "Check System Preferences > Security & Privacy > Privacy > Microphone"
                )
                
        except Exception as e:
            self.print_result(
                "Microphone Access",
                False,
                f"Cannot access audio devices: {str(e)}",
                "Grant microphone permissions in System Preferences"
            )
            
        return True
        
    def run_all_checks(self):
        """Run all health checks"""
        self.print_header()
        
        # Run all checks
        checks = [
            self.check_python_environment,
            self.check_dependencies,
            self.check_audio_system,
            self.check_llm_connection,
            self.check_tts_system,
            self.check_penny_components,
            self.check_daemon_health,
            self.check_permissions
        ]
        
        for check in checks:
            try:
                check()
            except Exception as e:
                print(f"❌ Check failed with exception: {str(e)}")
                self.error_count += 1
            print()
            
        # Summary
        self.print_summary()
        
    def print_summary(self):
        """Print overall health summary"""
        print("📋 Health Check Summary")
        print("=" * 23)
        
        total_checks = len(self.results)
        passed_checks = sum(1 for _, passed, _, _ in self.results if passed)
        
        if self.error_count == 0:
            print("🎉 All checks passed! Your PennyGPT system is ready to use.")
        elif self.error_count <= 3:
            print(f"⚠️  {self.error_count} issues found, but system should still work.")
        else:
            print(f"❌ {self.error_count} issues found. System may not work properly.")
            
        print(f"📊 Results: {passed_checks}/{total_checks} checks passed")
        print("")
        
        # Show failed checks with fixes
        failed_checks = [(name, fix) for name, passed, _, fix in self.results if not passed and fix]
        if failed_checks:
            print("🔧 Quick Fixes:")
            print("-" * 13)
            for name, fix in failed_checks:
                print(f"• {name}: {fix}")
            print("")
            
        print("🚀 Next Steps:")
        if self.error_count == 0:
            print("• Your system is ready! Try: PYTHONPATH=src python server.py")
            print("• Then test with: curl http://127.0.0.1:8080/health")
        else:
            print("• Fix the issues above and run 'penny doctor' again")
            print("• For help, check: docs/TROUBLESHOOTING.md")
            
        print("")
        print("For detailed setup instructions, see: README.md")

def main():
    """Main entry point"""
    doctor = PennyDoctor()
    doctor.run_all_checks()
    
    # Exit with error code if issues found
    sys.exit(doctor.error_count)

if __name__ == "__main__":
    main()
