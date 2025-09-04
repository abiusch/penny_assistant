#!/bin/bash

echo "🧪 Testing PennyMenuBar Setup..."
echo ""

# Test 1: Check if daemon is running
echo "1. Testing daemon connection..."
if curl -s http://127.0.0.1:8080/health > /dev/null; then
    echo "✅ FastAPI daemon is running"
    curl -s http://127.0.0.1:8080/health | python3 -m json.tool
else
    echo "❌ FastAPI daemon is NOT running"
    echo "   Start with: cd /Users/CJ/Desktop/penny_assistant && PYTHONPATH=src python server.py"
fi

echo ""

# Test 2: Check Xcode availability
echo "2. Testing Xcode setup..."
if command -v xcodebuild &> /dev/null; then
    echo "✅ Xcode command line tools available"
    xcodebuild -version | head -1
else
    echo "❌ Xcode command line tools NOT available"
    echo "   Install with: xcode-select --install"
fi

echo ""

# Test 3: Check project structure
echo "3. Testing project structure..."
cd "$(dirname "$0")"

required_files=(
    "PennyMenuBarApp.swift"
    "Info.plist" 
    "PennyMenuBar.entitlements"
    "README.md"
    "build.sh"
)

all_good=true
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ Missing: $file"
        all_good=false
    fi
done

echo ""

# Test 4: API endpoint testing
echo "4. Testing API endpoints..."
if curl -s http://127.0.0.1:8080/health > /dev/null; then
    echo "Testing /ptt/start..."
    curl -s -X POST http://127.0.0.1:8080/ptt/start | python3 -m json.tool
    
    echo "Testing /speak..."
    curl -s -X POST http://127.0.0.1:8080/speak \
        -H "Content-Type: application/json" \
        -d '{"text":"Menu bar test"}' | python3 -m json.tool
    
    echo "Testing /ptt/stop..."
    curl -s -X POST http://127.0.0.1:8080/ptt/stop | python3 -m json.tool
else
    echo "❌ Cannot test API endpoints - daemon not running"
fi

echo ""

# Summary
if [ "$all_good" = true ]; then
    echo "🎉 Setup looks good! Ready to build and run."
    echo ""
    echo "Next steps:"
    echo "  1. ./build.sh (to build the app)"
    echo "  2. open build/Release/PennyMenuBar.app (to run)"
else
    echo "⚠️  Some issues found. Fix the missing files and try again."
fi
