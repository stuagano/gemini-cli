#!/bin/bash

echo "🔨 Building Gemini Documentation Manager VS Code Extension"
echo "=========================================================="

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Compile TypeScript
echo "🔧 Compiling TypeScript..."
npm run compile

# Package extension
echo "📦 Packaging extension..."
npx vsce package

echo ""
echo "✅ Build complete!"
echo ""
echo "The extension has been packaged as a .vsix file"
echo "To install in VS Code:"
echo "1. Open VS Code"
echo "2. Go to Extensions view (Ctrl+Shift+X)"
echo "3. Click the ... menu"
echo "4. Select 'Install from VSIX...'"
echo "5. Choose the generated .vsix file"
echo ""
echo "Or install from command line:"
echo "code --install-extension gemini-docs-manager-*.vsix"