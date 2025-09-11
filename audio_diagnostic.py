#!/usr/bin/env python3
"""
Audio Device Diagnostic
Quick check to identify microphone issues
"""

import sounddevice as sd
import numpy as np

def main():
    print("🎤 Audio Device Diagnostic")
    print("=" * 30)
    
    # List all available devices
    print("Available audio devices:")
    try:
        devices = sd.query_devices()
        
        for i, device in enumerate(devices):
            device_type = []
            if device.get('max_inputs', 0) > 0:
                device_type.append('INPUT')
            if device.get('max_outputs', 0) > 0:
                device_type.append('OUTPUT')
            
            print(f"{i}: {device['name']} - {'/'.join(device_type) if device_type else 'UNKNOWN'} - {device.get('default_samplerate', 'Unknown')}Hz")
    
    except Exception as e:
        print(f"Error listing devices: {e}")
        # Fallback - just show basic info
        print("Using fallback device detection...")
        try:
            default_input = sd.query_devices(kind='input')
            print(f"Default input device: {default_input['name']}")
        except Exception as e2:
            print(f"Could not detect input device: {e2}")
    
    try:
        print(f"Current default input device: {sd.default.device}")
        default_input = sd.query_devices(kind='input')
        print(f"System default input: {default_input['name']}")
    except Exception as e:
        print(f"Error getting default devices: {e}")
    
    # Test microphone with different devices
    print("\n🎤 Testing microphone access...")
    
    # Test with system default
    try:
        print("Testing with system default microphone...")
        audio = sd.rec(int(2 * 16000), samplerate=16000, channels=1)
        sd.wait()
        max_level = np.max(np.abs(audio))
        print(f"✅ Captured audio - Max level: {max_level:.3f}")
        
        if max_level < 0.001:
            print("⚠️  Very low audio level - check microphone permissions or volume")
        else:
            print("✅ Audio levels look good!")
            
    except Exception as e:
        print(f"❌ Microphone test failed: {e}")
        print("Try checking System Preferences → Security & Privacy → Privacy → Microphone")
    
    # Suggest best device
    try:
        devices = sd.query_devices()
        input_devices = []
        for i, device in enumerate(devices):
            if device.get('max_inputs', 0) > 0:
                input_devices.append(i)
        
        print(f"\n📋 Available input device indices: {input_devices}")
        
        # Look for MacBook built-in mic
        for i, device in enumerate(devices):
            device_name = device['name'].lower()
            if ('macbook' in device_name or 'built-in' in device_name or 'internal' in device_name):
                if device.get('max_inputs', 0) > 0:
                    print(f"💡 Suggested device: {i} - {device['name']}")
                    break
    except Exception as e:
        print(f"Error suggesting devices: {e}")

if __name__ == "__main__":
    main()
