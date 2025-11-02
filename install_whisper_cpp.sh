#!/bin/bash
# Install Whisper.cpp for maximum speed on M4 Pro

echo "🎤 Installing Whisper.cpp..."
echo "=================================================="

cd /Users/CJ/Desktop/penny_assistant

# Check if already exists
if [ -d "whisper.cpp" ]; then
    echo "⚠️  whisper.cpp directory already exists"
    read -p "Remove and reinstall? (y/n): " reinstall
    if [ "$reinstall" = "y" ]; then
        rm -rf whisper.cpp
    else
        echo "Skipping Whisper.cpp installation"
        exit 0
    fi
fi

echo ""
echo "📥 Step 1: Cloning whisper.cpp repository..."
git clone https://github.com/ggerganov/whisper.cpp
cd whisper.cpp

echo ""
echo "🔨 Step 2: Building with Metal acceleration for M4 Pro..."
make

if [ $? -eq 0 ]; then
    echo "✅ Build successful!"
else
    echo "❌ Build failed. Trying with clean build..."
    make clean
    make
fi

echo ""
echo "📥 Step 3: Downloading large-v3 model (~3GB)..."
echo "This will take 5-10 minutes..."
bash ./models/download-ggml-model.sh large-v3

echo ""
echo "✅ Checking installation..."
if [ -f "main" ] && [ -f "models/ggml-large-v3.bin" ]; then
    echo "✅ Whisper.cpp installed successfully!"
    echo ""
    echo "📊 Model size:"
    ls -lh models/ggml-large-v3.bin
    
    echo ""
    echo "🧪 Testing with sample audio..."
    ./main -m models/ggml-large-v3.bin -f samples/jfk.wav
    
    echo ""
    echo "=================================================="
    echo "✅ Whisper.cpp ready!"
    echo "   Binary: $(pwd)/main"
    echo "   Model: $(pwd)/models/ggml-large-v3.bin"
    echo "=================================================="
else
    echo "❌ Installation incomplete"
    echo "Missing files:"
    [ ! -f "main" ] && echo "  - main binary"
    [ ! -f "models/ggml-large-v3.bin" ] && echo "  - large-v3 model"
fi
