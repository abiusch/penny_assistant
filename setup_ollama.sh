#!/bin/bash
# Quick Ollama check and setup for Penny

echo "🔍 Checking Ollama installation..."
echo "=================================================="

# Add Ollama to PATH
export PATH=$PATH:/Applications/Ollama.app/Contents/MacOS:/usr/local/bin

# Check version
echo ""
echo "📦 Ollama version:"
ollama --version

# List current models
echo ""
echo "📚 Current models:"
ollama list

echo ""
echo "=================================================="
echo "🎯 Models needed for Penny:"
echo "   - llama3.1:8b (~5GB) - Fast responses"
echo "   - llama3.1:70b-q4_K_M (~40GB) - Smart responses"
echo "=================================================="

echo ""
read -p "Pull llama3.1:8b? (y/n): " pull_8b
if [ "$pull_8b" = "y" ]; then
    echo "📥 Pulling llama3.1:8b (this will take ~10 min)..."
    ollama pull llama3.1:8b
    echo "✅ llama3.1:8b ready!"
fi

echo ""
read -p "Pull llama3.1:70b-q4_K_M? (y/n): " pull_70b
if [ "$pull_70b" = "y" ]; then
    echo "📥 Pulling llama3.1:70b-q4_K_M (this will take ~60 min)..."
    ollama pull llama3.1:70b-q4_K_M
    echo "✅ llama3.1:70b-q4_K_M ready!"
fi

echo ""
echo "✨ Final model list:"
ollama list

echo ""
echo "🧪 Quick test with 8B model:"
ollama run llama3.1:8b "Say hello in one sentence" --verbose false

echo ""
echo "=================================================="
echo "✅ Ollama setup complete!"
echo "=================================================="
