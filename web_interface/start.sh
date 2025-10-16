#!/bin/bash
# Quick start script for Penny Web Interface

echo "======================================"
echo "💜 Penny Web Interface - Quick Start"
echo "======================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3."
    exit 1
fi

echo "✅ Python 3 found"

# Check if Flask is installed
if ! python3 -c "import flask" 2>/dev/null; then
    echo "📦 Installing Flask and Flask-CORS..."
    pip install flask flask-cors
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies"
        exit 1
    fi
fi

echo "✅ Flask installed"
echo ""

# Navigate to web interface directory
cd "$(dirname "$0")"

echo "🚀 Starting Penny Web Interface..."
echo ""
echo "📱 Open your browser to: http://localhost:5001"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
python3 server.py
