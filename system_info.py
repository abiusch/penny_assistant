#!/usr/bin/env python3
"""
System Information Script for PennyGPT
Collects system info to help with troubleshooting
"""

import sys
import os
import platform
import subprocess
import json
from pathlib import Path

def get_python_info():
    """Get Python version and environment info."""
    return {
        "version": sys.version,
        "version_info": {
            "major": sys.version_info.major,
            "minor": sys.version_info.minor,
            "micro": sys.version_info.micro
        },
        "executable": sys.executable,
        "platform": sys.platform
    }

def get_system_info():
    """Get system platform information."""
    return {
        "system": platform.system(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "platform": platform.platform(),
        "node": platform.node()
    }

def check_lm_studio_process():
    """Check if LM Studio process is running."""
    try:
        if platform.system() == "Darwin":  # macOS
            result = subprocess.run(['pgrep', '-f', 'LM Studio'], 
                                  capture_output=True, text=True)
            return len(result.stdout.strip()) > 0
        elif platform.system() == "Windows":
            result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq LMStudio*'], 
                                  capture_output=True, text=True)
            return 'LMStudio' in result.stdout
        else:  # Linux
            result = subprocess.run(['pgrep', '-f', 'lm.studio'], 
                                  capture_output=True, text=True)
            return len(result.stdout.strip()) > 0
    except Exception:
        return False

def check_port_1234():
    """Check if port 1234 is being used (LM Studio default)."""
    try:
        if platform.system() == "Darwin":  # macOS
            result = subprocess.run(['lsof', '-i', ':1234'], 
                                  capture_output=True, text=True)
            return len(result.stdout.strip()) > 0
        elif platform.system() == "Windows":
            result = subprocess.run(['netstat', '-an'], 
                                  capture_output=True, text=True)
            return ':1234' in result.stdout
        else:  # Linux
            result = subprocess.run(['ss', '-tuln'], 
                                  capture_output=True, text=True)
            return ':1234' in result.stdout
    except Exception:
        return False

def get_audio_info():
    """Get audio device information if sounddevice is available."""
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        return {
            "available": True,
            "device_count": len(devices),
            "input_devices": len([d for d in devices if d['max_input_channels'] > 0]),
            "output_devices": len([d for d in devices if d['max_output_channels'] > 0]),
            "default_input": sd.query_devices(kind='input')['name'],
            "default_output": sd.query_devices(kind='output')['name']
        }
    except ImportError:
        return {"available": False, "error": "sounddevice not installed"}
    except Exception as e:
        return {"available": False, "error": str(e)}

def get_file_info():
    """Get information about key project files."""
    files = {
        "penny_config.json": "Configuration file",
        "requirements.txt": "Dependencies",
        "src/adapters/llm/openai_compat.py": "LLM adapter",
        "src/core/pipeline.py": "Core pipeline",
        "health_monitor.py": "Health monitor"
    }
    
    file_info = {}
    for filepath, description in files.items():
        path = Path(filepath)
        file_info[filepath] = {
            "description": description,
            "exists": path.exists(),
            "size": path.stat().st_size if path.exists() else None,
            "modified": path.stat().st_mtime if path.exists() else None
        }
    
    return file_info

def main():
    """Collect and display system information."""
    print("🖥️  PennyGPT System Information")
    print("=" * 40)
    
    info = {
        "python": get_python_info(),
        "system": get_system_info(),
        "lm_studio_process": check_lm_studio_process(),
        "port_1234_in_use": check_port_1234(),
        "audio": get_audio_info(),
        "files": get_file_info()
    }
    
    # Display formatted information
    print(f"\nPython: {info['python']['version_info']['major']}.{info['python']['version_info']['minor']}.{info['python']['version_info']['micro']}")
    print(f"System: {info['system']['system']} {info['system']['machine']}")
    print(f"Platform: {info['system']['platform']}")
    
    print("\n🔌 Services:")
    print(f"   LM Studio Process: {'✅ Running' if info['lm_studio_process'] else '❌ Not detected'}")
    print(f"   Port 1234: {'✅ In use' if info['port_1234_in_use'] else '❌ Available'}")
    
    print("\n🎵 Audio:")
    if info['audio']['available']:
        print(f"   Devices: ✅ {info['audio']['device_count']} total")
        print(f"   Input: {info['audio']['input_devices']} ({info['audio']['default_input']})")
        print(f"   Output: {info['audio']['output_devices']} ({info['audio']['default_output']})")
    else:
        print(f"   Status: ❌ {info['audio']['error']}")
    
    print("\n📁 Files:")
    for filepath, details in info['files'].items():
        status = "✅" if details['exists'] else "❌"
        print(f"   {status} {filepath} - {details['description']}")
    
    # Save to file for debugging
    with open('system_info.json', 'w') as f:
        json.dump(info, f, indent=2, default=str)
    
    print("\n💾 Full system info saved to: system_info.json")
    print("\n🚀 Next step: Run 'python check_health.py' for detailed component health")

if __name__ == "__main__":
    main()
