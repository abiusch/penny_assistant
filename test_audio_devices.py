#!/usr/bin/env python3
"""List all audio devices and test which one is working"""

import sounddevice as sd
import numpy as np

print("=" * 70)
print("AUDIO DEVICE DIAGNOSTIC")
print("=" * 70)

print("\n📋 Available Audio Devices:")
print(sd.query_devices())

print("\n" + "=" * 70)
print("CURRENT DEFAULT DEVICES")
print("=" * 70)

try:
    default_input = sd.query_devices(kind='input')
    print(f"\n🎤 Default Input Device:")
    print(f"   ID: {default_input['index']}")
    print(f"   Name: {default_input['name']}")
    print(f"   Channels: {default_input['max_input_channels']}")
except Exception as e:
    print(f"   ❌ Error getting default input: {e}")

try:
    default_output = sd.query_devices(kind='output')
    print(f"\n🔊 Default Output Device:")
    print(f"   ID: {default_output['index']}")
    print(f"   Name: {default_output['name']}")
    print(f"   Channels: {default_output['max_output_channels']}")
except Exception as e:
    print(f"   ❌ Error getting default output: {e}")

print("\n" + "=" * 70)
print("VOICE_ENHANCED_PENNY.PY CONFIGURATION")
print("=" * 70)

print("\nCurrent setting: sd.default.device = [1, 2]")
print("   Input device: 1")
print("   Output device: 2")

try:
    device_1 = sd.query_devices(1)
    print(f"\n   Device 1 info:")
    print(f"   Name: {device_1['name']}")
    print(f"   Input channels: {device_1['max_input_channels']}")
    print(f"   Output channels: {device_1['max_output_channels']}")

    if device_1['max_input_channels'] == 0:
        print("   ❌ WARNING: Device 1 has NO input channels!")
        print("      This device cannot record audio!")
except Exception as e:
    print(f"   ❌ Error with device 1: {e}")

print("\n" + "=" * 70)
print("RECOMMENDATION")
print("=" * 70)

# Find best input device
best_input = None
for i in range(sd.query_hostapis()[0]['device_count']):
    try:
        device = sd.query_devices(i)
        if device['max_input_channels'] > 0:
            if best_input is None or 'macbook' in device['name'].lower() or 'built-in' in device['name'].lower():
                best_input = (i, device)
    except:
        pass

if best_input:
    print(f"\n✅ Recommended input device:")
    print(f"   ID: {best_input[0]}")
    print(f"   Name: {best_input[1]['name']}")
    print(f"   Channels: {best_input[1]['max_input_channels']}")
    print(f"\n   FIX: Change voice_enhanced_penny.py line 54 to:")
    print(f"   sd.default.device = [{best_input[0]}, 2]")
else:
    print("\n⚠️  Could not find suitable input device")
