#!/bin/bash
# Install Coqui TTS for local voice synthesis

echo "🔊 Installing Coqui TTS..."
echo "=================================================="

# Check if already installed
if python3 -c "import TTS" 2>/dev/null; then
    echo "✅ TTS already installed"
    python3 -c "import TTS; print(f'   Version: {TTS.__version__}')"
    echo ""
    read -p "Reinstall anyway? (y/n): " reinstall
    if [ "$reinstall" != "y" ]; then
        echo "Skipping TTS installation"
        exit 0
    fi
fi

echo ""
echo "📥 Installing TTS library..."
/opt/homebrew/bin/pip3 install --break-system-packages TTS

if [ $? -eq 0 ]; then
    echo "✅ TTS installed successfully!"
else
    echo "❌ TTS installation failed"
    exit 1
fi

echo ""
echo "🧪 Testing TTS (this will download ~2GB model on first run)..."
echo "Please be patient, this takes 5-10 minutes the first time..."

cd /Users/CJ/Desktop/penny_assistant

tts --text "Hello, I'm Penny, your AI assistant running fully on your Mac" \
    --model_name tts_models/multilingual/multi-dataset/xtts_v2 \
    --out_path test_penny_voice.wav

if [ -f "test_penny_voice.wav" ]; then
    echo ""
    echo "✅ TTS working!"
    echo "📊 Generated audio:"
    ls -lh test_penny_voice.wav
    
    echo ""
    echo "🔊 Playing sample..."
    afplay test_penny_voice.wav
    
    echo ""
    echo "=================================================="
    echo "✅ Coqui TTS ready!"
    echo "   Model: xtts_v2 (multilingual)"
    echo "   Sample: test_penny_voice.wav"
    echo "=================================================="
else
    echo "❌ TTS test failed"
fi
