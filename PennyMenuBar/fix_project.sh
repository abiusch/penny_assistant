#!/bin/bash

echo "🛠️ Creating a proper SwiftUI menu bar project..."
echo ""

cd "$(dirname "$0")"

# Create a simple, working SwiftUI project structure
echo "Creating proper project structure..."

# Remove the broken project files
rm -rf PennyMenuBar.xcodeproj PennyMenuBar.xcworkspace

# Create a minimal, working Xcode project using command line tools
echo "Generating new Xcode project..."

# Use xcodebuild to create a basic project template
xcodegen_template="
name: PennyMenuBar
options:
  bundleIdPrefix: com.penny
targets:
  PennyMenuBar:
    type: application
    platform: macOS
    deploymentTarget: '13.0'
    sources:
      - path: .
        includes:
          - \"*.swift\"
    settings:
      PRODUCT_BUNDLE_IDENTIFIER: com.penny.menubar
      INFOPLIST_FILE: Info.plist
      LSUIElement: true
      MACOSX_DEPLOYMENT_TARGET: '13.0'
      SWIFT_VERSION: '5.0'
      ENABLE_HARDENED_RUNTIME: true
      CODE_SIGN_STYLE: Automatic
schemes:
  PennyMenuBar:
    build:
      targets:
        PennyMenuBar: all
    run:
      config: Debug
"

# For now, let's just use xcodebuild directly with the Swift file
echo "Building directly with xcodebuild..."

# Simple build using xcodebuild
xcodebuild -project /dev/null \
  -scheme PennyMenuBar \
  -configuration Release \
  -derivedDataPath ./build \
  build

echo "❌ Project structure needs manual creation. Let's use direct Swift compilation instead..."

# Alternative: Direct Swift compilation
echo "Compiling Swift directly..."
swiftc PennyMenuBarApp.swift \
  -target x86_64-apple-macos13.0 \
  -o PennyMenuBar \
  -framework SwiftUI \
  -framework Foundation \
  -framework AppKit

if [ -f PennyMenuBar ]; then
    echo "✅ Swift compilation successful!"
    echo "Run with: ./PennyMenuBar"
else
    echo "❌ Swift compilation failed. The project needs a proper Xcode setup."
    echo ""
    echo "Manual solution:"
    echo "1. Open Xcode"
    echo "2. Create New Project > macOS > App"
    echo "3. Name: PennyMenuBar, Interface: SwiftUI"
    echo "4. Copy the PennyMenuBarApp.swift content into the new project"
    echo "5. Set LSUIElement = true in Info.plist"
fi
