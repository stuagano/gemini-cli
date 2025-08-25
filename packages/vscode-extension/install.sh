#!/bin/bash

# Gemini Documentation Manager VS Code Extension Installer
# This script will build and install the extension

echo "🚀 Installing Gemini Documentation Manager..."

# Check if we're in the correct directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: package.json not found. Please run this script from the extension directory."
    exit 1
fi

# Check if VS Code is installed
if ! command -v code &> /dev/null; then
    echo "❌ Error: VS Code is not installed or 'code' command is not available in PATH"
    echo "Please install VS Code and enable the 'code' command in your shell"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Build the extension
echo "🔨 Building extension..."
npm run build

# Package the extension
echo "📦 Packaging extension..."
npm run package

# Find the generated .vsix file
VSIX_FILE=$(find . -name "*.vsix" -type f | head -1)

if [ -z "$VSIX_FILE" ]; then
    echo "❌ Error: No .vsix file found after packaging"
    exit 1
fi

# Uninstall previous version if it exists
echo "🗑️  Removing previous version..."
code --uninstall-extension gemini-cli.gemini-docs-manager 2>/dev/null || true

# Install the extension
echo "🎯 Installing extension..."
code --install-extension "$VSIX_FILE"

if [ $? -eq 0 ]; then
    echo "✅ Successfully installed Gemini Documentation Manager!"
    echo ""
    echo "📋 Next steps:"
    echo "1. Reload your VS Code window (Cmd+R)"
    echo "2. Look for the 📖 Gemini Manager panel in the Activity Bar"
    echo "3. Configure the extension in VS Code settings if needed"
    echo ""
    echo "🔧 Configuration options:"
    echo "- gemini.documentationPath: Path to your docs folder (default: 'docs')"
    echo "- gemini.epicsPath: Path to your epics/stories folder (default: 'docs/tasks')" 
    echo "- gemini.documentationStructure: 'gcar', 'flat', or 'custom'"
    echo "- gemini.ragServerUrl: RAG server URL (default: 'http://localhost:2000')"
else
    echo "❌ Failed to install extension"
    exit 1
fi