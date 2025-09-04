#!/bin/bash

echo "🚀 Building PennyMenuBar SwiftUI App..."
echo ""

cd "$(dirname "$0")"

# Check if Xcode is available
if ! command -v xcodebuild &> /dev/null; then
    echo "❌ Xcode command line tools not found!"
    echo "Install with: xcode-select --install"
    exit 1
fi

echo "📦 Building PennyMenuBar.app..."
xcodebuild -project PennyMenuBar.xcodeproj -scheme PennyMenuBar -configuration Release build

if [ $? -eq 0 ]; then
    echo "✅ Build successful!"
    echo ""
    echo "🎯 Your app is built and ready!"
    echo "📁 Location: build/Release/PennyMenuBar.app"
    echo ""
    echo "🚀 To run:"
    echo "   1. Make sure your FastAPI daemon is running on http://127.0.0.1:8080"
    echo "   2. Double-click the app or run: open build/Release/PennyMenuBar.app"
    echo ""
    echo "⌨️  Menu bar shortcuts:"
    echo "   - ⌘⇧S: Toggle Push-to-Talk"
    echo "   - ⌘⇧T: Test Speech"
    echo "   - ⌘Q: Quit"
else
    echo "❌ Build failed!"
    echo "Check the error messages above for details."
    exit 1
fi
