#!/bin/bash
# Install Piper TTS - Fast, local TTS for macOS with Metal acceleration
# Works with Python 3.13

set -e

echo "🔊 Installing Piper TTS..."
echo "=================================================="

# Install via pip
echo ""
echo "📥 Installing piper-tts..."
pip3 install piper-tts

# Create models directory
echo ""
echo "📁 Creating models directory..."
mkdir -p piper_models

# Download a fast, high-quality English voice model
echo ""
echo "📥 Downloading voice model (en_US-lessac-medium)..."
echo "This is a high-quality female voice, ~100MB"

cd piper_models

# Download model
curl -L "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx" -o en_US-lessac-medium.onnx

# Download model config
curl -L "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json" -o en_US-lessac-medium.onnx.json

cd ..

# Test installation
echo ""
echo "✅ Testing Piper TTS..."
echo "Hello, I am Penny. This is a test of the Piper text-to-speech system." | piper --model piper_models/en_US-lessac-medium.onnx --output_file test_output.wav

if [ -f test_output.wav ]; then
    echo "✅ Piper TTS installed successfully!"
    echo ""
    echo "Test audio saved to: test_output.wav"
    echo "Model: piper_models/en_US-lessac-medium.onnx"
    rm test_output.wav
else
    echo "❌ Test failed"
    exit 1
fi

echo ""
echo "=================================================="
echo "✅ Installation complete!"
echo ""
echo "Usage:"
echo "  echo 'Hello world' | piper --model piper_models/en_US-lessac-medium.onnx --output_file output.wav"
