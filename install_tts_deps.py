#!/usr/bin/env python3
"""
Install TTS dependencies for low-latency speech
"""

import subprocess
import sys

def install_tts_dependencies():
    """Install required TTS libraries"""
    print("Installing TTS Dependencies")
    print("=" * 30)
    
    dependencies = [
        ("gtts", "Google Text-to-Speech"),
        ("pyttsx3", "System Text-to-Speech Engine"),
    ]
    
    for package, description in dependencies:
        print(f"\nInstalling {package} ({description})...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", package
            ])
            print(f"✅ {package} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {package}: {e}")
        except Exception as e:
            print(f"❌ Error installing {package}: {e}")
    
    print(f"\n🎤 TTS setup complete!")
    print("You can now test with: python3 test_tts_latency.py")

if __name__ == "__main__":
    install_tts_dependencies()
